"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain import hub

from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()


def pull_prompts_from_langsmith():
    """Faz pull dos prompts do LangSmith Prompt Hub e salva localmente."""
    print_section_header("Pulling Prompts from LangSmith Prompt Hub")
    check_env_vars(["LANGCHAIN_HUB_API_KEY"])
    print("Connecting to LangSmith Prompt Hub...")
    prompts = hub.pull("leonanluppi/bug_to_user_story_v1")
    output_path = Path("prompts/bug_to_user_story_v1.yml")
    save_yaml(prompts, output_path)
    print(f"Prompts saved to {output_path}")
    ...


def main():
    """Função principal"""
    pull_prompts_from_langsmith()
    return 0
    ...


if __name__ == "__main__":
    sys.exit(main())
