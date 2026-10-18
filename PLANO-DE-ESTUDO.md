# Plano de Estudo e Execução — Pull, Otimização e Avaliação de Prompts

> Documento de trabalho pessoal. Consolida o diagnóstico do repositório, as decisões
> técnicas tomadas (com as evidências que as sustentam) e o roteiro de execução.
>
> **Perfil:** dev sênior C# aprendendo Python + LangChain. Método: entender antes de
> escrever, escrever tudo à mão.
>
> **Decisões travadas:** stack LangChain 0.3.x (caminho B) · provider OpenAI.

---

## 1. Diagnóstico do repositório

### Inventário

| Arquivo | Status | O que é |
|---|---|---|
| `src/utils.py` | pronto | YAML load/save, validação de estrutura, **factory de LLM** (`get_llm`, `get_eval_llm`) |
| `src/metrics.py` | pronto | 7 avaliadores *LLM-as-Judge* — **só 3 são usados** |
| `src/evaluate.py` | pronto | Orquestra: cria dataset no LangSmith → puxa prompt do Hub → roda nos 15 exemplos → calcula métricas |
| `datasets/bug_to_user_story.jsonl` | pronto | 15 pares `bug_report` → `reference` (ground truth) |
| `prompts/bug_to_user_story_v1.yml` | pronto | O prompt **ruim de propósito** |
| `src/pull_prompts.py` | corpo `...` | **implementar** |
| `src/push_prompts.py` | corpo `...` | **implementar** |
| `tests/test_prompts.py` | corpo `pass` | **implementar** (6 testes) |
| `prompts/bug_to_user_story_v2.yml` | não existe | **criar — é aqui que está 80% da nota** |

### O fluxo real (a pegadinha que derruba todo mundo)

O `evaluate.py` **não lê o YAML local**. Ele faz `hub.pull("{username}/bug_to_user_story_v2")`.
O LangSmith Hub é a fonte única de verdade:

```
v2.yml (você edita)  ──push──►  LangSmith Hub  ──pull──►  evaluate.py  ──►  notas
```

**Editar o YAML e rodar `evaluate.py` sem `push` avalia a versão anterior.**
Regra de ouro do ciclo de iteração: *nunca avalie sem ter feito push antes.*

Analogia C#: o YAML é o código-fonte, o `push` é o deploy, o `evaluate` roda contra o
que está publicado — não contra o working directory.

### Como a nota é realmente calculada

O enunciado fala em 5 métricas, mas `src/evaluate.py:216-228` mede apenas **3**.
As outras duas são derivadas por aritmética:

```python
helpfulness = (clarity + precision) / 2
correctness = (f1_score + precision) / 2
```

Consequências estratégicas:

1. **`precision` entra em 3 das 5 métricas.** É o gargalo matemático. Otimizar
   `precision` move `helpfulness` e `correctness` de graça.
2. O avaliador de `precision` (`src/metrics.py:246`) pune explicitamente
   *"informações não solicitadas"*, *"divagação"* e *"resposta que não responde
   exatamente o que foi perguntado"*, sempre **comparando com a `reference`**.
3. Portanto: um prompt que gera User Story longa, floreada e "mais completa que o
   esperado" **derruba a nota**. O v2 precisa imitar o **formato e o tamanho** das
   `reference` do dataset — não superá-las.
4. As 4 métricas específicas de `metrics.py` (`tone`, `acceptance_criteria`,
   `user_story_format`, `completeness`) **nunca são chamadas**. Não investir tempo nelas.

Critério de aprovação: **todas** as 5 >= 0.8 (não só a média) — `evaluate.py:262-263`.

---

## 2. Investigação de versões (por que o repo não instala)

### Situação

| Pacote | No repo | Atual (set/2026) |
|---|---|---|
| `langchain` | 0.3.13 | 1.4.2 |
| `langchain-core` | 0.3.28 | 1.6.3 |
| `langsmith` | 0.2.7 | 0.13.0 |
| `langchain-openai` | 0.2.14 | 1.6.2 |
| `langchain-google-genai` | 2.0.8 | 4.4.0 |
| `pydantic` | 2.10.4 | 2.13.5 |

### O bloqueio real: UMA linha, e não é o LangChain

Ambiente local: **Python 3.14.4** (única versão instalada na máquina).
Tentativa de instalar os pinos literais do repo:

```
error: the configured Python interpreter version (3.14) is newer than
       PyO3's maximum supported version (3.13)
💥 maturin failed
ERROR: Failed building wheel for pydantic-core
```

**Causa.** `pydantic` tem núcleo nativo (`pydantic-core`) escrito em Rust. O PyPI
distribui binários pré-compilados (*wheels*) por versão de interpretador. Wheels
disponíveis para `pydantic-core==2.27.2` (fixada por dentro do `pydantic 2.10.4`):

```
cp38 cp39 cp310 cp311 cp312 cp313      ← não existe cp314
```

Sem wheel, o `pip` cai para o *source dist* e tenta compilar Rust localmente. Falha
porque o PyO3 daquela época não conhecia o Python 3.14.

> Analogia C#: é um NuGet com binário nativo e *runtime identifiers*. No Python o RID
> inclui a **versão do interpretador** (`cp314`), porque a ABI do CPython muda a cada
> minor. `pydantic 2.10.4` simplesmente não publicou o RID da sua máquina.

Esse é o **único** pino do arquivo que carrega código nativo incompatível.

### Verificação empírica do caminho escolhido

Stack 0.3 completo instalado com **apenas o pino do `pydantic` relaxado**:

```
python: 3.14.4
langchain: 0.3.13 | core: 0.3.28 | langsmith: 0.2.7 | pydantic: 2.13.5
hub OK -> ['pull', 'push', 'dumps', 'loads', ...]
providers + ChatPromptTemplate OK
render: [SystemMessage(content='sou teste'), HumanMessage(content='teste')]
```

`langchain-community==0.3.13` também instala sem erro. **Tudo o que o desafio pede
roda no Python 3.14.**

### A API legada tem tudo o que o desafio exige

Assinatura real (obtida por introspecção, não por documentação):

```python
hub.pull(owner_repo_commit, *, include_model=None, api_url=None, api_key=None)

hub.push(repo_full_name, object, *,
         new_repo_is_public: bool = False,        # requisito "deixá-lo público"
         new_repo_description: str | None = None, # requisito "descrição"
         tags: Sequence[str] | None = None,       # requisito "tags"
         readme: str | None = None,
         parent_commit_hash: str | None = None)   # versionamento entre iterações
```

A API moderna (`langsmith.Client.push_prompt`) tem os mesmos parâmetros com nomes
diferentes (`is_public`, `description`). **Nada de conceito se perde ficando no 0.3.**

Equivalência para referência futura:

| LangChain 0.3 | LangChain 1.x |
|---|---|
| `from langchain import hub` | `from langsmith import Client` |
| `hub.pull(name)` | `client.pull_prompt(name)` |
| `hub.push(name, obj, new_repo_is_public=True)` | `client.push_prompt(name, object=obj, is_public=True)` |
| `new_repo_description=` / `tags=` | `description=` / `tags=` |

### Decisão: caminho B

| | Caminho | Custo | Resultado |
|---|---|---|---|
| A | Pinos 100% literais | instalar Python 3.12/3.13 (`uv python install 3.12`) | fidelidade absoluta |
| **B** | **Pacotes originais, só `pydantic` relaxado** | **1 linha** | **roda no 3.14, `evaluate.py` intocado** ✅ |
| C | Migrar para LangChain 1.4 | trocar imports no `evaluate.py` (arquivo "não alterar") | desvia do enunciado |

**Razão de engenharia (não de conveniência):** `evaluate.py` e `metrics.py` são o
*harness de avaliação* — a régua que dá a nota. Alterar a régua e depois usá-la para
provar aprovação é o pior lugar possível para introduzir uma variável. O caminho B não
toca em nenhum arquivo marcado como "não alterar", e concentra o esforço no que vale
nota: o `v2.yml`.

**Bônus opcional, depois da entrega:** branch `feat/langchain-1x` com o `evaluate.py`
portado para a API moderna + seção no README comparando as duas. Demonstrar que se
entendeu a migração vale mais no portfólio do que só usar a versão nova.

### Risco residual conhecido

Ao importar o provider do Google aparece:

```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package as soon as possible.
```

`langchain-google-genai==2.0.8` depende do SDK morto `google-generativeai 0.8.6`.
**Irrelevante para este projeto** — decidido usar OpenAI. `langchain-openai==0.2.14`
declara o SDK `openai` em faixa aberta, então veio `openai 1.109.1` (recente).

Transitivas instaladas e verificadas: `openai 1.109.1` · `pydantic 2.13.5` ·
`httpx 0.28.1` · `orjson 3.12.0` · `tenacity 9.1.4`.

---

## 3. Ambiente (executar)

### `requirements.txt` final

```
# LangChain Core
langchain==0.3.13
langchain-core==0.3.28
langchain-community==0.3.13

# LangSmith for prompt management and evaluation
langsmith==0.2.7

# LLM Providers
langchain-openai==0.2.14
langchain-google-genai==2.0.8

# Utilities
python-dotenv==1.0.1
pyyaml==6.0.2
# pydantic==2.10.4 -> sem wheel para cp314 (pydantic-core em Rust exige build local).
# Faixa compatível com langchain-core 0.3.x, que pede >=2.5.2,<3.0.0.
pydantic>=2.12,<3

# Testing
pytest==8.3.4
```

### Comandos

```bash
python3 -m venv venv
source venv/bin/activate          # sem isto, o pip suja o Python do sistema
pip install -r requirements.txt
```

`venv` = pasta com interpretador e `site-packages` isolados. Não existe GAC nem cache
global resolvido por projeto. O `(venv)` no prompt é a confirmação de estar no
ambiente certo.

### Ferramenta de defesa contra tutorial desatualizado

Introspecção é a Reflection do Python. Sempre que uma API do LangChain parecer
estranha, rodar isto em vez de procurar no Google:

```python
import inspect
from langchain import hub
print([n for n in dir(hub) if not n.startswith('_')])
print(inspect.signature(hub.push))
```

### `.env` (OpenAI)

Copiar de `.env.example` e preencher:

```
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=            # smith.langchain.com -> Settings -> API Keys
LANGSMITH_PROJECT=            # nome livre; vira o projeto de tracing
USERNAME_LANGSMITH_HUB=       # handle do Hub (ícone 🔒 ao abrir um prompt publicado)

OPENAI_API_KEY=

LLM_PROVIDER=openai
LLM_MODEL=                    # modelo gerador  — verificar catálogo vigente
EVAL_MODEL=                   # modelo juiz     — pode ser mais capaz que o gerador
```

`LLM_PROVIDER=openai` é obrigatório: `utils.py:190` faz `os.getenv('LLM_PROVIDER')`
e o `.env.example` vem com `google` ativo.

**Modelos:** `gpt-4o-mini` / `gpt-4o` do `.env.example` são de 2024. O enunciado
manda explicitamente consultar o catálogo vigente em
<https://platform.openai.com/docs/models>. Dois cuidados ao escolher:
`utils.py:203-207` passa `temperature=0` — alguns modelos de raciocínio rejeitam esse
parâmetro; e o juiz precisa obedecer "responda APENAS JSON" (`metrics.py`), senão
`extract_json_from_response` devolve `score: 0.0` silenciosamente.

### Orçamento de chamadas (planejar antes de rodar)

Uma execução de `evaluate.py` = **15 gerações + 45 chamadas de juiz = ~60 requests**
(3 juízes × 15 exemplos). Com 3-5 iterações esperadas: **~300 requests**.
Estimativa do enunciado: US$ 1-5.

---

## 4. Roteiro de aulas

Marcador **[LS]** = assistir as aulas de LangSmith do curso antes de executar.

| # | Aula | Entrega | Pré-requisito |
|---|---|---|---|
| 1 | Ambiente + investigação de dependências | `requirements.txt`, venv, `.env` | — (feito) |
| 2 | Python para quem vem de C# | — | — |
| 3 | `pull_prompts.py` — SDK do LangSmith, `ChatPromptTemplate`, serialização | script funcionando | **[LS]** |
| 4 | Prompt engineering do `v2` — Role + Few-shot + CoT calibrados pelas métricas | `v2.yml` | — |
| 5 | `push_prompts.py` — push público, tags, metadados, `parent_commit_hash` | script funcionando | **[LS]** |
| 6 | Avaliação e iteração — ler o tracing para descobrir *por que* a nota caiu | todas as métricas >= 0.8 | **[LS]** |
| 7 | `pytest` para quem vem de xUnit | 6 testes passando | — |
| 8 | README final + evidências | entregável completo | — |

### Aula 2 — Python para dev C# (mapa mental)

| Conceito | C# | Python |
|---|---|---|
| Pacotes | `.csproj` + NuGet, resolução transitiva determinística | `requirements.txt`, sem lockfile; `==` é o mais perto de reprodutível |
| Isolamento | runtime + cache global | `venv` por projeto |
| Namespace | `namespace` desacoplado da pasta | módulo **é** o arquivo; pacote **é** a pasta |
| Resolução de import | referência de assembly | busca em `sys.path` (lista ordenada, mutável em runtime) |
| Tipagem | estática, verificada | *duck typing*; type hints não são checadas em runtime |
| DTO | POCO / record | `dict` na maior parte do LangChain |
| Pipeline | fluent builder / middleware | operador `\|` (LCEL): `prompt \| llm` |

Dois detalhes que explicam o código do repo:

- **`python src/evaluate.py` funciona** com `from utils import ...` porque o Python
  coloca a pasta do script (`src/`) no início do `sys.path`. Rodar
  `python -m src.evaluate` da raiz **quebraria** esses imports. Daí o
  `sys.path.insert(0, ...)` em `tests/test_prompts.py:10` — o pytest roda da raiz e
  precisa alcançar `src/`.
- **`prompt | llm`** (`evaluate.py:152`) é sobrecarga de operador (`__or__`), o LCEL.
  Equivale a um pipeline fluente onde cada elo expõe `invoke`/`stream`/`batch`.

### Aula 4 — regras de calibração do `v2` (derivadas da seção 1)

O `v1` (`prompts/bug_to_user_story_v1.yml`) tem defeitos intencionais, todos
declarados no cabeçalho do arquivo:

- `{bug_report}` duplicado no `system_prompt` **e** no `user_prompt`
- nenhuma persona definida
- nenhum exemplo (zero-shot)
- instruções vagas, nenhuma regra de formato, nenhum edge case

Exigências do enunciado para o `v2`: **Few-shot obrigatório** + ao menos uma técnica
adicional (CoT, Tree of Thought, Skeleton of Thought, ReAct, Role Prompting), persona,
regras explícitas de comportamento, tratamento de edge cases, separação correta
System vs User.

Restrições impostas pelo harness (não pelo enunciado) — decisivas para a nota:

1. Formato e extensão da saída devem **espelhar as `reference`** do dataset:
   `Como um... eu quero... para que...` + `Critérios de Aceitação:` em bullets
   `Dado/Quando/Então/E`. Nada além disso.
2. Se aplicar CoT, o raciocínio **não pode aparecer na saída final** — texto extra é
   contado como divagação e penalizado por `precision`.
3. Few-shot é o instrumento mais eficaz aqui: os exemplos ensinam o formato
   *e* o tamanho ao mesmo tempo.
4. Não usar bugs do `datasets/*.jsonl` como exemplos few-shot — seria contaminação do
   conjunto de avaliação (e o enunciado proíbe alterar o dataset).
5. `test_minimum_techniques` lê o campo `techniques_applied` do YAML → o arquivo
   precisa desse campo com **>= 2** itens (`utils.py:143-145`).

### Aula 6 — protocolo de iteração

```
editar v2.yml  →  push_prompts.py  →  evaluate.py  →  ler tracing  →  repetir
```

Ao reprovar, abrir o tracing no LangSmith e ler o campo `reasoning` do juiz que deu a
nota baixa — ele diz literalmente o que faltou ou sobrou. Diagnóstico por métrica:

| Métrica baixa | Leitura provável | Ação |
|---|---|---|
| `precision` | saída com conteúdo além da `reference` (preâmbulo, raciocínio, seções extras) | enxugar; proibir texto fora do formato |
| `f1_score` | recall baixo: faltam critérios de aceitação esperados | garantir 4-5 critérios `Dado/Quando/Então` |
| `clarity` | estrutura inconsistente entre exemplos | fixar o template rigidamente |

Registrar as notas de cada iteração numa tabela — a jornada é parte do entregável.

---

## 5. Checklist de entregáveis

- [ ] `venv` criado, `requirements.txt` ajustado, `pip install` sem erro
- [ ] `.env` preenchido (LangSmith + OpenAI + modelos verificados no catálogo)
- [ ] `src/pull_prompts.py` implementado; `leonanluppi/bug_to_user_story_v1` salvo em `prompts/bug_to_user_story_v1.yml`
- [ ] `prompts/bug_to_user_story_v2.yml` criado, com `techniques_applied` (>= 2)
- [ ] `src/push_prompts.py` implementado; prompt publicado **como público** no Hub
- [ ] `src/evaluate.py` executado; **todas** as 5 métricas >= 0.8
- [ ] `tests/test_prompts.py` — 6 testes passando (`pytest tests/test_prompts.py`)
- [ ] README: seção **Técnicas Aplicadas (Fase 2)** — quais, por quê, exemplos práticos
- [ ] README: seção **Resultados Finais** — link público do LangSmith, screenshots >= 0.8, tabela v1 vs v2
- [ ] README: seção **Como Executar** — pré-requisitos, dependências, comandos por fase
- [ ] README: seção **Desvios** — o pino do `pydantic` e o motivo (wheel cp314)
- [ ] LangSmith público: dataset com 15 exemplos, execuções do v2, tracing de >= 3 exemplos
- [ ] Fork público no GitHub com tudo commitado

## 6. Ordem de execução

```bash
source venv/bin/activate
python src/pull_prompts.py      # fase 1 — trazer o prompt ruim
# editar prompts/bug_to_user_story_v2.yml  (fase 2 — à mão)
python src/push_prompts.py      # fase 3 — publicar
python src/evaluate.py          # fase 4 — avaliar  (repetir 3-5x)
pytest tests/test_prompts.py    # fase 5 — validar
```
