"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

V2_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        data = load_prompts(str(V2_PROMPT_PATH))
        assert data is not None, "O arquivo YAML deve ser carregado sem erros"
        assert "system_prompt" in data, "O campo 'system_prompt' deve existir no YAML"
        assert data["system_prompt"] is not None, "system_prompt não deve ser None"
        assert len(data["system_prompt"].strip()) > 0, "system_prompt não deve estar vazio"

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        data = load_prompts(str(V2_PROMPT_PATH))
        system_prompt = data.get("system_prompt", "")
        assert "Você é um" in system_prompt, (
            "system_prompt deve definir uma persona com 'Você é um ...'"
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        data = load_prompts(str(V2_PROMPT_PATH))
        system_prompt = data.get("system_prompt", "")
        mentions_format = (
            "Markdown" in system_prompt
            or "User Story" in system_prompt
            or "Como um" in system_prompt
        )
        assert mentions_format, (
            "system_prompt deve mencionar 'Markdown', 'User Story' ou o formato 'Como um'"
        )

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        data = load_prompts(str(V2_PROMPT_PATH))
        system_prompt = data.get("system_prompt", "")
        example_count = system_prompt.count("Exemplo")
        assert example_count >= 2, (
            f"system_prompt deve conter pelo menos 2 exemplos few-shot "
            f"(encontrado: {example_count})"
        )

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        raw_content = V2_PROMPT_PATH.read_text(encoding="utf-8")
        assert "[TODO]" not in raw_content, (
            "O arquivo YAML não deve conter marcadores [TODO]"
        )

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        data = load_prompts(str(V2_PROMPT_PATH))
        techniques = data.get("metadata", {}).get("techniques", [])
        assert isinstance(techniques, list), "metadata.techniques deve ser uma lista"
        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas em metadata.techniques, "
            f"encontradas: {len(techniques)}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
