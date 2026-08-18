"""
app.py — Dashboard DRE SG Global Group (BR + US lado a lado)
Rodar com: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from etl import (
    load_all, kpis, evolucao_mensal, composicao_por_grupo,
    load_all_caixa, kpis_avancados, tem_fluxo_de_caixa_real,
    indicadores_caixa, evolucao_caixa, ultima_data_com_movimento,
)

# --------------------------------------------------------------------------
# Config geral e identidade visual da SG Global Group
# --------------------------------------------------------------------------
COR_DESTAQUE = "#FF4800"
COR_FUNDO = "#0F0F24"
COR_NEUTRA = "#888888"

st.set_page_config(page_title="DRE • SG Global Group", layout="wide", page_icon="📊")

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: #FFFFFF; }}
    h1, h2, h3 {{ color: {COR_FUNDO}; }}
    div[data-testid="stMetric"] {{
        background-color: {COR_FUNDO};
        border-radius: 10px;
        padding: 14px;
    }}
    div[data-testid="stMetricLabel"] {{ color: {COR_NEUTRA} !important; }}
    div[data-testid="stMetricValue"] {{ color: {COR_DESTAQUE} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 Dashboard DRE — SG Global Group")
st.caption("Leitura consolidada da Demonstração do Resultado do Exercício (Brasil e EUA)")

# --------------------------------------------------------------------------
# Carregamento dos dados (cacheado)
# --------------------------------------------------------------------------


@st.cache_data(show_spinner="Carregando e limpando as bases...")
def carregar_dados(path_br, path_us):
    return load_all(path_br, path_us)


@st.cache_data(show_spinner="Carregando fluxo de caixa...")
def carregar_caixa(path_br, path_us):
    return load_all_caixa(path_br, path_us)


with st.sidebar:
    st.header("Fonte de dados")
    modo = st.radio("Como carregar os arquivos?", ["Usar arquivos padrão (./data)", "Enviar manualmente"])
    if modo == "Enviar manualmente":
        up_br = st.file_uploader("DRE_BR_DNC.xlsx", type="xlsx")
        up_us = st.file_uploader("DRE_US_DNC.xlsx", type="xlsx")
        path_br, path_us = up_br, up_us
    else:
        path_br, path_us = "data/DRE_BR_DNC.xlsx", "data/DRE_US_DNC.xlsx"

if not path_br or not path_us:
    st.info("Envie os dois arquivos na barra lateral para carregar o dashboard.")
    st.stop()

dados = carregar_dados(path_br, path_us)
df_br_full, df_us_full = dados["BRL"], dados["USD"]

caixa = carregar_caixa(path_br, path_us)
caixa_br_full, caixa_us_full = caixa["BRL"], caixa["USD"]

# --------------------------------------------------------------------------
# Filtros (barra lateral)
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    empresas_br = sorted(df_br_full["Empresa"].dropna().unique())
    empresas_us = sorted(df_us_full["Empresa"].dropna().unique())

    sel_empresas_br = st.multiselect("Empresas (BR)", empresas_br, default=empresas_br)
    sel_empresas_us = st.multiselect("Empresas (US)", empresas_us, default=empresas_us)

    data_min = min(df_br_full["Data de Competência"].min(), df_us_full["Data de Competência"].min())
    data_max = max(df_br_full["Data de Competência"].max(), df_us_full["Data de Competência"].max())
    periodo = st.slider(
        "Período de competência",
        min_value=data_min.to_pydatetime(),
        max_value=data_max.to_pydatetime(),
        value=(data_min.to_pydatetime(), data_max.to_pydatetime()),
        format="MM/YYYY",
    )

df_br = df_br_full[
    df_br_full["Empresa"].isin(sel_empresas_br)
    & df_br_full["Data de Competência"].between(periodo[0], periodo[1])
]
df_us = df_us_full[
    df_us_full["Empresa"].isin(sel_empresas_us)
    & df_us_full["Data de Competência"].between(periodo[0], periodo[1])
]

# Fluxo de caixa: filtra só por período (a lista de empresas da aba Caixa mensal
# não é exatamente a mesma da aba Base — ver aviso na seção de Fluxo de Caixa)
caixa_br = caixa_br_full[caixa_br_full["Data"].between(periodo[0], periodo[1])]
caixa_us = caixa_us_full[caixa_us_full["Data"].between(periodo[0], periodo[1])]

# --------------------------------------------------------------------------
# Visão Geral — cartões de KPI lado a lado (BR x US)
# --------------------------------------------------------------------------
st.subheader("Visão Geral")

col_br, col_us = st.columns(2)

for col, df_pais, moeda, simbolo in [
    (col_br, df_br, "Brasil (R$)", "R$"),
    (col_us, df_us, "EUA (US$)", "US$"),
]:
    with col:
        st.markdown(f"#### {moeda}")
        k = kpis(df_pais)
        c1, c2 = st.columns(2)
        c1.metric("Receita", f"{simbolo} {k['Receita']:,.0f}")
        c2.metric("Resultado Operacional", f"{simbolo} {k['Resultado Operacional']:,.0f}")
        c3, c4 = st.columns(2)
        c3.metric("Custos + Despesas", f"{simbolo} {(k['Custos Variáveis e Fixos'] + k['Despesas']):,.0f}")
        c4.metric("Margem", f"{k['Margem %']*100:,.1f}%" if pd.notna(k["Margem %"]) else "—")

st.divider()

# --------------------------------------------------------------------------
# Indicadores avançados de DRE — Receita Bruta/Líquida, Margem de Contribuição, EBITDA
# --------------------------------------------------------------------------
st.subheader("Indicadores de Resultado e DRE")
st.caption(
    "EBITDA aqui é uma aproximação operacional (Receita Líquida − Custos − Despesas): "
    "a Base não traz uma linha separada de depreciação/amortização para isolar do EBITDA contábil estrito."
)

col_br, col_us = st.columns(2)
for col, df_pais, simbolo in [(col_br, df_br, "R$"), (col_us, df_us, "US$")]:
    with col:
        ka = kpis_avancados(df_pais)
        c1, c2 = st.columns(2)
        c1.metric("Receita Bruta", f"{simbolo} {ka['Receita Bruta']:,.0f}")
        c2.metric("Receita Líquida", f"{simbolo} {ka['Receita Líquida']:,.0f}")
        c3, c4 = st.columns(2)
        c3.metric("Margem de Contribuição", f"{ka['Margem de Contribuição %']*100:,.1f}%" if pd.notna(ka["Margem de Contribuição %"]) else "—")
        c4.metric("EBITDA (aprox.)", f"{simbolo} {ka['EBITDA (aprox.)']:,.0f}")
        c5, _ = st.columns(2)
        c5.metric("Margem Líquida", f"{ka['Margem Líquida %']*100:,.1f}%" if pd.notna(ka["Margem Líquida %"]) else "—")

st.divider()

# --------------------------------------------------------------------------
# Fluxo de Caixa (aba "Caixa mensal")
# --------------------------------------------------------------------------
st.subheader("Fluxo de Caixa")

col_br, col_us = st.columns(2)
for col, df_caixa_pais, titulo, simbolo in [
    (col_br, caixa_br, "Brasil", "R$"),
    (col_us, caixa_us, "EUA", "US$"),
]:
    with col:
        st.markdown(f"#### {titulo}")
        if not tem_fluxo_de_caixa_real(df_caixa_pais):
            st.warning(
                "A aba **Caixa mensal** desta base não tem Entradas/Saídas reais registradas "
                "(fica zerada, só repetindo um Saldo Final estático). Burn Rate e Runway não "
                "podem ser calculados de forma confiável aqui — é preciso pedir esse dado à empresa."
            )
            continue

        ic = indicadores_caixa(df_caixa_pais)
        ultima_mov = ultima_data_com_movimento(df_caixa_pais)
        if ultima_mov is not None:
            st.caption(f"Última movimentação real registrada: {ultima_mov.strftime('%m/%Y')} — meses seguintes só repetem o saldo.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Atual", f"{simbolo} {ic['Saldo Atual']:,.0f}")
        c2.metric("Burn Rate Médio", f"{simbolo} {ic['Burn Rate Médio']:,.0f}/mês")
        runway_txt = f"{ic['Runway (meses)']:.1f} meses" if np.isfinite(ic["Runway (meses)"]) else "sem queima de caixa"
        c3.metric("Runway", runway_txt)

        evo_caixa = evolucao_caixa(df_caixa_pais)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo_caixa["Data"], y=evo_caixa["Entradas"], name="Entradas", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo_caixa["Data"], y=-evo_caixa["Saídas"], name="Saídas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo_caixa["Data"], y=evo_caixa["Saldo Final"], name="Saldo Final", line=dict(color=COR_FUNDO, width=2.5), yaxis="y2"))
        fig.update_layout(
            barmode="relative", height=340, legend=dict(orientation="h"),
            yaxis=dict(title="Entradas / Saídas"),
            yaxis2=dict(title="Saldo Final", overlaying="y", side="right"),
        )
        st.plotly_chart(fig, use_container_width=True)

st.caption(
    "⚠️ A coluna **Squad** da aba Caixa mensal só contém um valor fixo (\"Saldo Final\") em "
    "100% das linhas — não representa uma segmentação real por equipe/projeto, então não é "
    "possível montar o indicador de \"Resultado por Squad\" com o dado disponível hoje."
)

st.divider()

# --------------------------------------------------------------------------
# Evolução mensal — Receita x Custos/Despesas x Resultado
# --------------------------------------------------------------------------
st.subheader("Evolução Mensal")

col_br, col_us = st.columns(2)
for col, df_pais, titulo, simbolo in [
    (col_br, df_br, "Brasil", "R$"),
    (col_us, df_us, "EUA", "US$"),
]:
    with col:
        evo = evolucao_mensal(df_pais)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=evo.get("Receita", 0), name="Receita", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=-evo.get("Custos e Despesas", 0), name="Custos e Despesas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo["AnoMes"], y=evo["Resultado Operacional"], name="Resultado", line=dict(color=COR_FUNDO, width=3)))
        fig.update_layout(title=f"{titulo} — {simbolo}", barmode="relative", legend=dict(orientation="h"), height=380)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Composição de custos e despesas por grupo
# --------------------------------------------------------------------------
st.subheader("Composição de Custos e Despesas")

col_br, col_us = st.columns(2)
for col, df_pais, titulo in [(col_br, df_br, "Brasil"), (col_us, df_us, "EUA")]:
    with col:
        comp = composicao_por_grupo(df_pais)
        fig = px.bar(
            comp, x="Valor pago", y="Grupo DRE", orientation="h",
            color_discrete_sequence=[COR_DESTAQUE], title=titulo,
        )
        fig.update_layout(height=350, yaxis_title="", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --------------------------------------------------------------------------
# Tabela detalhada
# --------------------------------------------------------------------------
st.subheader("Detalhamento")
pais_tab = st.radio("Ver detalhamento de:", ["Brasil", "EUA"], horizontal=True)
df_detalhe = df_br if pais_tab == "Brasil" else df_us

tabela = (
    df_detalhe.groupby(["Grupo DRE", "Categoria"], as_index=False)[["Valor recebido", "Valor pago"]]
    .sum()
    .sort_values("Valor pago", ascending=False)
)
st.dataframe(tabela, use_container_width=True, height=350)
