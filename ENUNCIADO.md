# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

> Enunciado oficial do desafio — MBA em Engenharia de IA (Full Cycle).

## Objetivo

Você deve entregar um software capaz de:

1. Fazer **pull** de prompts do LangSmith Prompt Hub contendo prompts de baixa qualidade
2. **Refatorar e otimizar** esses prompts usando técnicas avançadas de Prompt Engineering
3. Fazer **push** dos prompts otimizados de volta ao LangSmith
4. **Avaliar** a qualidade através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
5. Atingir pontuação mínima de **0.8 (80%) em todas as métricas** de avaliação

---

## Exemplo no CLI

### Prompt RUIM (v1) — apenas ilustrativo, ponto de partida

```
==================================================
Prompt: {seu_username}/bug_to_user_story_v1
==================================================

Métricas Derivadas:
  - Helpfulness: 0.45 ✗
  - Correctness: 0.52 ✗

Métricas Base:
  - F1-Score: 0.48 ✗
  - Clarity: 0.50 ✗
  - Precision: 0.46 ✗

❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.8: helpfulness, correctness, f1_score, clarity, precision
```

### Prompt OTIMIZADO (v2) — seu objetivo é chegar aqui

```bash
# Após refatorar os prompts e fazer push
python src/push_prompts.py

# Executar avaliação
python src/evaluate.py
```

```
Executando avaliação dos prompts...
==================================================
Prompt: {seu_username}/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.96 ✓

Métricas Base:
  - F1-Score: 0.93 ✓
  - Clarity: 0.95 ✓
  - Precision: 0.92 ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.8

Resultados no LangSmith (notas gravadas como feedback no experimento):
  {seu_username}/bug_to_user_story_v2
    https://smith.langchain.com/o/.../datasets/.../compare?selectedSessions=...
```

---

## Tecnologias obrigatórias

| Item | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Framework | LangChain |
| Plataforma de avaliação | LangSmith |
| Gestão de prompts | LangSmith Prompt Hub |
| Formato de prompts | YAML |

### Pacotes recomendados

```python
from langsmith import Client                               # Pull/push de prompts, datasets e avaliação
from langchain_core.prompts import ChatPromptTemplate      # Montagem dos prompts
from langchain_openai import ChatOpenAI                    # LLM OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI  # LLM Gemini
```

### OpenAI

- Crie uma API Key: https://platform.openai.com/api-keys
- Você vai precisar de um modelo de LLM para **responder** e de um modelo de LLM para **avaliação**. Consulte a documentação oficial da OpenAI para ver os modelos disponíveis.
- Custo estimado: **~$1-5** para completar o desafio.

### Gemini (modelo free)

- Crie uma API Key: https://aistudio.google.com/app/apikey
- Você vai precisar de um modelo de LLM para responder e de um modelo de LLM para avaliação. Consulte a documentação oficial do Google.
- Os limites de requisições gratuitas mudam com frequência — consulte os limites atuais na documentação oficial.

### Escolha dos modelos

O desafio **não fixa modelos**. Nomes e versões mudam com frequência e alguns são descontinuados; faz parte do desafio consultar a documentação oficial do provedor, ver quais modelos estão disponíveis e selecionar os que atendem ao objetivo. Você pode usar o mesmo modelo para responder e avaliar, ou um modelo mais capaz na avaliação.

---

## Handle do LangSmith Hub (seu username)

O LangSmith identifica os prompts publicados por um handle público, no formato `handle/nome_do_prompt`. Esse handle é o valor de `USERNAME_LANGSMITH_HUB` no `.env`.

Ele **não existe por padrão**: é criado quando você torna um prompt público pela primeira vez. Faça esta etapa **antes** de tentar o push:

1. Abra o LangSmith e vá em **Prompts**
2. Crie um prompt qualquer (pode ser de teste) ou abra um existente
3. Clique nos três pontinhos no canto superior direito, ao lado do botão **Playground**
4. Escolha **Make Public**
5. Na tela **Choose your public handle**, defina o seu handle

> ⚠️ O handle é **definitivo** depois de confirmado — escolha com calma. Ele aparece no endereço do prompt (`handle/nome_do_prompt`) e é esse valor que vai no `.env`.

---

## Requisitos

### 1. Pull do prompt inicial do LangSmith

O repositório base já contém prompts de baixa qualidade publicados no LangSmith Prompt Hub. A primeira tarefa é criar o código capaz de fazer o pull desses prompts para o ambiente local.

**Tarefas:**

- [ ] Criar seu handle do LangSmith Hub (ver seção acima)
- [ ] Configurar credenciais do LangSmith no `.env` (conforme `.env.example`)
- [ ] Implementar `src/pull_prompts.py` (esqueleto já existe) que:
  - Conecta ao LangSmith usando suas credenciais
  - Faz pull do prompt `leonanluppi/bug_to_user_story_v1`
  - Salva o prompt localmente em `prompts/bug_to_user_story_v1.yml`

> **Atenção:** o LangSmith bloqueia por padrão o pull de prompts identificados por `owner/nome`, porque um prompt do Hub é um objeto LangChain serializado e pode vir de terceiros. Para o prompt semente do desafio, passe `dangerously_pull_public_prompt=True` no `client.pull_prompt(...)`.

### 2. Otimização do prompt

Refatorar o prompt usando as técnicas aprendidas no curso.

**Tarefas:**

- [ ] Analisar o prompt em `prompts/bug_to_user_story_v1.yml`
- [ ] Criar `prompts/bug_to_user_story_v2.yml` com a versão otimizada
- [ ] Aplicar **obrigatoriamente Few-shot Learning** (exemplos claros de entrada/saída) e **pelo menos uma** das técnicas adicionais:
  - **Chain of Thought (CoT):** instruir o modelo a "pensar passo a passo"
  - **Tree of Thought:** explorar múltiplos caminhos de raciocínio
  - **Skeleton of Thought:** estruturar a resposta em etapas claras
  - **ReAct:** Raciocínio + Ação para tarefas complexas
  - **Role Prompting:** definir persona e contexto detalhado
- [ ] Documentar no `README.md` quais técnicas foram escolhidas e por quê

**Requisitos do prompt otimizado:**

- [ ] Instruções claras e específicas
- [ ] Regras explícitas de comportamento
- [ ] Exemplos de entrada/saída (Few-shot) — **obrigatório**
- [ ] Tratamento de edge cases
- [ ] Uso adequado de **System vs User Prompt**

### 3. Push e avaliação

Enviar os prompts refatorados de volta ao LangSmith Prompt Hub.

**Tarefas:**

- [ ] Implementar `src/push_prompts.py` (esqueleto já existe) que:
  - Lê o prompt otimizado de `prompts/bug_to_user_story_v2.yml`
  - Faz push para o LangSmith com nome versionado: `{seu_username}/bug_to_user_story_v2`
  - Adiciona metadados (tags, descrição, técnicas utilizadas)
- [ ] Executar o script e verificar no dashboard do LangSmith se o prompt foi publicado
- [ ] Deixá-lo **público** (`is_public=True` no push, ou pelo menu "Make Public" na interface)

> Lembre-se: `{seu_username}` é o handle do Hub, que só existe depois de você ter tornado algum prompt público pelo menos uma vez.

### 4. Iteração

Espera-se **3-5 iterações**.

1. Analisar métricas baixas e identificar problemas
2. Editar o prompt, fazer push e avaliar novamente
3. Repetir até **TODAS** as métricas >= 0.8

Cada execução de `src/evaluate.py` cria um **experimento** no LangSmith, ligado ao dataset de avaliação. As 5 notas são gravadas como feedback em cada exemplo, permitindo comparar iterações lado a lado no dashboard. Ao final, o script imprime o link direto do experimento.

**Critério de aprovação:**

```
- Helpfulness >= 0.8
- Correctness >= 0.8
- F1-Score    >= 0.8
- Clarity     >= 0.8
- Precision   >= 0.8

MÉDIA das 5 métricas >= 0.8
```

> ⚠️ **IMPORTANTE:** TODAS as 5 métricas devem estar >= 0.8, não apenas a média!

### 5. Testes de validação

Editar `tests/test_prompts.py` e implementar, no mínimo, os 6 testes abaixo com `pytest`:

| Teste | O que verifica |
|---|---|
| `test_prompt_has_system_prompt` | O campo existe e não está vazio |
| `test_prompt_has_role_definition` | O prompt define uma persona (ex.: "Você é um Product Manager") |
| `test_prompt_mentions_format` | O prompt exige formato Markdown ou User Story padrão |
| `test_prompt_has_few_shot_examples` | O prompt contém exemplos de entrada/saída (Few-shot) |
| `test_prompt_no_todos` | Não há nenhum `[TODO]` esquecido no texto |
| `test_minimum_techniques` | Pelos metadados do YAML, pelo menos 2 técnicas foram listadas |

**Como validar:**

```bash
pytest tests/test_prompts.py
```

---

## Estrutura obrigatória do projeto

Fork do repositório base: https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Sua documentação do processo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (já incluso)
│   └── bug_to_user_story_v2.yml  # Seu prompt otimizado (criar)
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs (já incluso)
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith (implementar)
│   ├── push_prompts.py       # Push ao LangSmith (implementar)
│   ├── evaluate.py           # Avaliação automática (pronto)
│   ├── metrics.py            # 5 métricas implementadas (pronto)
│   └── utils.py              # Funções auxiliares (pronto)
│
├── tests/
│   └── test_prompts.py       # Testes de validação (implementar)
```

### O que você deve implementar

- [ ] `prompts/bug_to_user_story_v2.yml` — criar do zero com o prompt otimizado
- [ ] `src/pull_prompts.py` — implementar o corpo das funções
- [ ] `src/push_prompts.py` — implementar o corpo das funções
- [ ] `tests/test_prompts.py` — implementar os 6 testes de validação
- [ ] `README.md` — documentar o processo de otimização

### O que já vem pronto (NÃO alterar)

- `src/evaluate.py` — script de avaliação completo (cria o experimento no LangSmith e grava as notas como feedback)
- `src/metrics.py` — 5 métricas implementadas
- `src/utils.py` — funções auxiliares
- `datasets/bug_to_user_story.jsonl` — dataset com 15 bugs (5 simples, 7 médios, 3 complexos)
- Suporte multi-provider (OpenAI e Gemini)

---

## VirtualEnv para Python

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ordem de execução

```bash
# 1. Pull dos prompts ruins
python src/pull_prompts.py

# 2. Refatorar prompts
#    Editar manualmente prompts/bug_to_user_story_v2.yml

# 3. Push dos prompts otimizados
python src/push_prompts.py

# 4. Avaliação
python src/evaluate.py
```

---

## Entregável

### 1. Repositório público no GitHub (fork do repositório base) contendo

- [ ] Todo o código-fonte implementado
- [ ] `prompts/bug_to_user_story_v2.yml` 100% preenchido e funcional
- [ ] `README.md` atualizado

### 2. O README.md deve conter

**A) Seção "Técnicas Aplicadas (Fase 2)"**

- [ ] Quais técnicas avançadas foram escolhidas
- [ ] Justificativa de cada técnica
- [ ] Exemplos práticos de como cada técnica foi aplicada

**B) Seção "Resultados Finais"**

- [ ] Link público do dataset de avaliação, com os experimentos (ver "Evidências no LangSmith")
- [ ] Screenshots das avaliações com as notas mínimas de 0.8 atingidas
- [ ] Comparação entre v1 e v2: o que mudou e por quê

**C) Seção "Como Executar"**

- [ ] Instruções claras e detalhadas
- [ ] Pré-requisitos e dependências
- [ ] Comandos para cada fase do projeto

### 3. Evidências no LangSmith

Link público do dataset de avaliação (ou screenshots do dashboard). Devem estar visíveis:

- [ ] Dataset de avaliação com 15 exemplos
- [ ] Execuções do prompt v2 com notas ≥ 0.8
- [ ] Tracing detalhado de pelo menos 3 exemplos

O link impresso pelo `src/evaluate.py` só abre para quem tem acesso ao seu workspace. Para gerar um endereço público, compartilhe o dataset de avaliação — ele expõe junto os experimentos rodados contra ele:

```python
from langsmith import Client

print(Client().share_dataset(dataset_name="<seu LANGSMITH_PROJECT>-eval")["url"])
```

> Rode **uma vez** e guarde o endereço: ao compartilhar de novo, o link muda.

---

## Dicas finais

- Lembre-se da importância da **especificidade, contexto e persona** ao refatorar prompts
- Use **Few-shot Learning com 2-3 exemplos** claros para melhorar drasticamente a performance
- **Chain of Thought (CoT)** é excelente para tarefas que exigem raciocínio complexo (como análise de bugs)
- Use o **Tracing do LangSmith** como principal ferramenta de debug — ele mostra exatamente o que o LLM está "pensando"
- **Não altere os datasets de avaliação** — apenas o prompt em `prompts/bug_to_user_story_v2.yml`
- **Itere, itere, itere** — é normal precisar de 3-5 iterações para atingir 0.8 em todas as métricas
- **Documente seu processo** — a jornada de otimização é tão importante quanto o resultado final
