"""
etl.py
Módulo de limpeza e padronização das bases de dados da DRE (SG Global Group).

Lê a aba "Base" dos arquivos DRE_BR_DNC.xlsx e DRE_US_DNC.xlsx, seleciona
apenas as colunas "cruas" (evitando colunas calculadas na planilha original
que apresentam erros de fórmula: #VALUE!, "erro" etc.) e devolve um
DataFrame limpo e padronizado, pronto para alimentar o dashboard.
"""

import pandas as pd
import numpy as np

# Colunas realmente necessárias para a DRE — evita puxar as colunas
# calculadas da planilha original (que têm erro de fórmula em várias linhas)
COLUNAS_BASE = [
    "Data de Competência",
    "Categoria",
    "Descrição",
    "Cliente / Fornecedor",
    "Valor recebido",
    "Valor pago",
    "Conta",
    "Centro de custo",
    "Empresa",
    "Classificação",
    "Orçado",
]

# Mapa de classificação -> grupo macro da DRE (unifica BR e US,
# que têm rótulos ligeiramente diferentes: "Despesas Fixa" vs "Despesas Variavel" etc.)
GRUPO_DRE = {
    "Receitas": "Receita",
    "Devolução": "Receita",  # devoluções abatem receita
    "Custos Variável": "Custos Variáveis",
    "Custos Fixo": "Custos Fixos",
    "Despesas Fixa": "Despesas Fixas",
    "Despesas Variavel": "Despesas Variáveis",
    "Resultado Financeiro": "Resultado Financeiro",
    "Resultado não operacional": "Resultado Não Operacional",
    "Impostos": "Impostos",
    "Capex": "Capex",
    "Empréstimos": "Empréstimos",
    "Retirada de sócios": "Retirada de Sócios",
    "Aportes de capital": "Aportes de Capital",
    "Outras movimentações de caixa": "Outras Movimentações",
}


def _load_raw(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Base")
    # nem toda coluna existe nos dois arquivos (ex.: "Transaction ID" só no US) -> filtra o que existe
    cols = [c for c in COLUNAS_BASE if c in df.columns]
    df = df[cols].copy()
    return df


def clean_base(path: str, moeda: str) -> pd.DataFrame:
    """
    Carrega e limpa a aba Base de um arquivo DRE.

    Parameters
    ----------
    path : caminho do arquivo .xlsx
    moeda : "BRL" ou "USD" — rótulo para diferenciar as bases no dashboard

    Returns
    -------
    DataFrame limpo com colunas padronizadas.
    """
    df = _load_raw(path)

    # Strip de espaços em textos (a planilha original tem "Custos Fixo " com espaço sobrando)
    for c in ["Categoria", "Classificação", "Empresa", "Centro de custo", "Conta", "Orçado"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({"nan": np.nan})

    # Datas
    df["Data de Competência"] = pd.to_datetime(df["Data de Competência"], errors="coerce")
    df = df.dropna(subset=["Data de Competência"])

    # Valores numéricos — trata texto/erro residual como NaN
    df["Valor recebido"] = pd.to_numeric(df["Valor recebido"], errors="coerce")
    df["Valor pago"] = pd.to_numeric(df["Valor pago"], errors="coerce")

    # Fluxo líquido do lançamento (recebido positivo, pago negativo)
    df["Fluxo"] = df["Valor recebido"].fillna(0) - df["Valor pago"].fillna(0)

    # Cenário: só existe "Realizado" na Base (o "Orçado" fica em outras abas do arquivo original)
    df["Cenário"] = df["Orçado"].fillna("Realizado")

    # Grupo macro da DRE
    df["Grupo DRE"] = df["Classificação"].map(GRUPO_DRE).fillna(df["Classificação"])

    # Colunas de tempo para agregação
    df["Ano"] = df["Data de Competência"].dt.year
    df["Mes"] = df["Data de Competência"].dt.month
    df["AnoMes"] = df["Data de Competência"].dt.to_period("M").dt.to_timestamp()

    df["Moeda"] = moeda
    df["Empresa"] = df["Empresa"].str.strip()

    return df.reset_index(drop=True)


def load_all(path_br: str, path_us: str) -> dict:
    """Retorna {'BRL': df_br_limpo, 'USD': df_us_limpo}."""
    return {
        "BRL": clean_base(path_br, "BRL"),
        "USD": clean_base(path_us, "USD"),
    }


def load_all_caixa(path_br: str, path_us: str) -> dict:
    """Retorna {'BRL': caixa_br_limpo, 'USD': caixa_us_limpo}."""
    return {
        "BRL": clean_caixa(path_br, "BRL"),
        "USD": clean_caixa(path_us, "USD"),
    }


# --- Agregações usadas pelo dashboard --------------------------------------

RECEITA_GRUPOS = ["Receita"]
CUSTO_GRUPOS = ["Custos Variáveis", "Custos Fixos"]
DESPESA_GRUPOS = ["Despesas Fixas", "Despesas Variáveis"]


def kpis(df: pd.DataFrame) -> dict:
    """Calcula os KPIs principais da DRE para o recorte (já filtrado) informado."""
    receita = df.loc[df["Grupo DRE"].isin(RECEITA_GRUPOS), "Valor recebido"].sum()
    custos = df.loc[df["Grupo DRE"].isin(CUSTO_GRUPOS), "Valor pago"].sum()
    despesas = df.loc[df["Grupo DRE"].isin(DESPESA_GRUPOS), "Valor pago"].sum()
    impostos = df.loc[df["Grupo DRE"] == "Impostos", "Valor pago"].sum()
    resultado = receita - custos - despesas - impostos
    margem = (resultado / receita) if receita else np.nan
    return {
        "Receita": receita,
        "Custos Variáveis e Fixos": custos,
        "Despesas": despesas,
        "Impostos": impostos,
        "Resultado Operacional": resultado,
        "Margem %": margem,
    }


def evolucao_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Série mensal de Receita, Custos+Despesas e Resultado Operacional."""
    g = df.copy()
    g["Tipo"] = np.select(
        [g["Grupo DRE"].isin(RECEITA_GRUPOS),
         g["Grupo DRE"].isin(CUSTO_GRUPOS + DESPESA_GRUPOS)],
        ["Receita", "Custos e Despesas"],
        default="Outros",
    )
    g["Valor"] = np.where(g["Tipo"] == "Receita", g["Valor recebido"], g["Valor pago"])
    resumo = (
        g[g["Tipo"] != "Outros"]
        .groupby(["AnoMes", "Tipo"], as_index=False)["Valor"]
        .sum()
    )
    pivot = resumo.pivot(index="AnoMes", columns="Tipo", values="Valor").fillna(0)
    pivot["Resultado Operacional"] = pivot.get("Receita", 0) - pivot.get("Custos e Despesas", 0)
    return pivot.reset_index()


def composicao_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Total pago por Grupo DRE (para o gráfico de composição de custos/despesas)."""
    saida = df[df["Grupo DRE"].isin(CUSTO_GRUPOS + DESPESA_GRUPOS)]
    return (
        saida.groupby("Grupo DRE", as_index=False)["Valor pago"]
        .sum()
        .sort_values("Valor pago", ascending=False)
    )


def kpis_avancados(df: pd.DataFrame) -> dict:
    """
    Indicadores adicionais de DRE: Receita Bruta/Líquida, Margem de Contribuição,
    EBITDA (aproximado) e Margem Líquida.

    Aproximações usadas (documentadas por não haver linha de "Orçado" real nem
    detalhamento de depreciação/amortização na Base):
    - Receita Bruta = tudo classificado como "Receita".
    - Receita Líquida = Receita Bruta - Devoluções (grupo só existe na base US).
    - Margem de Contribuição = (Receita Líquida - Custos Variáveis) / Receita Líquida.
    - EBITDA (aproximado) = Receita Líquida - Custos Variáveis - Custos Fixos - Despesas
      (não há linha de depreciação/amortização separada na Base, então este é um proxy
      operacional, não um EBITDA contábil estrito).
    - Margem Líquida = Resultado Operacional (após impostos) / Receita Líquida.
    """
    devolucao = df.loc[df["Classificação"] == "Devolução", "Valor pago"].sum()
    receita_bruta = df.loc[df["Grupo DRE"].isin(RECEITA_GRUPOS), "Valor recebido"].sum()
    receita_liquida = receita_bruta - devolucao

    custos_var = df.loc[df["Grupo DRE"] == "Custos Variáveis", "Valor pago"].sum()
    custos_fixos = df.loc[df["Grupo DRE"] == "Custos Fixos", "Valor pago"].sum()
    despesas = df.loc[df["Grupo DRE"].isin(DESPESA_GRUPOS), "Valor pago"].sum()
    impostos = df.loc[df["Grupo DRE"] == "Impostos", "Valor pago"].sum()

    margem_contribuicao = np.nan
    if receita_liquida:
        margem_contribuicao = (receita_liquida - custos_var) / receita_liquida

    ebitda = receita_liquida - custos_var - custos_fixos - despesas
    resultado_liquido = ebitda - impostos
    margem_liquida = (resultado_liquido / receita_liquida) if receita_liquida else np.nan

    return {
        "Receita Bruta": receita_bruta,
        "Receita Líquida": receita_liquida,
        "Margem de Contribuição %": margem_contribuicao,
        "EBITDA (aprox.)": ebitda,
        "Resultado Líquido": resultado_liquido,
        "Margem Líquida %": margem_liquida,
    }


# --- Fluxo de Caixa (aba "Caixa mensal") -----------------------------------

COLUNAS_CAIXA = ["Data", "Empresa", "Orçado", "Entradas", "Saídas", "Net Cash", "Saldo Inicial", "Saldo Final", "Squad"]


def clean_caixa(path: str, moeda: str) -> pd.DataFrame:
    """Carrega e limpa a aba 'Caixa mensal'."""
    df = pd.read_excel(path, sheet_name="Caixa mensal")
    cols = [c for c in COLUNAS_CAIXA if c in df.columns]
    df = df[cols].copy()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])
    for c in ["Entradas", "Saídas", "Net Cash", "Saldo Inicial", "Saldo Final"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["Empresa"] = df["Empresa"].astype(str).str.strip()
    df["Moeda"] = moeda
    return df.reset_index(drop=True)


def tem_fluxo_de_caixa_real(df_caixa: pd.DataFrame) -> bool:
    """
    A aba Caixa mensal existe nos dois arquivos, mas em alguns casos vem sem
    movimentação real (Entradas/Saídas zeradas em 100% das linhas, só com um
    Saldo Final estático). Esta função sinaliza isso para o dashboard não
    apresentar Burn Rate/Runway calculados sobre dado vazio.
    """
    return bool((df_caixa["Entradas"].abs().sum() + df_caixa["Saídas"].abs().sum()) > 0)


def indicadores_caixa(df_caixa: pd.DataFrame) -> dict:
    """Saldo atual, burn rate médio e runway (em meses) a partir da Caixa mensal.

    Agrega por Data primeiro (soma todas as empresas do país no mesmo mês) antes
    de calcular — calcular direto sobre a base "achatada" misturaria o Saldo Final
    de empresas diferentes no mesmo mês.
    """
    serie = evolucao_caixa(df_caixa)
    saldo_atual = serie["Saldo Final"].iloc[-1] if len(serie) else np.nan

    meses_queima = serie[serie["Net Cash"] < 0]
    burn_rate = -meses_queima["Net Cash"].mean() if len(meses_queima) else 0.0

    runway = (saldo_atual / burn_rate) if burn_rate > 0 else np.inf

    return {"Saldo Atual": saldo_atual, "Burn Rate Médio": burn_rate, "Runway (meses)": runway}


def ultima_data_com_movimento(df_caixa: pd.DataFrame):
    """Último mês em que Entradas ou Saídas não são zero — depois disso, a aba
    normalmente só repete o último Saldo Final (sem movimentação real registrada)."""
    mov = df_caixa[(df_caixa["Entradas"] != 0) | (df_caixa["Saídas"] != 0)]
    return mov["Data"].max() if len(mov) else None


def evolucao_caixa(df_caixa: pd.DataFrame) -> pd.DataFrame:
    """Série mensal agregada (todas as empresas) de Entradas, Saídas, Net Cash e Saldo Final."""
    g = (
        df_caixa.groupby("Data", as_index=False)
        .agg({"Entradas": "sum", "Saídas": "sum", "Net Cash": "sum", "Saldo Final": "sum"})
        .sort_values("Data")
    )
    return g
