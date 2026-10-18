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
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])

    techniques = prompt_data.get("techniques_applied", [])
    readme = "Técnicas aplicadas:\n" + "\n".join(f"- {t}" for t in techniques)
    print(f"Fazendo push de: {prompt_name}")
    try:
        url = hub.push(
            prompt_name,
            prompt,
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description", ""),
            readme=readme,
            tags=prompt_data.get("tags", []),
        )
    except Exception as e:
        print(f"❌ Erro ao fazer push: {e}")
        return False

    print(f"✓ Push concluído: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    user_prompt = prompt_data.get("user_prompt", "")
    if "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("Push de Prompts para o LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data or PROMPT_KEY not in data:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_FILE}")
        return 1

    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_KEY}"
    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
