"""Valores de referência (dados públicos) usados para comparar o consumo.

- Água: ONU recomenda ~110 L/pessoa/dia -> 110 * 30 / 1000 = 3,3 m³/pessoa/mês
- Energia: consumo médio residencial no Brasil ~161 kWh/mês por residência (EPE, PDE 2035)
- Alimento: desperdício doméstico no Brasil ~94 kg/pessoa/ano (PNUMA, Food Waste Index 2024)
            -> 94 / 12 = 7,8 kg/pessoa/mês (meta: ficar ABAIXO disso)
"""

REFERENCIA = {
    "agua": {"valor": 3.3, "por_pessoa": True, "fonte": "ONU: 110 L/pessoa/dia"},
    "energia": {"valor": 161.0, "por_pessoa": False, "fonte": "EPE: média residencial"},
    "alimento": {"valor": 7.8, "por_pessoa": True, "fonte": "PNUMA: 94 kg/pessoa/ano"},
}

DICAS = {
    "agua": "Verifique vazamentos (feche tudo e veja se o hidrômetro gira) e reduza o banho para 5 min.",
    "energia": "Tire aparelhos da tomada (stand-by), troque lâmpadas por LED e use a máquina com carga cheia.",
    "alimento": "Planeje as compras, use 'primeiro que vence, primeiro que sai' e reaproveite sobras.",
}


def comparar(categoria, quantidade, pessoas):
    """Devolve a referência do registro e se ele está acima dela."""
    ref = REFERENCIA[categoria]
    limite = ref["valor"] * pessoas if ref["por_pessoa"] else ref["valor"]
    percentual = round((quantidade / limite) * 100, 1)
    return {
        "referencia": round(limite, 2),
        "percentual_da_referencia": percentual,
        "acima": quantidade > limite,
        "fonte": ref["fonte"],
        "dica": DICAS[categoria] if quantidade > limite else "Consumo dentro da referência. Continue assim!",
    }
