"""
Script para avaliar prompts otimizados e publicar resultados no LangSmith.

Este script:
1. Carrega dataset de avaliação de arquivo .jsonl (datasets/bug_to_user_story.jsonl)
2. Cria/atualiza dataset no LangSmith
3. Puxa prompt otimizado do LangSmith Hub
4. Executa avaliação com 4 métricas via langsmith.evaluate()
5. Publica resultados por exemplo no dashboard do LangSmith
6. Exibe resumo no terminal

Métricas avaliadas (threshold ≥ 0.9):
- Tone Score
- Acceptance Criteria Score
- User Story Format Score
- Completeness Score
"""

import os
import sys
import json
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import check_env_vars, format_score, print_section_header, get_llm as get_configured_llm
from metrics import (
    evaluate_tone_score,
    evaluate_acceptance_criteria_score,
    evaluate_user_story_format_score,
    evaluate_completeness_score,
)

load_dotenv()


def get_llm():
    return get_configured_llm(temperature=0)


def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
        return examples
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {jsonl_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSONL: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> str:
    print(f"Criando dataset de avaliação: {dataset_name}...")

    examples = load_dataset_from_jsonl(jsonl_path)
    if not examples:
        print("❌ Nenhum exemplo carregado do arquivo .jsonl")
        return dataset_name

    print(f"   ✓ Carregados {len(examples)} exemplos do arquivo {jsonl_path}")

    try:
        existing = next(
            (ds for ds in client.list_datasets(dataset_name=dataset_name) if ds.name == dataset_name),
            None
        )

        if existing:
            print(f"   ✓ Dataset '{dataset_name}' já existe, usando existente")
            return dataset_name

        dataset = client.create_dataset(dataset_name=dataset_name)
        for example in examples:
            client.create_example(
                dataset_id=dataset.id,
                inputs=example["inputs"],
                outputs=example["outputs"]
            )
        print(f"   ✓ Dataset criado com {len(examples)} exemplos")
        return dataset_name

    except Exception as e:
        print(f"   ⚠️  Erro ao criar dataset: {e}")
        return dataset_name


def pull_prompt_from_langsmith(prompt_name: str) -> ChatPromptTemplate:
    try:
        print(f"   Puxando prompt do LangSmith Hub: {prompt_name}")
        prompt = hub.pull(prompt_name)
        print(f"   ✓ Prompt carregado com sucesso")
        return prompt
    except Exception as e:
        error_msg = str(e).lower()
        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível carregar o prompt '{prompt_name}'")
        print(f"{'=' * 70}\n")
        if "not found" in error_msg or "404" in error_msg:
            print("⚠️  O prompt não foi encontrado no LangSmith Hub.\n")
            print("AÇÕES NECESSÁRIAS:")
            print("1. Faça push do prompt otimizado:")
            print(f"   python src/push_prompts.py")
            print(f"\n2. Confirme em: https://smith.langchain.com/prompts")
        else:
            print(f"Erro técnico: {e}")
        print(f"\n{'=' * 70}\n")
        raise


def run_evaluation(prompt_name: str, dataset_name: str, experiment_prefix: str) -> Dict[str, float]:
    """
    Executa avaliação usando langsmith.evaluate(), que publica automaticamente
    os scores por exemplo no dashboard do LangSmith.
    """
    print(f"\n🔍 Avaliando: {prompt_name}")

    prompt_template = pull_prompt_from_langsmith(prompt_name)
    llm = get_llm()

    # Target: executa o prompt em cada exemplo do dataset
    def target(inputs: dict) -> dict:
        chain = prompt_template | llm
        response = chain.invoke(inputs)
        return {"output": response.content}

    # Evaluators: recebem (run, example) e retornam score para o LangSmith
    def tone_evaluator(run, example):
        bug_report = example.inputs.get("bug_report", "")
        user_story = run.outputs.get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        result = evaluate_tone_score(bug_report, user_story, reference)
        return {"key": "tone_score", "score": result["score"], "comment": result.get("reasoning", "")}

    def acceptance_criteria_evaluator(run, example):
        bug_report = example.inputs.get("bug_report", "")
        user_story = run.outputs.get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        result = evaluate_acceptance_criteria_score(bug_report, user_story, reference)
        return {"key": "acceptance_criteria_score", "score": result["score"], "comment": result.get("reasoning", "")}

    def user_story_format_evaluator(run, example):
        bug_report = example.inputs.get("bug_report", "")
        user_story = run.outputs.get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        result = evaluate_user_story_format_score(bug_report, user_story, reference)
        return {"key": "user_story_format_score", "score": result["score"], "comment": result.get("reasoning", "")}

    def completeness_evaluator(run, example):
        bug_report = example.inputs.get("bug_report", "")
        user_story = run.outputs.get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        result = evaluate_completeness_score(bug_report, user_story, reference)
        return {"key": "completeness_score", "score": result["score"], "comment": result.get("reasoning", "")}

    results = evaluate(
        target,
        data=dataset_name,
        evaluators=[
            tone_evaluator,
            acceptance_criteria_evaluator,
            user_story_format_evaluator,
            completeness_evaluator,
        ],
        experiment_prefix=experiment_prefix,
        max_concurrency=1,
    )

    # Agrega scores médios a partir dos resultados
    scores = {
        "tone_score": [],
        "acceptance_criteria_score": [],
        "user_story_format_score": [],
        "completeness_score": [],
    }

    for result in results:
        for eval_result in result.get("evaluation_results", {}).get("results", []):
            key = eval_result.key
            if key in scores and eval_result.score is not None:
                scores[key].append(eval_result.score)

    return {
        key: round(sum(vals) / len(vals), 4) if vals else 0.0
        for key, vals in scores.items()
    }


def display_results(prompt_name: str, scores: Dict[str, float]) -> bool:
    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)

    metric_labels = {
        "tone_score": "Tone Score",
        "acceptance_criteria_score": "Acceptance Criteria Score",
        "user_story_format_score": "User Story Format Score",
        "completeness_score": "Completeness Score",
    }

    all_passed = True
    for key, label in metric_labels.items():
        score = scores.get(key, 0.0)
        passed = score >= 0.9
        if not passed:
            all_passed = False
        print(f"  - {label}: {format_score(score, threshold=0.9)}")

    average_score = sum(scores.values()) / len(scores) if scores else 0.0

    print("\n" + "-" * 50)
    print(f"📊 MÉDIA GERAL: {average_score:.4f}")
    print("-" * 50)

    if all_passed:
        print(f"\n✅ STATUS: APROVADO (todas métricas >= 0.9)")
    else:
        print(f"\n❌ STATUS: REPROVADO (alguma métrica < 0.9)")
        for key, label in metric_labels.items():
            score = scores.get(key, 0.0)
            if score < 0.9:
                print(f"   ⚠️  {label}: {score:.4f} (necessário: 0.9000)")

    return all_passed


def main():
    print_section_header("AVALIAÇÃO DE PROMPTS OTIMIZADOS")

    provider = os.getenv("LLM_PROVIDER", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    eval_model = os.getenv("EVAL_MODEL", "gpt-4o")

    print(f"Provider: {provider}")
    print(f"Modelo Principal: {llm_model}")
    print(f"Modelo de Avaliação: {eval_model}\n")

    required_vars = ["LANGSMITH_API_KEY", "LLM_PROVIDER"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif provider in ["google", "gemini"]:
        required_vars.append("GOOGLE_API_KEY")

    if not check_env_vars(required_vars):
        return 1

    client = Client()
    project_name = os.getenv("LANGCHAIN_PROJECT", "prompt-optimization-challenge-resolved")

    jsonl_path = "datasets/bug_to_user_story.jsonl"
    if not Path(jsonl_path).exists():
        print(f"❌ Arquivo de dataset não encontrado: {jsonl_path}")
        return 1

    dataset_name = f"{project_name}-eval"
    create_evaluation_dataset(client, dataset_name, jsonl_path)

    print("\n" + "=" * 70)
    print("PROMPTS PARA AVALIAR")
    print("=" * 70)
    print("\nCertifique-se de ter feito push dos prompts antes de avaliar:")
    print("  python src/push_prompts.py\n")

    prompts_to_evaluate = ["bug_to_user_story_v2"]

    all_passed = True
    evaluated_count = 0
    results_summary = []

    for prompt_name in prompts_to_evaluate:
        evaluated_count += 1
        experiment_prefix = f"{prompt_name}-eval3"

        try:
            scores = run_evaluation(prompt_name, dataset_name, experiment_prefix)
            passed = display_results(prompt_name, scores)
            all_passed = all_passed and passed
            results_summary.append({"prompt": prompt_name, "scores": scores, "passed": passed})

        except Exception as e:
            print(f"\n❌ Falha ao avaliar '{prompt_name}': {e}")
            all_passed = False
            results_summary.append({
                "prompt": prompt_name,
                "scores": {k: 0.0 for k in ["tone_score", "acceptance_criteria_score", "user_story_format_score", "completeness_score"]},
                "passed": False
            })

    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50 + "\n")

    if evaluated_count == 0:
        print("⚠️  Nenhum prompt foi avaliado")
        return 1

    print(f"Prompts avaliados: {evaluated_count}")
    print(f"Aprovados: {sum(1 for r in results_summary if r['passed'])}")
    print(f"Reprovados: {sum(1 for r in results_summary if not r['passed'])}\n")

    if all_passed:
        print("✅ Todos os prompts atingiram score >= 0.9 em todas as métricas!")
        print(f"\n✓ Confira os resultados em:")
        print(f"  https://smith.langchain.com/projects/{project_name}")
        print("\nPróximos passos:")
        print("1. Documente o processo no README.md")
        print("2. Capture screenshots das avaliações")
        print("3. Faça commit e push para o GitHub")
        return 0
    else:
        print("⚠️  Alguns prompts não atingiram score >= 0.9 em todas as métricas")
        print("\nPróximos passos:")
        print("1. Refatore os prompts com score baixo")
        print("2. Faça push novamente: python src/push_prompts.py")
        print("3. Execute: python src/evaluate.py novamente")
        return 1


if __name__ == "__main__":
    sys.exit(main())
