# Ponderada CC08 — do pipeline ao deadlock

**Aluno:** Francisco de Araujo Ferreira Filho

Análise de arquitetura, pipeline, processos/threads, semáforos e deadlock aplicada à pulseira sensorial Tato, com a decisão de CTO sobre o processador de produção.

O documento principal está em [`ponderada/ponderada-tato.md`](./ponderada/ponderada-tato.md).

## Como rodar a questão A4

Requer Python 3 (testado com 3.12), sem dependências externas. Cada comando roda 3 execuções de 20.000 amostras com buffer de N = 3 e imprime a tabela de resultados.

```bash
python3 ponderada/codigo/versao1.py   # versão 1: sem sincronização (condição de corrida)
python3 ponderada/codigo/versao2.py   # versão 2: semáforos vazio/cheio/mutex
python3 ponderada/codigo/versao3.py   # versão 3: ordem dos waits trocada (deadlock)
```

Opções: `--execucoes K` e `--amostras M` (por exemplo, `python3 ponderada/codigo/versao1.py --execucoes 1 --amostras 5000`).

## Declaração de uso de IA

Usei o assistente de IA **Claude Code (Anthropic, modelo Claude Opus 5.5)** como apoio nesta atividade, para:

- planejar a ponderada (como dividir e organizar as respostas da Parte A e o memorando da Parte B);
- gerar os scripts em Python da A4 (`versao1.py`, `versao2.py` e `versao3.py`), que depois revisei e executei;
- revisar o conteúdo da Parte A e da Parte B e o funcionamento dos três scripts da A4;
- conferir se os números das tabelas da A4 batiam com as execuções;
- revisar erros gramaticais e a estrutura da documentação (README, `ponderada-tato.md` e os cabeçalhos e docstrings dos scripts);
- revisar a organização do repositório conforme o enunciado (README e `.gitignore` na raiz, entrega em `/ponderada`).
