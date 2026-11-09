"""Cliente TCP: quando um consumo passa da referência, avisa o painel de alertas por socket."""
import json
import socket
import config
from logger import registrar


def enviar_alerta(registro, comparacao):
    mensagem = {
        "id": registro["id"],
        "apelido": registro["apelido"],
        "categoria": registro["categoria"],
        "quantidade": registro["quantidade"],
        "unidade": registro["unidade"],
        "percentual": comparacao["percentual_da_referencia"],
    }
    try:
        with socket.create_connection((config.ALERTA_HOST, config.ALERTA_PORT), timeout=2) as s:
            s.sendall((json.dumps(mensagem) + "\n").encode("utf-8"))
            resposta = s.recv(64).decode("utf-8").strip()
        registrar("enviar_alerta_tcp", f"ok id={registro['id']} resposta={resposta}")
        return True
    except OSError:
        # O painel pode estar desligado: a API continua funcionando normalmente.
        registrar("enviar_alerta_tcp", f"painel indisponivel id={registro['id']}", "aviso")
        return False
