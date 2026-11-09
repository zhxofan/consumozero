"""ConsumoZero - API REST (Flask) para registrar e reduzir desperdício de água, energia e alimentos."""
from flask import Flask, jsonify, request, send_from_directory
from mysql.connector import Error as ErroMySQL

import config
import db
from alertas import enviar_alerta
from clima import ErroClima, previsao_semana
from logger import registrar
from referencias import comparar
from validacao import CATEGORIAS, ErroValidacao, validar_id, validar_registro

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024   # corpo máximo de 4 KB (evita abuso)
app.json.ensure_ascii = False


# ---------- utilidades ----------
def erro(mensagem, status):
    return jsonify({"erro": mensagem}), status


def ler_json():
    dados = request.get_json(silent=True)
    if dados is None:
        raise ErroValidacao("Envie um JSON válido com Content-Type: application/json.")
    return dados


def com_comparacao(registro):
    registro["analise"] = comparar(registro["categoria"], registro["quantidade"], registro["pessoas"])
    return registro


# ---------- cabeçalhos de segurança em todas as respostas ----------
@app.after_request
def cabecalhos_seguranca(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "no-referrer"
    resposta.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    return resposta


# ---------- tratamento global de erros (sem detalhes internos) ----------
@app.errorhandler(ErroValidacao)
def tratar_validacao(e):
    registrar(f"{request.method} {request.path}", f"400 {e}", "aviso")
    return erro(str(e), 400)


@app.errorhandler(ErroMySQL)
def tratar_banco(e):
    registrar(f"{request.method} {request.path}", f"500 erro_banco errno={getattr(e, 'errno', '?')}", "erro")
    return erro("Erro interno. Tente novamente mais tarde.", 500)


@app.errorhandler(404)
def tratar_404(e):
    return erro("Recurso não encontrado.", 404)


@app.errorhandler(405)
def tratar_405(e):
    return erro("Método não permitido.", 405)


@app.errorhandler(413)
def tratar_413(e):
    return erro("Requisição grande demais.", 413)


@app.errorhandler(Exception)
def tratar_generico(e):
    registrar(f"{request.method} {request.path}", f"500 {type(e).__name__}", "erro")
    return erro("Erro interno. Tente novamente mais tarde.", 500)


# ---------- interface web ----------
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------- CRUD ----------
@app.get("/api/registros")
def listar_registros():
    categoria = request.args.get("categoria")
    if categoria is not None and categoria not in CATEGORIAS:
        raise ErroValidacao("Categoria deve ser: agua, energia ou alimento.")
    registros = [com_comparacao(r) for r in db.listar(categoria)]
    registrar("GET /api/registros", f"200 total={len(registros)}")
    return jsonify(registros), 200


@app.get("/api/registros/<int:id_registro>")
def buscar_registro(id_registro):
    validar_id(id_registro)
    registro = db.buscar(id_registro)
    if registro is None:
        registrar(f"GET /api/registros/{id_registro}", "404")
        return erro("Registro não encontrado.", 404)
    registrar(f"GET /api/registros/{id_registro}", "200")
    return jsonify(com_comparacao(registro)), 200


@app.post("/api/registros")
def criar_registro():
    dados = validar_registro(ler_json())
    novo_id = db.inserir(dados)
    registro = com_comparacao(db.buscar(novo_id))
    registrar("POST /api/registros", f"201 id={novo_id} categoria={dados['categoria']}")
    if registro["analise"]["acima"]:
        enviar_alerta(registro, registro["analise"])
    return jsonify(registro), 201


@app.put("/api/registros/<int:id_registro>")
def atualizar_registro(id_registro):
    validar_id(id_registro)
    dados = validar_registro(ler_json())
    if db.buscar(id_registro) is None:
        registrar(f"PUT /api/registros/{id_registro}", "404")
        return erro("Registro não encontrado.", 404)
    db.atualizar(id_registro, dados)
    registro = com_comparacao(db.buscar(id_registro))
    registrar(f"PUT /api/registros/{id_registro}", "200")
    if registro["analise"]["acima"]:
        enviar_alerta(registro, registro["analise"])
    return jsonify(registro), 200


@app.delete("/api/registros/<int:id_registro>")
def excluir_registro(id_registro):
    validar_id(id_registro)
    if db.excluir(id_registro) == 0:
        registrar(f"DELETE /api/registros/{id_registro}", "404")
        return erro("Registro não encontrado.", 404)
    registrar(f"DELETE /api/registros/{id_registro}", "204")
    return "", 204


# ---------- resumo e fonte externa ----------
@app.get("/api/resumo")
def resumo():
    registros = [com_comparacao(r) for r in db.listar()]
    por_categoria = {}
    for cat, unidade in CATEGORIAS.items():
        da_cat = [r for r in registros if r["categoria"] == cat]
        por_categoria[cat] = {
            "unidade": unidade,
            "registros": len(da_cat),
            "acima_da_referencia": sum(1 for r in da_cat if r["analise"]["acima"]),
            "total": round(sum(r["quantidade"] for r in da_cat), 2),
        }
    registrar("GET /api/resumo", "200")
    return jsonify(por_categoria), 200


@app.get("/api/clima")
def clima():
    try:
        dados = previsao_semana()
    except ErroClima as e:
        registrar("GET /api/clima", f"503 servico_externo {e}", "aviso")
        return erro("Serviço de clima indisponível no momento.", 503)
    registrar("GET /api/clima", "200")
    return jsonify(dados), 200


if __name__ == "__main__":
    registrar("iniciar_api", "ok")
    app.run(host="127.0.0.1", port=5000, debug=config.FLASK_DEBUG)
