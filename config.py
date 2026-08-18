"""Configurações centrais de apresentação e moeda do dashboard."""

PAISES = {
    "Brasil": {"codigo": "BR", "moeda": "R$", "emoji": "🇧🇷"},
    "EUA": {"codigo": "US", "moeda": "US$", "emoji": "🇺🇸"},
}

MERCADOS = tuple(PAISES.keys())


def config_pais(nome: str) -> dict:
    """Retorna a configuração de um mercado usando apenas os nomes exibidos."""
    return PAISES[nome]
