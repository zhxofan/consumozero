"""Fonte externa: API pública Open-Meteo (sem chave), consumida com requests + JSON."""
import requests
import config

URL = "https://api.open-meteo.com/v1/forecast"


class ErroClima(Exception):
    """Falha ao consultar o serviço externo."""


def previsao_semana():
    parametros = {
        "latitude": config.CLIMA_LAT,
        "longitude": config.CLIMA_LON,
        "daily": "temperature_2m_max,precipitation_sum",
        "timezone": "America/Sao_Paulo",
        "forecast_days": 7,
    }
    try:
        resposta = requests.get(URL, params=parametros, timeout=8)
        resposta.raise_for_status()
        dados = resposta.json()
        diario = dados["daily"]
    except (requests.RequestException, ValueError, KeyError) as erro:
        raise ErroClima(type(erro).__name__)

    dias = []
    for data, tmax, chuva in zip(diario["time"], diario["temperature_2m_max"], diario["precipitation_sum"]):
        dias.append({"data": data, "temp_max": tmax, "chuva_mm": chuva})

    quentes = [d for d in dias if d["temp_max"] is not None and d["temp_max"] >= 30]
    chuvosos = [d for d in dias if d["chuva_mm"] and d["chuva_mm"] >= 5]

    alertas = []
    if quentes:
        alertas.append(f"{len(quentes)} dia(s) com 30°C ou mais: o consumo de água e energia tende a subir. "
                       "Guarde alimentos perecíveis na geladeira e evite deixá-la aberta.")
    if chuvosos:
        alertas.append(f"{len(chuvosos)} dia(s) com chuva forte: boa hora para captar água da chuva "
                       "para limpeza e plantas.")
    if not alertas:
        alertas.append("Semana sem extremos de calor ou chuva prevista.")

    return {"dias": dias, "alertas": alertas, "fonte": "Open-Meteo"}
