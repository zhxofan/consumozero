"""Log em arquivo: data/hora | nível | ação | resultado."""
import logging
import os

PASTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(PASTA_LOG, exist_ok=True)

_logger = logging.getLogger("consumozero")
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    arquivo = logging.FileHandler(os.path.join(PASTA_LOG, "app.log"), encoding="utf-8")
    arquivo.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                                           "%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(arquivo)


def registrar(acao, resultado, nivel="info"):
    """Grava uma linha no log. Nunca passe dados pessoais aqui (LGPD)."""
    mensagem = f"acao={acao} | resultado={resultado}"
    if nivel == "erro":
        _logger.error(mensagem)
    elif nivel == "aviso":
        _logger.warning(mensagem)
    else:
        _logger.info(mensagem)
