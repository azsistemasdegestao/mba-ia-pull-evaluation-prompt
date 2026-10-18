# Histórico de Iterações: `bug_to_user_story_v2`

Registro de cada avaliação do prompt otimizado: métricas, diagnóstico a partir dos
comentários do juiz (LLM-as-Judge) e a hipótese que orientou a iteração seguinte.

**Configuração das avaliações**

| Item | Valor |
|---|---|
| Provider | OpenAI |
| Modelo gerador (`LLM_MODEL`) | `gpt-4o-mini` |
| Modelo avaliador (`EVAL_MODEL`) | `gpt-4o` |
| Dataset | `mba-bug-to-user-story-eval` (15 exemplos: 5 simples, 7 médios, 3 complexos) |
| Critério de aprovação | todas as 5 métricas ≥ 0.8 |

**Lembrete sobre as métricas:** apenas F1-Score, Clarity e Precision são julgadas pelo
LLM avaliador. As outras duas são derivadas:

- Helpfulness = (Clarity + Precision) / 2
- Correctness = (F1-Score + Precision) / 2

Por isso, Precision pesa nas duas métricas derivadas, e F1 baixo derruba Correctness.

---

## Evolução

| Iteração | Mudança principal | F1 | Clarity | Precision | Helpfulness | Correctness | Média | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | v2 inicial (Role + Few-shot + CoT + Skeleton) | 0.76 | 0.88 | 0.81 | 0.85 | 0.79 | 0.8174 | ❌ |
| 2 | Reparo de 8 trechos corrompidos (restaura o passo 5) | 0.76 | 0.87 | 0.83 | 0.85 | 0.80* | 0.8227 | ❌ |

\* 0.7962 exato, arredondado para 0.80 na saída do terminal, mas abaixo do limite.

---

## Iteração 1: linha de base

**Data:** 2026-10-18
**Experimento:** `alexandre-silva-bug_to_user_story_v2-9be93ac8`
**Link:** https://smith.langchain.com/o/830b566d-4887-40ca-8544-046d339e768a/datasets/b866f1cb-44b0-46a9-8170-1d131d830df6/compare?selectedSessions=e6bf2d41-c6c2-488f-99c9-d1ff2beee922

### O que foi avaliado

Primeira versão do v2, construída a partir do diagnóstico do v1:

- **Role Prompting:** persona de Product Manager sênior especialista em Gherkin
- **Chain of Thought:** análise interna em 5 passos (persona, comportamento esperado,
  valor, fatos concretos, complexidade), com instrução explícita de **não** exibir o raciocínio
- **Skeleton of Thought:** três modelos de resposta (simples, médio e complexo), copiados
  da estrutura do gabarito
- **Few-shot:** três exemplos próprios (um por complexidade), sem reaproveitar casos do dataset
- **Regras explícitas** (sem introdução, não inventar, não omitir, Gherkin, proporcionalidade)
  e **casos especiais**
- `{bug_report}` apenas no user prompt (corrige a duplicação do v1)

### Resultado

| Métrica | Nota | Status |
|---|---|---|
| F1-Score | 0.76 | ❌ |
| Clarity | 0.88 | ✅ |
| Precision | 0.81 | ✅ |
| Helpfulness | 0.85 | ✅ |
| Correctness | 0.79 | ❌ |
| **Média** | **0.8174** | ❌ (F1 e Correctness abaixo de 0.8) |

Notas por exemplo:

| # | F1 | Clarity | Precision |
|---|---|---|---|
| 1 | 0.75 | 0.90 | 0.90 |
| 2 | 0.75 | 0.90 | 0.90 |
| 3 | 0.75 | 0.90 | 0.90 |
| 4 | 0.62 | 0.85 | 0.67 |
| 5 | 0.58 | 0.90 | 0.67 |
| 6 | 0.85 | 0.90 | 0.90 |
| 7 | 0.85 | 0.90 | 0.67 |
| 8 | 0.75 | 0.90 | 0.90 |
| 9 | 0.65 | 0.85 | 0.67 |
| 10 | 0.75 | 0.80 | 0.67 |
| 11 | 0.80 | 0.90 | 0.90 |
| 12 | 0.69 | 0.80 | 0.80 |
| 13 | 1.00 | 0.95 | 1.00 |
| 14 | 0.90 | 0.90 | 0.90 |
| 15 | 0.80 | 0.90 | 0.67 |

> A numeração segue a ordem de execução do experimento, que não é necessariamente
> a ordem das linhas do arquivo `.jsonl`.

### Diagnóstico

**1. O F1 caiu por recall, não por erro.** Nos exemplos de nota baixa, o juiz quase
nunca apontou informação errada. A crítica recorrente foi **omissão** de critérios que o
gabarito traz:

| Bug | O que o juiz disse que faltou |
|---|---|
| Webhook de pagamento | e-mail de confirmação, log de auditoria |
| Modal atrás do menu | foco do teclado, fechar com ESC, backdrop clicável |
| Contagem de usuários ativos | atualização em tempo real, filtro por status "ativo" |
| Endpoint sem validação de permissão | acesso aos próprios dados, lado do admin, log de auditoria |
| Desconto no pipeline de vendas | exemplo de cálculo com o valor correto |
| Checkout sem estoque | validação em tempo real, reserva de estoque |

**Causa provável:** a regra 3 ("não invente fatos") combinada com a regra 6 ("seja
proporcional") deixou o modelo conservador demais. Ele passou a não incluir os
**comportamentos esperados** que um PM experiente acrescentaria, e são justamente esses
que o gabarito contém. A regra precisa proibir inventar **dados** (números, nomes,
causas), não **boas práticas** do tipo de problema.

**2. Erro de classificação de complexidade (hipótese do teste de fumaça confirmada).**
O bug de segurança do endpoint `/api/users/:id`, que é **médio**, foi respondido no
formato **complexo** (`=== USER STORY PRINCIPAL ===` e tasks), com 1.372 caracteres contra
849 da referência. No formato errado, o modelo também perdeu os "Critérios Adicionais para
Admins" e a lista de dados expostos. Outros bugs médios saíram até 2x maiores que a
referência (1.483 contra 704 e 1.392 contra 768).

A definição de COMPLEXO incluía "vários componentes afetados", o que é vago: um bug
grave de um único problema "parecia" complexo para o modelo.

**3. Um caso pontual de imprecisão.** No relatório de vendas lento, o modelo escreveu
"gerar em menos de 2 minutos", repetindo o sintoma do relato como se fosse a meta. O
juiz classificou como erro factual.

### ⚠️ Descoberta posterior: o prompt avaliado estava corrompido

Ao preparar a iteração 2, a leitura linha a linha do `v2.yml` revelou **8 trechos
corrompidos** desde o commit `41f890f` (provável falha de copiar e colar): frases cortadas
no meio e, o mais grave, **o passo 5 da análise ausente**. Era justamente o passo que
define SIMPLES, MÉDIO e COMPLEXO. Outros cortes atingiram o template da frase da story
(`eu quero [açãonefício]`), a descrição do modelo MÉDIO e as regras 4 e 5.

**Impacto na leitura dos resultados:** o prompt mandava "escolher o modelo de acordo com a
complexidade", mas nunca dizia como classificá-la. Isso explica melhor o erro de formato do
bug de segurança do que a hipótese original, e pode ter contribuído para as omissões.

**Por que passou despercebido:** a validação feita antes do push era **estrutural** (YAML
válido, seções presentes, apenas `{bug_report}` como variável, sem TODO). Todos os títulos
estavam lá, então tudo passou. Validação estrutural não detecta texto corrompido. Para
conteúdo em linguagem natural, a revisão precisa incluir a leitura do texto.

### Hipótese para a iteração 2 (revisada)

Para isolar o efeito de cada mudança, a iteração 2 **apenas repara as 8 corrupções**,
restaurando o v2 como ele foi projetado. Se F1 e Correctness continuarem abaixo de 0.8, as
três mudanças abaixo ficam para a iteração 3.

### Mudanças planejadas para a iteração 3

Subir o recall sem perder precisão, com três mudanças:

1. **Critério de complexidade:** COMPLEXO somente quando o relato descreve 2 ou mais
   problemas distintos. Um único problema, mesmo grave ou de segurança, é MÉDIO.
2. **Novo passo 6 na análise:** completar os critérios com os comportamentos esperados
   para cada tipo de bug (segurança, interface, pagamento, cálculo, dados, validação).
3. **Regra 3 recalibrada:** proibir inventar **dados**, permitindo explicitamente
   comportamentos esperados e boas práticas.

**Expectativa:** F1 sobe com o recall. Precision sobe ou se mantém, porque o juiz baixava
o "foco" justamente por falta de critérios. **Risco:** respostas mais longas podem baixar
a Clarity (critério de concisão).

---

## Iteração 2: reparo do texto corrompido

**Data:** 2026-10-18
**Experimento:** `alexandre-silva-bug_to_user_story_v2-a52c09dc`
**Link:** https://smith.langchain.com/o/830b566d-4887-40ca-8544-046d339e768a/datasets/b866f1cb-44b0-46a9-8170-1d131d830df6/compare?selectedSessions=474fdac0-77b7-44a5-8c4a-dfe437a49dd1
**Commit:** `8a1074f`

### O que mudou

Apenas o reparo das 8 corrupções, sem nenhuma outra alteração, para isolar o efeito.

### Resultado

| Métrica | Iter. 1 | Iter. 2 | Variação |
|---|---|---|---|
| F1-Score | 0.7623 | 0.7623 | = |
| Clarity | 0.88 | 0.8733 | ≈ |
| Precision | 0.81 | 0.83 | ↑ |
| Helpfulness | 0.85 | 0.85 | = |
| Correctness | 0.79 | 0.7962 | ↑ (ainda < 0.8) |
| Bugs não complexos no formato COMPLEXO | 4 de 15 | 5 de 15 | ↑ |

### Diagnóstico

**A hipótese "a corrupção causou o F1 baixo" foi descartada.** Com o texto íntegro, o F1
ficou idêntico. O experimento confirmou que as causas são as identificadas na iteração 1:

1. **Recall:** os comentários do juiz repetem quase literalmente as omissões da iteração 1
   (foco do teclado e ESC no modal, e-mail e log no webhook, acesso próprio e auditoria no
   endpoint de usuários, cálculo detalhado no desconto).
2. **Formato:** mesmo com o passo 5 restaurado, 5 bugs médios receberam seções `===` do
   modelo COMPLEXO. A expressão "vários componentes afetados" continua vaga.
3. **Sinal novo, de alucinação induzida pelo esqueleto:** no bug do modal, o modelo
   preencheu `Severidade: MÉDIA`, embora o relato não mencione severidade. O campo existia
   no esqueleto, e o modelo o preencheu por inventar o dado.

### Mudanças para a iteração 3

1. **Critério de complexidade:** COMPLEXO somente com 2 ou mais problemas distintos; um único
   problema, mesmo grave, é MÉDIO. Mais a trava: "Nunca use títulos com === fora do modelo
   COMPLEXO".
2. **Passo 6 na análise:** critérios esperados por tipo de bug (segurança, interface,
   pagamento, cálculo, dados, validação).
3. **Regra 3 recalibrada:** proíbe inventar **dados** (incluindo severidade ausente no relato)
   e permite explicitamente comportamentos esperados e boas práticas.
