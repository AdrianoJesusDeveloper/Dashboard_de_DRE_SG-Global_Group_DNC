"""Dashboard financeiro da SG Global Group."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import MERCADOS, config_pais
from etl import (
    composicao_por_grupo,
    evolucao_caixa,
    evolucao_mensal,
    indicadores_caixa,
    kpis,
    kpis_avancados,
    load_all,
    load_all_caixa,
    tem_fluxo_de_caixa_real,
    ultima_data_com_movimento,
)

COR_DESTAQUE = "#FF4800"
COR_FUNDO = "#0F0F24"
COR_NEUTRA = "#777777"

st.set_page_config(page_title="DRE • SG Global Group", layout="wide", page_icon="📊")

st.markdown(f"""
<style>
.stApp {{ background:#F7F8FA; }}
.block-container {{ max-width:1500px; padding-top:1.2rem; padding-bottom:3rem; }}
h1,h2,h3 {{ color:{COR_FUNDO}; }}
[data-testid="stMetric"] {{ background:#FFF; border:1px solid #E6E8EC; border-radius:12px; padding:14px 16px; box-shadow:0 1px 2px rgba(15,15,36,.04); }}
[data-testid="stMetricLabel"] {{ color:{COR_NEUTRA} !important; font-weight:600; }}
[data-testid="stMetricValue"] {{ color:{COR_FUNDO} !important; font-size:clamp(1.2rem,2vw,1.8rem); }}
.hero {{ background:linear-gradient(135deg,#0F0F24 0%,#1B1B38 100%); color:white; padding:24px; border-radius:16px; margin-bottom:18px; }}
.hero h1 {{ color:white; margin-bottom:4px; }} .hero p {{ color:#D8D9E2; margin:0; }}
.insight {{ background:#FFF7F2; border-left:4px solid #FF4800; padding:14px 16px; border-radius:8px; margin:10px 0 18px; }}
.section-note {{ color:#666; font-size:.92rem; margin-top:-8px; margin-bottom:12px; }}
@media (max-width:768px) {{ .block-container {{ padding:.8rem .7rem 2rem; }} .hero {{ padding:18px; border-radius:12px; }} .hero h1 {{ font-size:1.5rem; }} [data-testid="stMetric"] {{ padding:10px 12px; }} [data-testid="stMetricValue"] {{ font-size:1.15rem; }} .stPlotlyChart {{ width:100% !important; }} }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>📊 Dashboard Financeiro — SG Global Group</h1>
<p>DRE, performance e fluxo de caixa para apoiar decisões executivas — Brasil e EUA.</p>
</div>
""", unsafe_allow_html=True)


def format_money(value, symbol):
    if value is None or pd.isna(value):
        return "—"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"{symbol} {value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"{symbol} {value / 1_000:,.0f}K"
    return f"{symbol} {value:,.0f}"


def mercado_label(nome):
    cfg = config_pais(nome)
    return f"{cfg['emoji']} {nome}"


def insight_text(df, nome, k):
    cfg = config_pais(nome)
    receita = k["Receita Líquida"]
    resultado = k["Resultado Operacional"]
    margem = k["Margem %"]
    if pd.isna(receita) or pd.isna(resultado):
        return f"<strong>{nome}</strong>: não há dados suficientes para gerar o resumo executivo."
    margem_txt = f"{margem * 100:.1f}%" if pd.notna(margem) else "não disponível"
    sinal = "positivo" if resultado >= 0 else "negativo"
    return (f"<strong>{nome}</strong>: receita líquida de {format_money(receita, cfg['moeda'])}, "
            f"resultado operacional de {format_money(resultado, cfg['moeda'])} e margem de {margem_txt}. "
            f"O resultado atual é <strong>{sinal}</strong>.")


@st.cache_data(show_spinner="Carregando e limpando as bases...")
def carregar_dados(path_br, path_us):
    return load_all(path_br, path_us)


@st.cache_data(show_spinner="Carregando fluxo de caixa...")
def carregar_caixa(path_br, path_us):
    return load_all_caixa(path_br, path_us)


with st.sidebar:
    st.header("🎛️ Controles")
    modo = st.radio("Fonte de dados", ["Arquivos padrão", "Enviar manualmente"],
                    help="Use os arquivos em ./data ou envie duas bases Excel.")
    if modo == "Enviar manualmente":
        path_br = st.file_uploader("DRE Brasil (.xlsx)", type="xlsx")
        path_us = st.file_uploader("DRE EUA (.xlsx)", type="xlsx")
    else:
        path_br, path_us = "data/DRE_BR_DNC.xlsx", "data/DRE_US_DNC.xlsx"

if not path_br or not path_us:
    st.info("Envie os dois arquivos para iniciar a análise.")
    st.stop()

dados = carregar_dados(path_br, path_us)
caixa = carregar_caixa(path_br, path_us)
dfs = {"Brasil": dados["BRL"], "EUA": dados["USD"]}
dfs_caixa = {"Brasil": caixa["BRL"], "EUA": caixa["USD"]}

with st.sidebar:
    st.subheader("Filtros")
    empresas = {}
    selecionadas = {}
    for nome in MERCADOS:
        empresas[nome] = sorted(dfs[nome]["Empresa"].dropna().unique().tolist())
        selecionadas[nome] = st.multiselect(
            f"Empresas — {nome}", empresas[nome], default=empresas[nome], key=f"emp_{nome}"
        )

    data_min = min(df["Data de Competência"].min() for df in dfs.values())
    data_max = max(df["Data de Competência"].max() for df in dfs.values())
    periodo = st.slider(
        "Período de competência", min_value=data_min.to_pydatetime(), max_value=data_max.to_pydatetime(),
        value=(data_min.to_pydatetime(), data_max.to_pydatetime()), format="MM/YYYY"
    )
    st.caption("💡 No celular, selecione um mercado por vez para reduzir a rolagem.")

filtros = {}
for nome in MERCADOS:
    filtros[nome] = dfs[nome][
        dfs[nome]["Empresa"].isin(selecionadas[nome])
        & dfs[nome]["Data de Competência"].between(periodo[0], periodo[1])
    ]

filtros_caixa = {
    nome: dfs_caixa[nome][dfs_caixa[nome]["Data"].between(periodo[0], periodo[1])]
    for nome in MERCADOS
}

kpis_atuais = {nome: kpis(filtros[nome]) for nome in MERCADOS}

# Comparações monetárias entre moedas diferentes foram removidas: a visão geral
# compara margens e tendências, enquanto os valores permanecem separados por moeda.
tab_geral, tab_dre, tab_caixa, tab_detalhe = st.tabs(
    ["📊 Visão Geral", "💰 DRE & Performance", "💵 Fluxo de Caixa", "🔎 Detalhamento"]
)

with tab_geral:
    st.subheader("Resumo Executivo")
    st.markdown("<div class='section-note'>Indicadores por mercado. Valores monetários não são somados entre moedas.</div>", unsafe_allow_html=True)

    cols = st.columns(2)
    for col, nome in zip(cols, MERCADOS):
        cfg = config_pais(nome)
        k = kpis_atuais[nome]
        with col:
            st.markdown(f"### {mercado_label(nome)}")
            a, b = st.columns(2)
            a.metric("Receita Líquida", format_money(k["Receita Líquida"], cfg["moeda"]))
            b.metric("Resultado Operacional", format_money(k["Resultado Operacional"], cfg["moeda"]))
            a, b = st.columns(2)
            total = k["Custos Variáveis e Fixos"] + k["Despesas"]
            a.metric("Custos + Despesas", format_money(total, cfg["moeda"]))
            margem = k["Margem %"] * 100 if pd.notna(k["Margem %"]) else np.nan
            b.metric("Margem Operacional", f"{margem:.1f}%" if pd.notna(margem) else "—")

    st.markdown(
        f"<div class='insight'>💡 {insight_text(filtros['Brasil'], 'Brasil', kpis_atuais['Brasil'])}<br>"
        f"{insight_text(filtros['EUA'], 'EUA', kpis_atuais['EUA'])}</div>", unsafe_allow_html=True)

    st.subheader("Comparação Estrutural")
    comparacao = pd.DataFrame({
        "Indicador": ["Margem Operacional", "Margem Líquida"],
        "Brasil": [kpis_atuais["Brasil"]["Margem %"] * 100, kpis_atuais["Brasil"]["Margem Líquida %"] * 100],
        "EUA": [kpis_atuais["EUA"]["Margem %"] * 100, kpis_atuais["EUA"]["Margem Líquida %"] * 100],
    })
    fig = px.bar(comparacao, x="Indicador", y=["Brasil", "EUA"], barmode="group", height=330,
                 labels={"value": "%", "variable": "Mercado"})
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), legend=dict(orientation="h"), yaxis_title="Percentual")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    st.caption("Comparação em percentuais: Brasil e EUA permanecem em suas respectivas moedas e não são convertidos.")

with tab_dre:
    st.subheader("Indicadores de Resultado e DRE")
    st.markdown("<div class='section-note'>Receita, margem, contribuição e resultado operacional com premissas explícitas.</div>", unsafe_allow_html=True)
    st.caption("O indicador 'EBITDA (proxy)' é uma aproximação operacional; a base não permite calcular EBITDA contábil estrito porque não separa depreciação e amortização.")

    for nome in MERCADOS:
        cfg = config_pais(nome)
        df = filtros[nome]
        ka = kpis_avancados(df)
        st.markdown(f"### {mercado_label(nome)}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Bruta", format_money(ka["Receita Bruta"], cfg["moeda"]))
        c2.metric("Receita Líquida", format_money(ka["Receita Líquida"], cfg["moeda"]))
        c3.metric("Margem de Contribuição", f"{ka['Margem de Contribuição %'] * 100:.1f}%" if pd.notna(ka["Margem de Contribuição %"]) else "—")
        c1, c2 = st.columns(2)
        c1.metric("EBITDA (proxy)", format_money(ka["EBITDA (proxy)"], cfg["moeda"]))
        c2.metric("Resultado Líquido", format_money(ka["Resultado Líquido"], cfg["moeda"]))

        evo = evolucao_mensal(df)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=evo.get("Receita Líquida", 0), name="Receita Líquida", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo["AnoMes"], y=-evo.get("Custos e Despesas", 0), name="Custos + Despesas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo["AnoMes"], y=evo["Resultado Operacional"], name="Resultado Operacional", line=dict(color=COR_FUNDO, width=3)))
        fig.update_layout(title=f"{nome} — Evolução Mensal", barmode="relative", height=390,
                          margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h"), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    st.subheader("Composição de Custos e Despesas")
    cols = st.columns(2)
    for col, nome in zip(cols, MERCADOS):
        with col:
            comp = composicao_por_grupo(filtros[nome]).copy()
            total = comp["Valor pago"].sum()
            comp["Participação"] = comp["Valor pago"] / total * 100 if total else 0
            fig = px.bar(comp, x="Valor pago", y="Grupo DRE", orientation="h", text="Participação", height=350)
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(title=nome, xaxis_title=f"Valor ({config_pais(nome)['moeda']})", yaxis_title="", margin=dict(l=10, r=25, t=45, b=10))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})

with tab_caixa:
    st.subheader("Fluxo de Caixa")
    st.markdown("<div class='section-note'>Liquidez e movimentação por mercado. Indicadores só são exibidos quando há movimentação real.</div>", unsafe_allow_html=True)
    for nome in MERCADOS:
        cfg = config_pais(nome)
        df_caixa = filtros_caixa[nome]
        st.markdown(f"### {mercado_label(nome)}")
        if not tem_fluxo_de_caixa_real(df_caixa):
            st.warning("A base não possui Entradas/Saídas reais suficientes para calcular Burn Rate e Runway com confiabilidade.")
            continue
        ic = indicadores_caixa(df_caixa)
        ultima_mov = ultima_data_com_movimento(df_caixa)
        if ultima_mov is not None:
            st.caption(f"Última movimentação real: {ultima_mov.strftime('%m/%Y')}. Meses posteriores podem apenas repetir o saldo.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Atual", format_money(ic["Saldo Atual"], cfg["moeda"]))
        c2.metric("Burn Rate Médio", f"{format_money(ic['Burn Rate Médio'], cfg['moeda'])}/mês")
        c3.metric("Runway", f"{ic['Runway (meses)']:.1f} meses" if np.isfinite(ic["Runway (meses)"]) else "Sem queima de caixa")
        evo = evolucao_caixa(df_caixa)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=evo["Data"], y=evo["Entradas"], name="Entradas", marker_color=COR_DESTAQUE))
        fig.add_trace(go.Bar(x=evo["Data"], y=-evo["Saídas"], name="Saídas", marker_color=COR_NEUTRA))
        fig.add_trace(go.Scatter(x=evo["Data"], y=evo["Saldo Final"], name="Saldo Final", line=dict(color=COR_FUNDO, width=2.5), yaxis="y2"))
        fig.update_layout(title=f"{nome} — Movimentação de Caixa", barmode="relative", height=360,
                          margin=dict(l=10, r=10, t=50, b=10), legend=dict(orientation="h"),
                          yaxis=dict(title=f"Entradas / Saídas ({cfg['moeda']})"), yaxis2=dict(title=f"Saldo ({cfg['moeda']})", overlaying="y", side="right"), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    st.info("⚠️ A coluna Squad da aba Caixa mensal não representa uma segmentação real por equipe/projeto; por isso não é usada como indicador de resultado.")

with tab_detalhe:
    st.subheader("🔎 Exploração dos Dados")
    st.markdown("<div class='section-note'>Investigue grupos e categorias sem sair do contexto do dashboard.</div>", unsafe_allow_html=True)
    nome = st.radio("Mercado", list(MERCADOS), horizontal=True)
    df = filtros[nome]
    grupos = ["Todos"] + sorted(df["Grupo DRE"].dropna().unique().tolist())
    categorias = ["Todas"] + sorted(df["Categoria"].dropna().unique().tolist())
    c1, c2, c3 = st.columns(3)
    grupo_sel = c1.selectbox("Grupo DRE", grupos)
    categoria_sel = c2.selectbox("Categoria", categorias)
    ordem = c3.selectbox("Ordenar por", ["Valor pago", "Valor recebido"])
    filtrado = df.copy()
    if grupo_sel != "Todos": filtrado = filtrado[filtrado["Grupo DRE"] == grupo_sel]
    if categoria_sel != "Todas": filtrado = filtrado[filtrado["Categoria"] == categoria_sel]
    tabela = (filtrado.groupby(["Grupo DRE", "Categoria"], as_index=False)[["Valor recebido", "Valor pago"]]
              .sum().sort_values(ordem, ascending=False))
    total_pago = tabela["Valor pago"].sum()
    tabela["% do total pago"] = tabela["Valor pago"] / total_pago * 100 if total_pago else 0
    st.dataframe(tabela, use_container_width=True, height=430, hide_index=True,
                 column_config={"Valor recebido": st.column_config.NumberColumn(format="%.2f"),
                                "Valor pago": st.column_config.NumberColumn(format="%.2f"),
                                "% do total pago": st.column_config.NumberColumn(format="%.1f%%")})
    st.caption(f"{len(tabela):,} combinações de grupo/categoria após os filtros selecionados.")
