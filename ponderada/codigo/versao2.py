"""
versao2.py - Produtor/consumidor COM semáforos (Ponderada CC08, questão A4.2).

Mesma pulseira Tato da versão 1, agora sincronizada com três semáforos:
    vazio (começa em N): posições livres no buffer;
    cheio (começa em 0): posições com amostra pronta;
    mutex (começa em 1): exclusão mútua no acesso ao buffer e aos índices.
O time.sleep(0) continua dentro da região crítica para mostrar que, com o
mutex, a troca de thread no pior momento deixa de causar erro.

Uso:
    python3 versao2.py                 # 3 execuções de 20.000 amostras
    python3 versao2.py --execucoes 1 --amostras 5000

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
    Roda uma execução do produtor/consumidor sincronizado por semáforos.

    Parâmetros:
        total_amostras (int): quantas amostras o produtor gera.

    Retorno:
        dict com as chaves:
            consumidas (int): quantas leituras o consumidor fez;
            perdidas (int): amostras 0..total-1 que nunca foram lidas;
            duplicadas (int): leituras extras de amostras já lidas;
            travou (bool): se alguma thread ficou 1 s bloqueada.

    Funcionamento:
        Produtor: wait(vazio) -> wait(mutex) -> insere -> signal(mutex) -> signal(cheio).
        Consumidor: wait(cheio) -> wait(mutex) -> retira -> signal(mutex) -> signal(vazio).
        Todo wait usa timeout de 1 s; estourar o timeout é registrado como travamento.
    """
    vazio = threading.Semaphore(N)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)
    buffer = [None] * N
    recebidas = []
    estado = {"travou": False}

    def esperar(semaforo):
        """
        Executa wait(semaforo) com timeout para detectar travamento.

        Parâmetros:
            semaforo (threading.Semaphore): semáforo a decrementar.

        Retorno:
            bool: True se conseguiu o semáforo; False se outra thread já
            registrou travamento ou se o timeout de TIMEOUT_TRAVA estourou
            (nesse caso marca estado["travou"] = True).
        """
        if estado["travou"] or not semaforo.acquire(timeout=TIMEOUT_TRAVA):
            estado["travou"] = True
            return False
        return True

    def produtor():
        """
        Thread produtora (sensor): gera as amostras 0..total_amostras-1.

        Parâmetros:
            nenhum (usa total_amostras, buffer e os semáforos do escopo de executar).

        Retorno:
            None. Encerra antes do fim se algum wait estourar o timeout.

        Funcionamento:
            Faz wait(vazio) e depois wait(mutex), grava na posição `entrada`.
            Libera o mutex e sinaliza `cheio` depois de cada inserção.
        """
        entrada = 0
        for amostra in range(total_amostras):
            if not esperar(vazio):
                return
            if not esperar(mutex):
                return
            buffer[entrada] = amostra
            time.sleep(0)
            entrada = (entrada + 1) % N
            mutex.release()
            cheio.release()

    def consumidor():
        """
        Thread consumidora (motor): retira total_amostras amostras do buffer.

        Parâmetros:
            nenhum (usa buffer, recebidas e os semáforos do escopo de executar).

        Retorno:
            None. Cada valor lido é anexado à lista `recebidas`; encerra antes
            do fim se algum wait estourar o timeout.

        Funcionamento:
            Faz wait(cheio) e wait(mutex), lê a posição `saida`, libera o mutex
            e sinaliza `vazio`, abrindo espaço para o produtor.
        """
        saida = 0
        for _ in range(total_amostras):
            if not esperar(cheio):
                return
            if not esperar(mutex):
                return
            recebidas.append(buffer[saida])
            time.sleep(0)
            saida = (saida + 1) % N
            mutex.release()
            vazio.release()

    t_prod = threading.Thread(target=produtor)
    t_cons = threading.Thread(target=consumidor)
    t_prod.start()
    t_cons.start()
    t_prod.join()
    t_cons.join()

    return avaliar(recebidas, total_amostras, estado["travou"])


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
    parser = argparse.ArgumentParser(description="A4 versão 2: com semáforos")
    parser.add_argument("--execucoes", type=int, default=3)
    parser.add_argument("--amostras", type=int, default=20000)
    args = parser.parse_args()

    print(f"Versão 2 (semáforos vazio/cheio/mutex) | N = {N} | {args.amostras} amostras")
    print(f"{'exec':>4} {'consumidas':>10} {'perdidas':>8} {'duplicadas':>10} {'travou':>6}")
    for i in range(1, args.execucoes + 1):
        r = executar(args.amostras)
        print(f"{i:>4} {r['consumidas']:>10} {r['perdidas']:>8} {r['duplicadas']:>10} "
              f"{'sim' if r['travou'] else 'não':>6}")


if __name__ == "__main__":
    main()
