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
| 3 | Critério de complexidade + passo 6 + regra 3 recalibrada | 0.78 | 0.87 | 0.82 | 0.85 | 0.80* | 0.8221 | ❌ |
| 4 | Few-shot alinhado às instruções (2 exemplos médios novos) | **0.80** | **0.88** | **0.86** | **0.87** | **0.83** | **0.8508** | ✅ |

\* Arredondado na saída do terminal. Valores exatos: 0.7962 (iteração 2) e 0.7984 (iteração 3), ambos abaixo do limite.

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

---

## Iteração 3: complexidade, passo 6 e regra 3

**Data:** 2026-10-18
**Experimento:** `alexandre-silva-bug_to_user_story_v2-6c9ec5d8`
**Link:** https://smith.langchain.com/o/830b566d-4887-40ca-8544-046d339e768a/datasets/b866f1cb-44b0-46a9-8170-1d131d830df6/compare?selectedSessions=e975f3cb-dd97-44a5-825f-5589b25bb2ec
**Commit:** `ce3c596`

### Resultado

| Métrica | Iter. 2 | Iter. 3 | Variação |
|---|---|---|---|
| F1-Score | 0.7623 | 0.7762 | ↑ |
| Clarity | 0.8733 | 0.87 | ≈ |
| Precision | 0.83 | 0.8207 | ≈ |
| Helpfulness | 0.85 | 0.8453 | ≈ |
| Correctness | 0.7962 | 0.7984 | ↑ (ainda < 0.8) |

### Diagnóstico

**1. O modelo ignorou o passo 6 e seguiu os exemplos.** As instruções pediam acessibilidade
em bugs de interface, e-mail e log em webhooks e "Exemplo de Cálculo:" em bugs de valores.
Nenhum desses itens apareceu nas respostas. Os exemplos few-shot, porém, nunca demonstravam
essas seções: o exemplo médio só tinha "Critérios de Aceitação" e "Contexto Técnico".
**Quando instrução e exemplo divergem, o modelo (especialmente um modelo pequeno como o
`gpt-4o-mini`) segue o exemplo.**

**2. O erro de formato tem um padrão.** Três bugs médios ainda saíram no formato COMPLEXO
(webhook, endpoint de usuários e app Android). Os três trazem **listas no relato** (passos de
reprodução, exemplo, observações). O modelo interpreta "lista" como "vários problemas", e a
nova regra pode ter reforçado isso ao citar "lista numerada" como exemplo de complexidade.

**3. Sintoma convertido em meta.** No relatório lento, o critério gerado foi "menos de 2
minutos", repetindo o valor do problema. O gabarito exige uma meta melhor que o atual.

**4. Ruído do juiz.** No webhook, um avaliador apontou falta de "e-mail de confirmação"
(F1) enquanto, em outra execução, o avaliador de Precision chamou o mesmo item de
alucinação. LLM-as-Judge tem variância. Por isso a análise se apoia em padrões recorrentes
em vários exemplos, e não em casos isolados.

### Mudanças para a iteração 4

Tese: **alinhar os exemplos few-shot com as instruções.**

1. **Exemplos reescritos:** além do simples e do complexo, dois exemplos médios, um de
   integração com passos numerados (mostrando HTTP de sucesso, efeitos esperados e que passos
   não tornam o bug complexo) e um de permissão entre perfis (mostrando "Critérios Adicionais
   para [perfil]:" e "Contexto de Segurança:").
2. **Critério de complexidade:** passos de reprodução, detalhes e observações em lista não
   são problemas distintos.
3. **Seções complementares no modelo MÉDIO:** incluir "Critérios de Acessibilidade:" e
   "Critérios Adicionais para [perfil]:" entre as opções.
4. **Regra de performance:** o critério deve exigir desempenho melhor que o atual, nunca
   repetir o valor do problema como meta.

**Ajustes feitos durante o teste de fumaça (antes da avaliação):**

5. **Contradições removidas:** o modelo MÉDIO dizia "seções somente se o relato trouxer
   informação" e a regra 6 dizia "não acrescente seções que o relato não sustenta", o que
   contradizia as seções de boas práticas. Agora: "uma a três seções adequadas ao tipo de bug"
   e "bug médio usa o modelo MÉDIO, nunca o COMPLEXO".
6. **Brechas do modelo MÉDIO fechadas:** no teste, o bug do Android copiou "Problemas
   Identificados" e "Tasks" sem usar `===`, e dois bugs inventaram "Severidade: ALTA". Foi
   acrescentado: "Título, Descrição, Problemas Identificados e Tasks Técnicas Sugeridas são
   exclusivas do COMPLEXO. Só escreva Severidade se o relato informar."

Teste de fumaça (só geração, sem o juiz): o modal passou a incluir "Critérios de
Acessibilidade", o webhook e o Android saíram no formato MÉDIO sem severidade inventada, e o
relatório lento passou a exigir "menos de 60 segundos" em vez de repetir os 2 minutos do
sintoma. O endpoint de usuários ainda saiu no formato COMPLEXO, mas com os dois perfis
(403 e 200) e os dados expostos, que eram as omissões apontadas pelo juiz.

---

## Iteração 4: few-shot alinhado às instruções ✅ APROVADO

**Data:** 2026-10-18
**Experimento:** `alexandre-silva-bug_to_user_story_v2-a3853820`
**Link:** https://smith.langchain.com/o/830b566d-4887-40ca-8544-046d339e768a/datasets/b866f1cb-44b0-46a9-8170-1d131d830df6/compare?selectedSessions=61e18230-d687-4bbf-bbc3-8f326fc74e96
**Commit:** `a841aaa`

### Resultado

| Métrica | Iter. 1 | Iter. 3 | Iter. 4 | Status |
|---|---|---|---|---|
| F1-Score | 0.7623 | 0.7762 | **0.8025** | ✅ |
| Clarity | 0.88 | 0.87 | **0.8833** | ✅ |
| Precision | 0.81 | 0.8207 | **0.8627** | ✅ |
| Helpfulness | 0.85 | 0.8453 | **0.873** | ✅ |
| Correctness | 0.79 | 0.7984 | **0.8326** | ✅ |
| **Média** | 0.8174 | 0.8221 | **0.8508** | ✅ |
| Bugs médios no formato COMPLEXO | 4 | — | **1** | |

### Diagnóstico

A tese da iteração se confirmou: **alinhar os exemplos few-shot com as instruções foi a
mudança de maior impacto do processo.** Nas iterações 2 e 3, mudar apenas instruções moveu o
F1 em no máximo +0.014. Com os exemplos demonstrando as seções pedidas, o F1 subiu +0.026 e a
Precision +0.042, porque as respostas passaram a cobrir os critérios que o gabarito contém
(acessibilidade, perfis diferentes, efeitos esperados de integrações) e a respeitar o formato
MÉDIO.

### Margem e limitações

- **A margem do F1 é pequena (0.8025).** Como o juiz é um LLM, há variância entre execuções
  (ver o ruído registrado na iteração 3). Uma nova execução do mesmo prompt pode oscilar em
  torno do limite.
- O bug de segurança do endpoint de usuários continua saindo no formato COMPLEXO, embora agora
  com o conteúdo correto (os dois perfis e os dados expostos).
