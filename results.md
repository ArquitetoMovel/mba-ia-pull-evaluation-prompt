# Resultados da execução do código

## Prompt V2 - Primeira execução

```shell
==================================================
Prompt: bug_to_user_story_v2
==================================================

Métricas LangSmith:
  - Helpfulness: 0.85 ✗
  - Correctness: 0.88 ✗

Métricas Customizadas:
  - F1-Score: 0.81 ✗
  - Clarity: 0.75 ✗
  - Precision: 0.96 ✓

--------------------------------------------------
📊 MÉDIA GERAL: 0.8508
--------------------------------------------------

❌ STATUS: REPROVADO (média < 0.9)
⚠️  Média atual: 0.8508 | Necessário: 0.9000

==================================================
RESUMO FINAL
==================================================

Prompts avaliados: 1
Aprovados: 0
Reprovados: 1

⚠️  Alguns prompts não atingiram média >= 0.9

Próximos passos:
1. Refatore os prompts com score baixo
2. Faça push novamente: python src/push_prompts.py

```
