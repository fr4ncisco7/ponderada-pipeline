"""
versao1.py - Produtor/consumidor SEM sincronização (Ponderada CC08, questão A4.1).

Simula a pulseira Tato: a thread do sensor (produtora) gera amostras numeradas
0, 1, 2, ... e a thread do motor (consumidora) as retira de um buffer circular
de N posições. A única coordenação é um contador compartilhado `ocupadas` e
espera ocupada. Um time.sleep(0) entre ler e escrever o contador força a troca
de thread no pior momento e expõe a condição de corrida.

Uso:
    python3 versao1.py                 # 3 execuções de 20.000 amostras
    python3 versao1.py --execucoes 1 --amostras 5000

Autor: Francisco de Araujo Ferreira Filho (D1 = 9, D2 = 0, N = 3)
"""

import argparse
import threading
import time
from collections import Counter

N = 3                 # tamanho do buffer: 3 + (D2 mod 5), com D2 = 0
TIMEOUT_TRAVA = 1.0   # segundos sem receber nada => travamento


def executar(total_amostras):
    """
    Roda uma execução do produtor/consumidor sem sincronização.

    Parâmetros:
        total_amostras (int): quantas amostras o produtor gera.

    Retorno:
        dict com as chaves:
            consumidas (int): quantas leituras o consumidor fez;
            perdidas (int): amostras 0..total-1 que nunca foram lidas;
            duplicadas (int): leituras extras de amostras já lidas;
            travou (bool): se o consumidor ficou 1 s sem receber nada.

    Funcionamento:
        Produtor e consumidor acessam o buffer e o contador `ocupadas` sem
        nenhuma exclusão mútua. A atualização do contador é feita em dois
        passos (ler, ceder a CPU, escrever), então incrementos e decrementos
        se perdem e o contador deixa de refletir o buffer.
    """
    estado = {"ocupadas": 0, "produtor_terminou": False, "parar": False}
    buffer = [None] * N
    recebidas = []

    def produtor():
        """
        Thread produtora (sensor): gera as amostras 0..total_amostras-1.

        Parâmetros:
            nenhum (usa total_amostras, buffer e estado do escopo de executar).

        Retorno:
            None. Ao terminar, marca estado["produtor_terminou"] = True.

        Funcionamento:
            Faz espera ocupada enquanto o contador indica buffer cheio, escreve a
            amostra na posição `entrada` e incrementa `ocupadas` em dois passos
            (ler, time.sleep(0), escrever), o que expõe a condição de corrida.
            Encerra antes do fim se o consumidor sinalizar estado["parar"].
        """
        entrada = 0
        for amostra in range(total_amostras):
            while estado["ocupadas"] >= N:          # espera ocupada: buffer cheio
                if estado["parar"]:
                    return
                time.sleep(0)
            buffer[entrada] = amostra
            entrada = (entrada + 1) % N
            lido = estado["ocupadas"]                # região crítica: ler...
            time.sleep(0)                            # ...ser interrompida...
            estado["ocupadas"] = lido + 1            # ...e escrever
        estado["produtor_terminou"] = True

    def consumidor():
        """
        Thread consumidora (motor): retira amostras do buffer.

        Parâmetros:
            nenhum (usa buffer, estado e recebidas do escopo de executar).

        Retorno:
            None. Cada valor lido é anexado à lista `recebidas`.

        Funcionamento:
            Faz espera ocupada enquanto o contador indica buffer vazio, lê a
            posição `saida` e decrementa `ocupadas` em dois passos (ler,
            time.sleep(0), escrever). Encerra quando o produtor terminou e o
            contador chegou a 0, ou após TIMEOUT_TRAVA segundos sem receber nada
            (travamento), sinalizando estado["parar"] para o produtor.
        """
        saida = 0
        ultimo_recebimento = time.monotonic()
        while True:
            while estado["ocupadas"] <= 0:           # espera ocupada: buffer vazio
                if estado["produtor_terminou"]:
                    return
                if time.monotonic() - ultimo_recebimento > TIMEOUT_TRAVA:
                    estado["parar"] = True
                    return
                time.sleep(0)
            recebidas.append(buffer[saida])
            saida = (saida + 1) % N
            ultimo_recebimento = time.monotonic()
            lido = estado["ocupadas"]                # região crítica: ler...
            time.sleep(0)                            # ...ser interrompida...
            estado["ocupadas"] = lido - 1            # ...e escrever

    t_prod = threading.Thread(target=produtor)
    t_cons = threading.Thread(target=consumidor)
    t_prod.start()
    t_cons.start()
    t_cons.join()
    estado["parar"] = True
    t_prod.join()

    return avaliar(recebidas, total_amostras, estado["parar"] and not estado["produtor_terminou"])


def avaliar(recebidas, total_amostras, travou):
    """
    Compara o que o consumidor recebeu com o que o produtor gerou.

    Parâmetros:
        recebidas (list): valores lidos do buffer, na ordem de leitura.
        total_amostras (int): quantas amostras o produtor deveria gerar.
        travou (bool): se a execução terminou por travamento.

    Retorno:
        dict com consumidas, perdidas, duplicadas e travou.
    """
    contagem = Counter(recebidas)
    perdidas = sum(1 for a in range(total_amostras) if a not in contagem)
    duplicadas = sum(c - 1 for c in contagem.values() if c > 1)
    return {
        "consumidas": len(recebidas),
        "perdidas": perdidas,
        "duplicadas": duplicadas,
        "travou": travou,
    }


def main():
    """
    Ponto de entrada: lê os argumentos, roda as execuções e imprime a tabela.

    Parâmetros:
        nenhum (lê da linha de comando --execucoes, padrão 3, e
        --amostras, padrão 20000).

    Retorno:
        None. Imprime uma linha por execução com consumidas, perdidas,
        duplicadas e se travou.
    """
    parser = argparse.ArgumentParser(description="A4 versão 1: sem sincronização")
    parser.add_argument("--execucoes", type=int, default=3)
    parser.add_argument("--amostras", type=int, default=20000)
    args = parser.parse_args()

    print(f"Versão 1 (sem sincronização) | N = {N} | {args.amostras} amostras")
    print(f"{'exec':>4} {'consumidas':>10} {'perdidas':>8} {'duplicadas':>10} {'travou':>6}")
    for i in range(1, args.execucoes + 1):
        r = executar(args.amostras)
        print(f"{i:>4} {r['consumidas']:>10} {r['perdidas']:>8} {r['duplicadas']:>10} "
              f"{'sim' if r['travou'] else 'não':>6}")


if __name__ == "__main__":
    main()
