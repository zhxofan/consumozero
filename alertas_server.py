"""Servidor TCP do painel de alertas (rodar em outro terminal: python alertas_server.py).

Recebe uma linha JSON por conexão, mostra no terminal e responde "OK".
Pode ser usado, por exemplo, pela associação de moradores para acompanhar
casas/comércios que passaram da referência.
"""
import json
import socket
import threading
import config
from logger import registrar


def atender(conexao, endereco):
    with conexao:
        try:
            dados = conexao.recv(1024).decode("utf-8").strip()
            alerta = json.loads(dados)
            print(f"[ALERTA] {alerta['apelido']} | {alerta['categoria']} = "
                  f"{alerta['quantidade']} {alerta['unidade']} ({alerta['percentual']}% da referência)")
            registrar("alerta_recebido", f"id={alerta['id']} categoria={alerta['categoria']}")
            conexao.sendall(b"OK\n")
        except (ValueError, KeyError, UnicodeDecodeError):
            registrar("alerta_recebido", f"mensagem invalida de {endereco[0]}", "aviso")
            conexao.sendall(b"ERRO\n")


def iniciar():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((config.ALERTA_HOST, config.ALERTA_PORT))
    servidor.listen(5)
    print(f"Painel de alertas ouvindo em {config.ALERTA_HOST}:{config.ALERTA_PORT} (Ctrl+C para sair)")
    try:
        while True:
            conexao, endereco = servidor.accept()
            threading.Thread(target=atender, args=(conexao, endereco), daemon=True).start()
    except KeyboardInterrupt:
        print("\nEncerrando painel.")
    finally:
        servidor.close()


if __name__ == "__main__":
    iniciar()
