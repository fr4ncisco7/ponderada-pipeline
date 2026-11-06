"""
versao3.py - Produtor/consumidor com semáforos em ORDEM TROCADA (Ponderada CC08, questão A4.3).

Igual à versão 2, mas o produtor faz wait(mutex) ANTES de wait(vazio). Quando o
buffer enche, o produtor dorme em `vazio` segurando o `mutex`; o consumidor,
que é o único que poderia liberar `vazio`, fica bloqueado em `mutex`. Resultado:
deadlock. Todo wait usa timeout de 1 s para detectar o travamento e encerrar.

Uso:
    python3 versao3.py                 # 3 execuções de 20.000 amostras
    python3 versao3.py --execucoes 1 --amostras 5000

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
    Roda uma execução do produtor/consumidor com a ordem de wait trocada.

    Parâmetros:
        total_amostras (int): quantas amostras o produtor gera.

    Retorno:
        dict com as chaves:
            consumidas (int): quantas leituras o consumidor fez;
            perdidas (int): amostras 0..total-1 que nunca foram lidas;
            duplicadas (int): leituras extras de amostras já lidas;
            travou (bool): se alguma thread ficou 1 s bloqueada.

    Funcionamento:
        Produtor: wait(mutex) -> wait(vazio) -> insere -> signal(mutex) -> signal(cheio).
        Consumidor: wait(cheio) -> wait(mutex) -> retira -> signal(mutex) -> signal(vazio).
        Se o produtor pegar o mutex com o buffer cheio, nenhuma das duas avança.
    """
    vazio = threading.Semaphore(N)
    cheio = threading.Semaphore(0)
    mutex = threading.Semaphore(1)
    buffer = [None] * N
    recebidas = []
    estado = {"travou": False, "travamento": ""}

    def esperar(semaforo, quem, nome):
        """
        Executa wait(semaforo) com timeout e registra onde houve travamento.

        Parâmetros:
            semaforo (threading.Semaphore): semáforo a decrementar.
            quem (str): nome da thread que espera ("produtor" ou "consumidor").
            nome (str): nome do semáforo, usado na mensagem de travamento.

        Retorno:
            bool: True se conseguiu o semáforo; False se outra thread já
            registrou travamento ou se o timeout de TIMEOUT_TRAVA estourou
            (nesse caso marca estado["travou"] e anota em estado["travamento"]).
        """
        if estado["travou"]:
            return False
        if not semaforo.acquire(timeout=TIMEOUT_TRAVA):
            estado["travou"] = True
            estado["travamento"] += f"{quem} preso em wait({nome}); "
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
            ORDEM TROCADA: faz wait(mutex) e depois wait(vazio). Com o buffer cheio,
            dorme em `vazio` segurando o mutex, causando o deadlock.
            Libera o mutex e sinaliza `cheio` depois de cada inserção.
        """
        entrada = 0
        for amostra in range(total_amostras):
            if not esperar(mutex, "produtor", "mutex"):   # ordem trocada:
                return
            if not esperar(vazio, "produtor", "vazio"):   # dorme segurando o mutex
                mutex.release()
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
            if not esperar(cheio, "consumidor", "cheio"):
                return
            if not esperar(mutex, "consumidor", "mutex"):
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

    resultado = avaliar(recebidas, total_amostras, estado["travou"])
    resultado["travamento"] = estado["travamento"]
    return resultado


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
    parser = argparse.ArgumentParser(description="A4 versão 3: ordem dos waits trocada")
    parser.add_argument("--execucoes", type=int, default=3)
    parser.add_argument("--amostras", type=int, default=20000)
    args = parser.parse_args()

    print(f"Versão 3 (wait(mutex) antes de wait(vazio)) | N = {N} | {args.amostras} amostras")
    print(f"{'exec':>4} {'consumidas':>10} {'perdidas':>8} {'duplicadas':>10} {'travou':>6}  detalhe")
    for i in range(1, args.execucoes + 1):
        r = executar(args.amostras)
        print(f"{i:>4} {r['consumidas']:>10} {r['perdidas']:>8} {r['duplicadas']:>10} "
              f"{'sim' if r['travou'] else 'não':>6}  {r['travamento']}")


if __name__ == "__main__":
    main()
