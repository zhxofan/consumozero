# 💧⚡🥕 ConsumoZero

Protótipo CitizenTech (Global Solution – Coding for Security) para **reduzir desperdício de água, energia e alimentos** em residências, comunidades e pequenos negócios.

A família ou o comerciante registra o consumo do mês (sem dados pessoais, só um apelido). O sistema compara com referências públicas (ONU, EPE, PNUMA), mostra se está acima, dá uma dica prática, envia alerta para um painel via socket TCP e cruza com a previsão do tempo (Open-Meteo) para avisar sobre dias de calor ou chuva.

## Funcionalidades

| Requisito | Onde está |
|---|---|
| API REST Flask (GET, POST, PUT, DELETE) com status corretos | `app.py` |
| MySQL com CRUD em Python puro, sem ORM, consultas parametrizadas | `db.py`, `schema.sql` |
| Fonte externa com `requests` + JSON | `clima.py` (Open-Meteo, sem chave) |
| Interface web HTML/CSS consumindo a API | `static/` |
| Log em arquivo (data/hora, ação, resultado) | `logger.py` → `logs/app.log` |
| Módulo extra: sockets TCP | `alertas.py` (cliente) e `alertas_server.py` (servidor) |
| Validação de entrada | `validacao.py` |
| Testes automatizados | `tests/test_api.py` |

## Estrutura

```
consumozero/
├── app.py              # rotas da API + tratamento de erros + cabeçalhos de segurança
├── config.py           # lê o .env
├── db.py               # CRUD MySQL (sem ORM)
├── validacao.py        # validação (lista branca) de toda entrada
├── referencias.py      # valores de referência e dicas
├── clima.py            # API externa Open-Meteo
├── alertas.py          # cliente TCP (envia alerta)
├── alertas_server.py   # servidor TCP (painel de alertas)
├── logger.py           # log em arquivo
├── schema.sql          # cria banco, tabela, usuário de privilégio mínimo e dados fictícios
├── static/             # index.html, style.css, app.js
├── tests/test_api.py   # 17 testes (rodam sem MySQL)
├── logs/               # app.log é gerado aqui
├── requirements.txt
└── .env.example
```

## Como executar do zero

### 1. Pré-requisitos
- Python 3.10+
- MySQL 8.0.16+ (precisa suportar `CHECK`)

### 2. Ambiente Python
```bash
cd consumozero
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Banco de dados
Abra o `schema.sql`, **troque a senha** do usuário `consumozero_app` e rode como root:
```bash
mysql -u root -p < schema.sql
```
(No MySQL Workbench: abra o arquivo e execute tudo com o raio ⚡.)

### 4. Arquivo .env
```bash
# Windows
copy .env.example .env
# Linux/Mac
cp .env.example .env
```
Coloque no `.env` a mesma senha usada no `schema.sql`.

### 5. Rodar
Terminal 1 – painel de alertas (opcional, mas recomendado para a demo):
```bash
python alertas_server.py
```
Terminal 2 – API + interface:
```bash
python app.py
```
Acesse **http://127.0.0.1:5000**

### 6. Testes
```bash
python -m unittest discover tests -v
```

## Endpoints

| Método | Rota | Sucesso | Erros |
|---|---|---|---|
| GET | `/api/registros` (`?categoria=agua`) | 200 | 400, 500 |
| GET | `/api/registros/<id>` | 200 | 404 |
| POST | `/api/registros` | 201 | 400, 413 |
| PUT | `/api/registros/<id>` | 200 | 400, 404 |
| DELETE | `/api/registros/<id>` | 204 | 404 |
| GET | `/api/resumo` | 200 | 500 |
| GET | `/api/clima` | 200 | 503 (serviço externo fora) |

Exemplo de corpo (POST/PUT):
```json
{
  "apelido": "Casa Azul",
  "categoria": "agua",
  "quantidade": 18.5,
  "mes_referencia": "2026-10",
  "pessoas": 4
}
```

Teste rápido com curl:
```bash
curl -X POST http://127.0.0.1:5000/api/registros -H "Content-Type: application/json" -d "{\"apelido\":\"Casa Azul\",\"categoria\":\"agua\",\"quantidade\":18.5,\"mes_referencia\":\"2026-10\",\"pessoas\":4}"
curl http://127.0.0.1:5000/api/registros
curl -X PUT http://127.0.0.1:5000/api/registros/1 -H "Content-Type: application/json" -d "{\"apelido\":\"Casa Azul\",\"categoria\":\"agua\",\"quantidade\":12,\"mes_referencia\":\"2026-10\",\"pessoas\":4}"
curl -X DELETE http://127.0.0.1:5000/api/registros/1 -i
```

## Segurança

- Credenciais só no `.env` (fora do Git via `.gitignore`)
- Consultas parametrizadas (`%s`) em todo o `db.py`
- Validação por lista branca: campos permitidos, regex no apelido e no mês, faixas numéricas
- Mensagens de erro genéricas; detalhes só no log (sem dados pessoais)
- Usuário do MySQL com privilégio mínimo (só CRUD na tabela)
- Limite de 4 KB no corpo da requisição
- Cabeçalhos de segurança (CSP, nosniff, X-Frame-Options) e front sem `innerHTML`
- LGPD: só apelido + números de consumo. Nada de nome, CPF, endereço ou telefone.

## Referências usadas

- ONU – 110 L/pessoa/dia de água
- EPE – consumo médio residencial ~161 kWh/mês (PDE 2035)
- PNUMA – Food Waste Index Report 2024: ~94 kg/pessoa/ano desperdiçados em domicílios no Brasil
- Instituto Trata Brasil – Estudo de Perdas de Água 2025

## Dados

Todos os dados do projeto são **fictícios**. A previsão do tempo vem da API aberta Open-Meteo.
