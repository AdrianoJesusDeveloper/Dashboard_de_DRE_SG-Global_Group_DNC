"""ETL, padronização e métricas da DRE e do fluxo de caixa."""

import pandas as pd
import numpy as np

COLUNAS_BASE = [
    "Data de Competência", "Categoria", "Descrição", "Cliente / Fornecedor",
    "Valor recebido", "Valor pago", "Conta", "Centro de custo", "Empresa",
    "Classificação", "Orçado",
]

GRUPO_DRE = {
    "Receitas": "Receita", "Devolução": "Devoluções",
    "Custos Variável": "Custos Variáveis", "Custos Fixo": "Custos Fixos",
    "Despesas Fixa": "Despesas Fixas", "Despesas Variavel": "Despesas Variáveis",
    "Resultado Financeiro": "Resultado Financeiro",
    "Resultado não operacional": "Resultado Não Operacional",
    "Impostos": "Impostos", "Capex": "Capex", "Empréstimos": "Empréstimos",
    "Retirada de sócios": "Retirada de Sócios", "Aportes de capital": "Aportes de Capital",
    "Outras movimentações de caixa": "Outras Movimentações",
}

RECEITA_GRUPOS = ["Receita"]
CUSTO_VARIAVEL_GRUPOS = ["Custos Variáveis"]
CUSTO_GRUPOS = ["Custos Variáveis", "Custos Fixos"]
DESPESA_GRUPOS = ["Despesas Fixas", "Despesas Variáveis"]


def _load_raw(path):
    df = pd.read_excel(path, sheet_name="Base")
    return df[[c for c in COLUNAS_BASE if c in df.columns]].copy()


def clean_base(path, moeda):
    df = _load_raw(path)
    for c in ["Categoria", "Classificação", "Empresa", "Centro de custo", "Conta", "Orçado"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().replace({"nan": np.nan})
    df["Data de Competência"] = pd.to_datetime(df["Data de Competência"], errors="coerce")
    df = df.dropna(subset=["Data de Competência"])
    for c in ["Valor recebido", "Valor pago"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["Fluxo"] = df["Valor recebido"] - df["Valor pago"]
    df["Cenário"] = df["Orçado"].fillna("Realizado")
    df["Grupo DRE"] = df["Classificação"].map(GRUPO_DRE).fillna(df["Classificação"])
    df["Ano"] = df["Data de Competência"].dt.year
    df["Mes"] = df["Data de Competência"].dt.month
    df["AnoMes"] = df["Data de Competência"].dt.to_period("M").dt.to_timestamp()
    df["Moeda"] = moeda
    return df.reset_index(drop=True)


def load_all(path_br, path_us):
    return {"BRL": clean_base(path_br, "BRL"), "USD": clean_base(path_us, "USD")}


def kpis(df):
    receita = df.loc[df["Grupo DRE"].isin(RECEITA_GRUPOS), "Valor recebido"].sum()
    devolucoes = df.loc[df["Grupo DRE"] == "Devoluções", "Valor pago"].sum()
    receita_liquida = receita - devolucoes
    custos = df.loc[df["Grupo DRE"].isin(CUSTO_GRUPOS), "Valor pago"].sum()
    despesas = df.loc[df["Grupo DRE"].isin(DESPESA_GRUPOS), "Valor pago"].sum()
    impostos = df.loc[df["Grupo DRE"] == "Impostos", "Valor pago"].sum()
    resultado_operacional = receita_liquida - custos - despesas
    resultado_liquido = resultado_operacional - impostos
    margem = resultado_operacional / receita_liquida if receita_liquida else np.nan
    margem_liquida = resultado_liquido / receita_liquida if receita_liquida else np.nan
    return {
        "Receita": receita,
        "Devoluções": devolucoes,
        "Receita Líquida": receita_liquida,
        "Custos Variáveis e Fixos": custos,
        "Despesas": despesas,
        "Impostos": impostos,
        "Resultado Operacional": resultado_operacional,
        "Resultado Líquido": resultado_liquido,
        "Margem %": margem,
        "Margem Líquida %": margem_liquida,
    }


def evolucao_mensal(df):
    g = df.copy()
    g["Tipo"] = np.select(
        [g["Grupo DRE"].isin(RECEITA_GRUPOS), g["Grupo DRE"].isin(CUSTO_GRUPOS + DESPESA_GRUPOS)],
        ["Receita Líquida", "Custos e Despesas"], default="Outros"
    )
    g["Valor"] = np.where(g["Tipo"] == "Receita Líquida", g["Valor recebido"], g["Valor pago"])
    resumo = g[g["Tipo"] != "Outros"].groupby(["AnoMes", "Tipo"], as_index=False)["Valor"].sum()
    pivot = resumo.pivot(index="AnoMes", columns="Tipo", values="Valor").fillna(0)
    pivot["Resultado Operacional"] = pivot.get("Receita Líquida", 0) - pivot.get("Custos e Despesas", 0)
    return pivot.reset_index()


def composicao_por_grupo(df):
    return (
        df[df["Grupo DRE"].isin(CUSTO_GRUPOS + DESPESA_GRUPOS)]
        .groupby("Grupo DRE", as_index=False)["Valor pago"].sum()
        .sort_values("Valor pago", ascending=False)
    )


def kpis_avancados(df):
    k = kpis(df)
    custos_var = df.loc[df["Grupo DRE"].isin(CUSTO_VARIAVEL_GRUPOS), "Valor pago"].sum()
    margem_contribuicao = ((k["Receita Líquida"] - custos_var) / k["Receita Líquida"]
                           if k["Receita Líquida"] else np.nan)
    # Proxy operacional: a base não permite calcular EBITDA contábil estrito.
    ebitda_proxy = k["Receita Líquida"] - k["Custos Variáveis e Fixos"] - k["Despesas"]
    return {
        "Receita Bruta": k["Receita"],
        "Receita Líquida": k["Receita Líquida"],
        "Margem de Contribuição %": margem_contribuicao,
        "EBITDA (proxy)": ebitda_proxy,
        "Resultado Operacional": k["Resultado Operacional"],
        "Resultado Líquido": k["Resultado Líquido"],
        "Margem Líquida %": k["Margem Líquida %"],
    }


COLUNAS_CAIXA = ["Data", "Empresa", "Orçado", "Entradas", "Saídas", "Net Cash", "Saldo Inicial", "Saldo Final", "Squad"]


def clean_caixa(path, moeda):
    df = pd.read_excel(path, sheet_name="Caixa mensal")
    df = df[[c for c in COLUNAS_CAIXA if c in df.columns]].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"])
    for c in ["Entradas", "Saídas", "Net Cash", "Saldo Inicial", "Saldo Final"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["Empresa"] = df["Empresa"].astype(str).str.strip()
    df["Moeda"] = moeda
    return df.reset_index(drop=True)


def load_all_caixa(path_br, path_us):
    return {"BRL": clean_caixa(path_br, "BRL"), "USD": clean_caixa(path_us, "USD")}


def tem_fluxo_de_caixa_real(df_caixa):
    return bool((df_caixa["Entradas"].abs().sum() + df_caixa["Saídas"].abs().sum()) > 0)


def evolucao_caixa(df_caixa):
    return (
        df_caixa.groupby("Data", as_index=False)
        .agg({"Entradas": "sum", "Saídas": "sum", "Net Cash": "sum", "Saldo Final": "sum"})
        .sort_values("Data")
    )


def indicadores_caixa(df_caixa):
    serie = evolucao_caixa(df_caixa)
    saldo_atual = serie["Saldo Final"].iloc[-1] if len(serie) else np.nan
    meses_queima = serie[serie["Net Cash"] < 0]
    burn_rate = -meses_queima["Net Cash"].mean() if len(meses_queima) else 0.0
    runway = saldo_atual / burn_rate if burn_rate > 0 else np.inf
    return {"Saldo Atual": saldo_atual, "Burn Rate Médio": burn_rate, "Runway (meses)": runway}


def ultima_data_com_movimento(df_caixa):
    mov = df_caixa[(df_caixa["Entradas"] != 0) | (df_caixa["Saídas"] != 0)]
    return mov["Data"].max() if len(mov) else None
