"""Validação de TODA entrada que chega na API (lista branca)."""
import re

# categoria -> unidade de medida
CATEGORIAS = {"agua": "m3", "energia": "kWh", "alimento": "kg"}

# Apelido: só letras, números, espaço, hífen e _ (sem nome real, sem CPF, sem endereço)
REGEX_APELIDO = re.compile(r"^[A-Za-z0-9À-ÿ _-]{3,40}$")
REGEX_MES = re.compile(r"^(20[2-9][0-9])-(0[1-9]|1[0-2])$")  # AAAA-MM

QUANTIDADE_MAX = 100000
PESSOAS_MAX = 50


class ErroValidacao(Exception):
    """Erro de entrada inválida (vira HTTP 400)."""


def validar_registro(dados):
    """Recebe o JSON do cliente e devolve um dicionário limpo, ou lança ErroValidacao."""
    if not isinstance(dados, dict):
        raise ErroValidacao("Envie um JSON válido.")

    campos = {"apelido", "categoria", "quantidade", "mes_referencia", "pessoas"}
    extras = set(dados) - campos
    if extras:
        raise ErroValidacao("Campos não permitidos: " + ", ".join(sorted(extras)))

    faltando = [c for c in campos if c not in dados]
    if faltando:
        raise ErroValidacao("Campos obrigatórios: " + ", ".join(sorted(faltando)))

    apelido = str(dados["apelido"]).strip()
    if not REGEX_APELIDO.match(apelido):
        raise ErroValidacao("Apelido deve ter 3 a 40 caracteres (letras, números, espaço, - ou _).")

    categoria = str(dados["categoria"]).strip().lower()
    if categoria not in CATEGORIAS:
        raise ErroValidacao("Categoria deve ser: agua, energia ou alimento.")

    try:
        quantidade = float(dados["quantidade"])
    except (TypeError, ValueError):
        raise ErroValidacao("Quantidade deve ser um número.")
    if not (0 < quantidade <= QUANTIDADE_MAX):
        raise ErroValidacao(f"Quantidade deve estar entre 0 e {QUANTIDADE_MAX}.")

    mes = str(dados["mes_referencia"]).strip()
    if not REGEX_MES.match(mes):
        raise ErroValidacao("Mês de referência no formato AAAA-MM.")

    # bool é subclasse de int em Python, por isso a checagem extra
    pessoas = dados["pessoas"]
    if isinstance(pessoas, bool) or not isinstance(pessoas, int) or not (1 <= pessoas <= PESSOAS_MAX):
        raise ErroValidacao(f"Pessoas deve ser um inteiro entre 1 e {PESSOAS_MAX}.")

    return {
        "apelido": apelido,
        "categoria": categoria,
        "unidade": CATEGORIAS[categoria],
        "quantidade": round(quantidade, 2),
        "mes_referencia": mes,
        "pessoas": pessoas,
    }


def validar_id(valor):
    """IDs vêm da URL como int (Flask já converte); aqui só garantimos que é positivo."""
    if not isinstance(valor, int) or valor <= 0:
        raise ErroValidacao("ID inválido.")
    return valor
