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

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


@pytest.fixture(scope="module")
def prompt():
    """Carrega o prompt v2 uma única vez para todos os testes."""
    return load_prompts(str(PROMPT_FILE))[PROMPT_KEY]

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' não existe"
        assert prompt["system_prompt"].strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt["system_prompt"]
        assert "Você é um" in system_prompt, "Prompt não define uma persona com 'Você é um...'"
        assert "Product Manager" in system_prompt, "Persona não é de Product Manager"

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt["system_prompt"]
        assert "User Story" in system_prompt, "Prompt não menciona User Story"
        assert "Como um [persona], eu quero" in system_prompt, "Falta o template padrão da User Story"
        assert "Critérios de Aceitação" in system_prompt, "Falta a seção de critérios de aceitação"
        assert "Gherkin" in system_prompt, "Prompt não exige critérios em Gherkin"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt["system_prompt"]
        entradas = system_prompt.count("Entrada:")
        saidas = system_prompt.count("Saída:")
        assert entradas >= 2, f"Few-shot exige pelo menos 2 exemplos, encontrados: {entradas}"
        assert entradas == saidas, f"Exemplos incompletos: {entradas} entradas e {saidas} saídas"

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        conteudo = PROMPT_FILE.read_text(encoding="utf-8")
        assert "TODO" not in conteudo, "O arquivo do prompt ainda contém TODO"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt):
        """Usa o validador do projeto (utils.validate_prompt_structure)."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura inválida: {errors}"

    def test_only_bug_report_variable(self, prompt):
        """Garante que {bug_report} é a única variável e que aparece só no user prompt."""
        from langchain_core.prompts import ChatPromptTemplate
        template = ChatPromptTemplate.from_messages([
            ("system", prompt["system_prompt"]),
            ("human", prompt["user_prompt"]),
        ])
        assert template.input_variables == ["bug_report"], (
            f"Variáveis inesperadas no template: {template.input_variables}"
        )
        assert "{bug_report}" not in prompt["system_prompt"], (
            "{bug_report} duplicado no system prompt (defeito do v1)"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])