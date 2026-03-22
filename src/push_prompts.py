"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    print_section_header(f"Pushing Prompt '{prompt_name}' to LangSmith Hub")
    check_env_vars(["LANGCHAIN_HUB_API_KEY"])
    try:
        # Obter o prompt em prompts/bug_to_user_story_v2.yml
        messages = [(msg["role"], msg["content"]) for msg in prompt_data["messages"]]
        prompt_template = ChatPromptTemplate.from_messages(messages)
        # Push para o Hub (PÚBLICO)
        hub.push(
            prompt_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description", ""),
            tags=prompt_data.get("tags", []),
        )
        print(f"Prompt '{prompt_name}' pushed successfully!")
        return True
    except Exception as e:
        print(f"Error pushing prompt: {e}")
        return False    
    


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []
    if "messages" not in prompt_data:
        errors.append("Missing 'messages' key.")
    elif not isinstance(prompt_data["messages"], list):
        errors.append("'messages' should be a list.")
    else:
        for i, message in enumerate(prompt_data["messages"]):
            if "role" not in message or "content" not in message:
                errors.append(f"Message {i} is missing 'role' or 'content'.")
            elif message["role"] not in ["system", "user", "assistant"]:
                errors.append(f"Message {i} has invalid role '{message['role']}'.")
    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    if validate_prompt_data := validate_prompt(load_yaml("prompts/bug_to_user_story_v2.yml")):
        print("Prompt data is valid. Proceeding to push...")
        if push_prompt_to_langsmith("arquitetomovel/bug_to_user_story_v2", load_yaml("prompts/bug_to_user_story_v2.yml")):
            print("Prompt pushed successfully!")
        else:
            print("Failed to push prompt.")


if __name__ == "__main__":
    sys.exit(main())
