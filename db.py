"""Acesso ao MySQL SEM ORM. Toda consulta usa parâmetros (%s) -> evita SQL Injection."""
import mysql.connector
import config


def conectar():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
    )


def _executar(sql, parametros=(), buscar=None):
    """Abre conexão, executa e fecha. buscar = None | 'um' | 'todos'."""
    conexao = conectar()
    try:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        if buscar == "um":
            resultado = cursor.fetchone()
        elif buscar == "todos":
            resultado = cursor.fetchall()
        else:
            conexao.commit()
            resultado = cursor.lastrowid if sql.strip().upper().startswith("INSERT") else cursor.rowcount
        cursor.close()
        return resultado
    finally:
        conexao.close()


def _formatar(linha):
    """Converte tipos do MySQL (Decimal, datetime) para JSON."""
    if linha is None:
        return None
    linha["quantidade"] = float(linha["quantidade"])
    linha["criado_em"] = linha["criado_em"].strftime("%Y-%m-%d %H:%M:%S")
    return linha


COLUNAS = "id, apelido, categoria, unidade, quantidade, mes_referencia, pessoas, criado_em"


def listar(categoria=None):
    if categoria:
        sql = f"SELECT {COLUNAS} FROM registros WHERE categoria = %s ORDER BY mes_referencia DESC, id DESC"
        linhas = _executar(sql, (categoria,), buscar="todos")
    else:
        sql = f"SELECT {COLUNAS} FROM registros ORDER BY mes_referencia DESC, id DESC"
        linhas = _executar(sql, buscar="todos")
    return [_formatar(l) for l in linhas]


def buscar(id_registro):
    sql = f"SELECT {COLUNAS} FROM registros WHERE id = %s"
    return _formatar(_executar(sql, (id_registro,), buscar="um"))


def inserir(r):
    sql = ("INSERT INTO registros (apelido, categoria, unidade, quantidade, mes_referencia, pessoas) "
           "VALUES (%s, %s, %s, %s, %s, %s)")
    return _executar(sql, (r["apelido"], r["categoria"], r["unidade"],
                           r["quantidade"], r["mes_referencia"], r["pessoas"]))


def atualizar(id_registro, r):
    sql = ("UPDATE registros SET apelido=%s, categoria=%s, unidade=%s, quantidade=%s, "
           "mes_referencia=%s, pessoas=%s WHERE id=%s")
    return _executar(sql, (r["apelido"], r["categoria"], r["unidade"], r["quantidade"],
                           r["mes_referencia"], r["pessoas"], id_registro))


def excluir(id_registro):
    return _executar("DELETE FROM registros WHERE id = %s", (id_registro,))
