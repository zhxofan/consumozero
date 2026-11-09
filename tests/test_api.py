"""Testes automatizados (rodar: python -m unittest discover tests -v).

O banco é substituído por um "falso" em memória (mock), então os testes
rodam sem MySQL. Eles validam status HTTP, validação de entrada e segurança.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as aplicacao  # noqa: E402
from validacao import ErroValidacao, validar_registro  # noqa: E402

VALIDO = {"apelido": "Casa Teste", "categoria": "agua", "quantidade": 20,
          "mes_referencia": "2026-10", "pessoas": 4}


class BancoFalso:
    """Imita as funções do db.py guardando os dados num dicionário."""

    def __init__(self):
        self.dados, self.prox = {}, 1

    def listar(self, categoria=None):
        return [dict(r) for r in self.dados.values() if not categoria or r["categoria"] == categoria]

    def buscar(self, i):
        return dict(self.dados[i]) if i in self.dados else None

    def inserir(self, r):
        i = self.prox
        self.dados[i] = {**r, "id": i, "criado_em": "2026-11-09 10:00:00"}
        self.prox += 1
        return i

    def atualizar(self, i, r):
        self.dados[i].update(r)
        return 1

    def excluir(self, i):
        return 1 if self.dados.pop(i, None) else 0


class TestValidacao(unittest.TestCase):
    def test_valido(self):
        r = validar_registro(dict(VALIDO))
        self.assertEqual(r["unidade"], "m3")

    def test_sql_injection_no_apelido(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "apelido": "x'; DROP TABLE registros;--"})

    def test_xss_no_apelido(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "apelido": "<script>alert(1)</script>"})

    def test_campo_extra_cpf(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "cpf": "000.000.000-00"})

    def test_quantidade_negativa(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "quantidade": -5})

    def test_mes_invalido(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "mes_referencia": "2026-13"})

    def test_pessoas_booleano(self):
        with self.assertRaises(ErroValidacao):
            validar_registro({**VALIDO, "pessoas": True})


class TestApi(unittest.TestCase):
    def setUp(self):
        self.banco = BancoFalso()
        self.patches = [patch.object(aplicacao.db, nome, getattr(self.banco, nome))
                        for nome in ("listar", "buscar", "inserir", "atualizar", "excluir")]
        self.patches.append(patch.object(aplicacao, "enviar_alerta", lambda *a: True))
        for p in self.patches:
            p.start()
        self.cliente = aplicacao.app.test_client()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_crud_completo(self):
        r = self.cliente.post("/api/registros", json=VALIDO)
        self.assertEqual(r.status_code, 201)
        novo_id = r.get_json()["id"]
        self.assertTrue(r.get_json()["analise"]["acima"])  # 20 m3 > 3,3 * 4 = 13,2

        self.assertEqual(self.cliente.get("/api/registros").status_code, 200)
        self.assertEqual(self.cliente.get(f"/api/registros/{novo_id}").status_code, 200)

        r = self.cliente.put(f"/api/registros/{novo_id}", json={**VALIDO, "quantidade": 10})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.get_json()["analise"]["acima"])

        self.assertEqual(self.cliente.delete(f"/api/registros/{novo_id}").status_code, 204)
        self.assertEqual(self.cliente.get(f"/api/registros/{novo_id}").status_code, 404)

    def test_400_entrada_invalida(self):
        r = self.cliente.post("/api/registros", json={**VALIDO, "categoria": "gasolina"})
        self.assertEqual(r.status_code, 400)

    def test_400_sem_json(self):
        r = self.cliente.post("/api/registros", data="nao e json")
        self.assertEqual(r.status_code, 400)

    def test_404_put_e_delete(self):
        self.assertEqual(self.cliente.put("/api/registros/999", json=VALIDO).status_code, 404)
        self.assertEqual(self.cliente.delete("/api/registros/999").status_code, 404)

    def test_405_metodo(self):
        self.assertEqual(self.cliente.patch("/api/registros/1").status_code, 405)

    def test_413_corpo_grande(self):
        r = self.cliente.post("/api/registros", json={**VALIDO, "apelido": "a" * 10000})
        self.assertEqual(r.status_code, 413)

    def test_500_sem_detalhes_internos(self):
        def quebra(*a):
            raise RuntimeError("senha=segredo host=10.0.0.5")
        with patch.object(aplicacao.db, "listar", quebra):
            r = self.cliente.get("/api/registros")
        self.assertEqual(r.status_code, 500)
        self.assertNotIn("segredo", r.get_data(as_text=True))

    def test_cabecalhos_seguranca(self):
        r = self.cliente.get("/api/registros")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])


class TestClima(unittest.TestCase):
    def test_previsao_com_resposta_falsa(self):
        import clima

        class RespostaFalsa:
            def raise_for_status(self):
                pass

            def json(self):
                return {"daily": {"time": ["2026-11-10", "2026-11-11"],
                                  "temperature_2m_max": [32.1, 25.0],
                                  "precipitation_sum": [0.0, 12.4]}}

        with patch.object(clima.requests, "get", lambda *a, **k: RespostaFalsa()):
            dados = clima.previsao_semana()
        self.assertEqual(len(dados["dias"]), 2)
        self.assertEqual(len(dados["alertas"]), 2)  # 1 dia quente + 1 dia chuvoso

    def test_api_externa_fora_do_ar_retorna_503(self):
        import clima

        def falha(*a, **k):
            raise clima.requests.ConnectionError()

        with patch.object(clima.requests, "get", falha):
            r = aplicacao.app.test_client().get("/api/clima")
        self.assertEqual(r.status_code, 503)


if __name__ == "__main__":
    unittest.main()
