"""
Dashboard DRE — SG Global Group
V2: foco em UX, responsividade, leitura executiva e exploração dos dados.
Rodar com: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from etl import (
    load_all,
    kpis,
    evolucao_mensal,
    composicao_por_grupo,
    load_all_caixa,
    kpis_avancados,
    tem_fluxo_de_caixa_real,
    indicadores_caixa,
    evolucao_caixa,
    ultima_data_com_movimento,
)

COR_DESTAQUE = "#FF4800"
COR_FUNDO = "#0F0F24"
COR_NEUTRA = "#777777"
COR_POSITIVA = "#16803A"
COR_NEGATIVA = "#B42318"

st.set_page_config(
    page_title="DRE • SG Global Group",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .stApp {{ background: #F7F8FA; }}
    .block-container {{ max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem; }}
    h1, h2, h3 {{ color: {COR_FUNDO}; }}
    [data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid #E6E8EC;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(15,15,36,.04);
    }}
    [data-testid="stMetricLabel"] {{ color: {COR_NEUTRA} !important; font-weight: 600; }}
    [data-testid="stMetricValue"] {{ color: {COR_FUNDO} !important; font-size: clamp(1.2rem, 2vw, 1.8rem); }}
    .hero {{
        background: linear-gradient(135deg, #0F0F24 0%, #1B1B38 100%);
        color: white; padding: 24px; border-radius: 16px; margin-bottom: 18px;
    }}
    .hero h1 {{ color: white; margin-bottom: 4px; }}
    .hero p {{ color: #D8D9E2; margin: 0; }}
    .insight {{
        background: #FFF7F2; border-left: 4px solid #FF4800;
        padding: 14px 16px; border-radius: 8px; margin: 10px 0 18px;
    }}
    .section-note {{ color: #666; font-size: .92rem; margin-top: -8px; margin-bottom: 12px; }}
    @media (max-width: 768px) {{
        .block-container {{ padding: 0.8rem 0.7rem 2rem; }}
        .hero {{ padding: 18px; border-radius: 12px; }}
        .hero h1 {{ font-size: 1.55rem; }}
        [data-testid="stMetric"] {{ padding: 10px 12px; }}
        [data-testid="stMetricValue"] {{ font-size: 1.2rem; }}
        .stPlotlyChart {{ width: 100% !important; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>📊 Dashboard Financeiro — SG Global Group</h1>
      <p>DRE, performance e fluxo de caixa para apoiar decisões executivas — Brasil e EUA.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Carregando e limpando as bases...")
def carregar_dados(path_br, path_us):
    return load_all(path_br, path_us)


@st.cache_data(show_spinner="Carregando fluxo de caixa...")
def carregar_caixa(path_br, path_us):
    return load_all_caixa(path_br, path_us)


def pct_change(current, previous):
    if previous is None or pd.isna(previous) or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def format_money(value, symbol):
    if pd.isna(value):
        return "—"
    value = float(value)
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{symbol} {value / 1_000_000:,.1f}M"
    if abs_value >= 1_000:
        return f"{symbol} {value / 1_000:,.0f}K"
    return f"{symbol} {value:,.0f}"


def insight_text(df_pais, titulo):
    k = kpis(df_pais)
    receita = k.get("Receita", np.nan)
    resultado = k.get("Resultado Operacional", np.nan)
    margem = k.get("Margem %", np.nan)
    if pd.isna(receita) or pd.isna(resultado):
        return f"{titulo}: não há dados suficientes para gerar o resumo executivo."
    margem_txt = f"{margem * 100:.1f}%" if pd.notna(margem) else "não disponível"
    sinal = "positivo" if resultado >= 0 else "negativo"
    return (
        f"<strong>{titulo}</strong>: receita de {format_money(receita, 'R$' if titulo == 'Brasil' else 'US$')}, "
        f"resultado operacional de {format_money(resultado, 'R$' if titulo == 'Brasil' else 'US$')} "
        f"e margem de {margem_txt}. O resultado atual é <strong>{sinal}</strong>."
    )


# --------------------------------------------------------------------------
# Sidebar: fonte + filtros, com menos ruído visual
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Controles")
    modo = st.radio(
        "Fonte de dados",
        ["Arquivos padrão", "Enviar manualmente"],
        help="Use os arquivos em ./data ou envie duas bases Excel.",
    )
    if modo == "Enviar manualmente":
        up_br = st.file_uploader("DRE Brasil (.xlsx)", type="xlsx")
        up_us = st.file_uploader("DRE EUA (.xlsx)", type="xlsx")
        path_br, path_us = up_br, up_us
    else:
        path_br, path_us = "data/DRE_BR_DNC.xlsx", "data/DRE_US_DNC.xlsx"

if not path_br or not path_us:
    st.info("Envie os dois arquivos para iniciar a análise.")
    st.stop()

dados = carregar_dados(path_br, path_us)
df_br_full, df_us_full = dados["BRL"], dados["USD"]
caixa = carregar_caixa(path_br, path_us)
caixa_br_full, caixa_us_full = caixa["BRL"], caixa["USD"]

with st.sidebar:
    st.subheader("Filtros")
    empresas_br = sorted(df_br_full["Empresa"].dropna().unique())
    empresas_us = sorted(df_us_full["Empresa"].dropna().unique())
    sel_empresas_br = st.multiselect("Empresas — Brasil", empresas_br, default=empresas_br)
    sel_empresas_us = st.multiselect("Empresas — EUA", empresas_us, default=empresas_us)

    data_min = min(df_br_full["Data de Competência"].min(), df_us_full["Data de Competência"].min())
    data_max = max(df_br_full["Data de Competência"].max(), df_us_full["Data de Competência"].max())
    periodo = st.slider(
        "Período de competência",
        min_value=data_min.to_pydatetime(),
        max_value=data_max.to_pydatetime(),
        value=(data_min.to_pydatetime(), data_max.to_pydatetime()),
        format="MM/YYYY",
    )
    st.caption("💡 Dica: no celular, use um mercado por vez para reduzir a rolagem.")


df_br = df_br_full[
    df_br_full["Empresa"].isin(sel_empresas_br)
    & df_br_full["Data de Competência"].between(periodo[0], periodo[1])
]
df_us = df_us_full[
    df_us_full["Empresa"].isin(sel_empresas_us)
    & df_us_full["Data de Competência"].between(periodo[0], periodo[1])
]
caixa_br = caixa_br_full[caixa_br_full["Data"].between(periodo[0], periodo[1])]
caixa_us = caixa_us_full[caixa_us_full["Data"].between(periodo[0], periodo[1])]

# --------------------------------------------------------------------------
# Navegação principal: reduz a página vertical e cria um fluxo executivo.
# --------------------------------------------------------------------------
tab_geral, tab_dre, tab_caixa, tab_detalhe = st.tabs(
    ["📊 Visão Geral", "💰 DRE & Performance", "💵 Fluxo de Caixa", "🔎 Detalhamento"]
)

with tab_geral:
    st.subheader("Resumo Executivo")
    st.markdown(
        "<div class='section-note'>Comece pelos indicadores. Use as demais abas para investigar os principais movimentos.</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    for col, df_pais, titulo, simbolo in [
        (c1, df_br, "Brasil", "R$"),
        (c2, df_us, "EUA", "US$"),
    ]:
        with col:
            st.markdown(f"### 🇧🇷 {titulo}" if titulo == "Brasil" else f"### 🇺🇸 {titulo}")
            k = kpis(df_pais)
            a, b = st.columns(2)
            a.metric("Receita", format_money(k["Receita"], simbolo))
            b.metric("Resultado Operacional", format_money(k["Resultado Operacional"], simbolo))
            a, b = st.columns(2)
            total_custos = k["Custos Variáveis e Fixos"] + k["Despesas"]
            a.metric("Custos + Despesas", format_money(total_custos, simbolo))
            margem = k["Margem %"] * 100 if pd.notna(k["Margem %"]) else np.nan
            b.metric("Margem", f"{margem:.1f}%" if pd.notna(margem) else "—")

    st.markdown(
        f"<div class='insight'>💡 {insight_text(df_br, 'Brasil')}<br>{insight_text(df_us, 'EUA')}</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Comparação de Performance")
    comp_df = pd.DataFrame(
        {
            "Indicador": ["Receita", "Resultado Operacional", "Custos + Despesas"],
            "Brasil": [kpis(df_br)["Receita"], kpis(df_br)["Resultado Operacional"], kpis(df_br)["Custos Variáveis e Fixos"] + kpis(df_br)["Despesas"]],
            "EUA": [kpis(df_us)["Receita"], kpis(df_us)["Resultado Operacional"], kpis(df_us)["Custos Variáveis e Fixos"] + kpis(df_us)["Despesas"]],
        }
    )
    fig = px.bar(comp_df, x="Indicador", y=["Brasil", "EUA"], barmode="group", height=360)
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

with tab_dre:
    st.subheader("Indicadores de Resultado e DRE")
    st.markdown(
        "<div class='section-note'>Receita, margem, contribuição e EBITDA aproximado para leitura financeira.</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "EBITDA é uma aproximação operacional (Receita Líquida − Custos − Despesas), pois a base não traz uma linha separada de depreciação/amortização."
    )

    for df_pais, titulo, simbolo in [(df_br, "Brasil", "R$"), (df_us, "EUA", "US$")]:
        st.markdown(f"### {'🇧🇷' if titulo == 'Brasil' else '🇺🇸'} {titulo}")
        ka = kpis_avancados(df_pais)
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Bruta", format_money(ka["Receita Bruta"], simbolo))
        c2.metric("Receita Líquida", format_money(ka["Receita Líquida"], simbolo))
        c3.metric("Margem de Contribuição", f"{ka['Margem de Contribuição %'] * 100:.1f}%" if pd.notna(ka["Margem de Contribuição %"]) else "—")
        c1, c2 = st.columns(2)
        c1.metric("EBITDA (aprox.)", format_money(ka["EBITDA (aprox.)"], simbolo))
        c2.metric("Margem Líquida", f"{ka['Margem Líquida %'] * 100:.1f}%" if pd.notna(ka["Margem Líquida %"]) else "—")

        evo = evolucao_mensal(df_pais)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=evo.get("Receita", 0), name="Receita", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=-evo.get("Custos e Despesas", 0), name="Custos + Despesas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo["AnoMes"], y=evo["Resultado Operacional"], name="Resultado", line=dict(color=COR_FUNDO, width=3)))
        fig.update_layout(
            title=f"{titulo} — Evolução Mensal",
            barmode="relative",
            height=390,
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    st.subheader("Composição de Custos e Despesas")
    c1, c2 = st.columns(2)
    for col, df_pais, titulo, simbolo in [(c1, df_br, "Brasil", "R$"), (c2, df_us, "EUA", "US$")]:
        with col:
            comp = composicao_por_grupo(df_pais).copy()
            total = comp["Valor pago"].sum()
            comp["Participação"] = comp["Valor pago"] / total * 100 if total else 0
            fig = px.bar(comp, x="Valor pago", y="Grupo DRE", orientation="h", text="Participação", height=350)
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(title=titulo, xaxis_title="Valor", yaxis_title="", margin=dict(l=10, r=25, t=45, b=10))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

with tab_caixa:
    st.subheader("Fluxo de Caixa")
    st.markdown(
        "<div class='section-note'>Indicadores de liquidez e movimentação. Valores devem ser interpretados conforme a qualidade da base.</div>",
        unsafe_allow_html=True,
    )
    for df_caixa_pais, titulo, simbolo in [(caixa_br, "Brasil", "R$"), (caixa_us, "EUA", "US$")]:
        st.markdown(f"### {'🇧🇷' if titulo == 'Brasil' else '🇺🇸'} {titulo}")
        if not tem_fluxo_de_caixa_real(df_caixa_pais):
            st.warning(
                "A base não possui Entradas/Saídas reais suficientes para calcular Burn Rate e Runway com confiabilidade. "
                "Solicite à empresa a movimentação de caixa real."
            )
            continue

        ic = indicadores_caixa(df_caixa_pais)
        ultima_mov = ultima_data_com_movimento(df_caixa_pais)
        if ultima_mov is not None:
            st.caption(f"Última movimentação real: {ultima_mov.strftime('%m/%Y')}. Meses posteriores podem apenas repetir o saldo.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Atual", format_money(ic["Saldo Atual"], simbolo))
        c2.metric("Burn Rate Médio", f"{format_money(ic['Burn Rate Médio'], simbolo)}/mês")
        runway = ic["Runway (meses)"]
        c3.metric("Runway", f"{runway:.1f} meses" if np.isfinite(runway) else "Sem queima de caixa")

        evo_caixa = evolucao_caixa(df_caixa_pais)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo_caixa["Data"], y=evo_caixa["Entradas"], name="Entradas", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo_caixa["Data"], y=-evo_caixa["Saídas"], name="Saídas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo_caixa["Data"], y=evo_caixa["Saldo Final"], name="Saldo Final", line=dict(color=COR_FUNDO, width=2.5), yaxis="y2"))
        fig.update_layout(
            title=f"{titulo} — Movimentação de Caixa",
            barmode="relative",
            height=360,
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h"),
            yaxis=dict(title="Entradas / Saídas"),
            yaxis2=dict(title="Saldo", overlaying="y", side="right"),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    st.info(
        "⚠️ A coluna **Squad** da aba Caixa mensal não representa uma segmentação real por equipe/projeto. "
        "Por isso, o dashboard não apresenta Resultado por Squad como se fosse um indicador confiável."
    )

with tab_detalhe:
    st.subheader("🔎 Exploração dos Dados")
    st.markdown(
        "<div class='section-note'>Use os filtros abaixo para investigar grupos e categorias sem sair do contexto do dashboard.</div>",
        unsafe_allow_html=True,
    )
    pais_tab = st.radio("Mercado", ["Brasil", "EUA"], horizontal=True)
    df_detalhe = df_br if pais_tab == "Brasil" else df_us

    grupos = ["Todos"] + sorted(df_detalhe["Grupo DRE"].dropna().unique().tolist())
    categorias = ["Todas"] + sorted(df_detalhe["Categoria"].dropna().unique().tolist())
    c1, c2, c3 = st.columns(3)
    grupo_sel = c1.selectbox("Grupo DRE", grupos)
    categoria_sel = c2.selectbox("Categoria", categorias)
    ordem = c3.selectbox("Ordenar por", ["Valor pago", "Valor recebido"])

    filtrado = df_detalhe.copy()
    if grupo_sel != "Todos":
        filtrado = filtrado[filtrado["Grupo DRE"] == grupo_sel]
    if categoria_sel != "Todas":
        filtrado = filtrado[filtrado["Categoria"] == categoria_sel]

    tabela = (
        filtrado.groupby(["Grupo DRE", "Categoria"], as_index=False)[["Valor recebido", "Valor pago"]]
        .sum()
        .sort_values(ordem, ascending=False)
    )
    total_pago = tabela["Valor pago"].sum()
    tabela["% do total pago"] = tabela["Valor pago"] / total_pago * 100 if total_pago else 0
    st.dataframe(
        tabela,
        use_container_width=True,
        height=430,
        hide_index=True,
        column_config={
            "Valor recebido": st.column_config.NumberColumn(format="%.2f"),
            "Valor pago": st.column_config.NumberColumn(format="%.2f"),
            "% do total pago": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

    st.caption(f"{len(tabela):,} combinações de grupo/categoria após os filtros selecionados.")
