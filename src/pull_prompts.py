"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

PROMPT_HUB_NAME = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"


def pull_prompts_from_langsmith():
    print(f"Puxando prompt: {PROMPT_HUB_NAME}")
    try:
        client = Client()
        prompt = client.pull_prompt(PROMPT_HUB_NAME, dangerously_pull_public_prompt=True)
    except Exception as e:
        print(f"❌ Erro ao fazer pull: {e}")
        return False

    system_prompt = ""
    user_prompt = ""
    for message in prompt.messages:
        if isinstance(message, SystemMessagePromptTemplate):
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate):
            user_prompt = message.prompt.template

    data = {
        PROMPT_KEY: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "created_at": date.today().isoformat(),
            "source": PROMPT_HUB_NAME,
            "commit_hash": prompt.metadata.get("lc_hub_commit_hash"),
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    if not save_yaml(data, str(OUTPUT_PATH)):
        return False

    print(f"✓ Prompt salvo em {OUTPUT_PATH}")
    return True


def main():
    """Função principal"""
    print_section_header("Pull de Prompts do LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())
