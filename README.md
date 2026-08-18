<div align="center">

<img src="docs/screenshots/banner.png" alt="Dashboard DRE — SG Global Group" width="100%" />

<br/>

# 📊 Dashboard DRE · SG Global Group

### **Inteligência Financeira para Decisão**

**Brasil** · **EUA**

Transformando dados financeiros brutos em indicadores claros, comparáveis e acionáveis.

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-111827?style=for-the-badge&logo=python&logoColor=3776AB)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-111827?style=for-the-badge&logo=pandas&logoColor=150458)](https://pandas.pydata.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=FFFFFF)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualization-111827?style=for-the-badge&logo=plotly&logoColor=3F4F75)](https://plotly.com/python/)
[![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-F59E0B?style=for-the-badge)]()

<br/>

**Projeto I · Escola de Dados · DNC**

</div>

---

## 🎯 Visão executiva

O **Dashboard DRE — SG Global Group** é uma solução de análise financeira desenvolvida para transformar duas bases de dados — **Brasil** e **EUA** — em uma visão executiva da **Demonstração do Resultado do Exercício (DRE)** e do **Fluxo de Caixa**.

A aplicação combina **ETL, tratamento de dados, regras de negócio, indicadores financeiros e visualização interativa** em uma única experiência analítica.

> **Objetivo:** reduzir a distância entre o dado bruto e a decisão gerencial.

### Mercados oficiais da interface

| Mercado | Moeda | Uso na análise |
|:---:|:---:|:---|
| **Brasil** | **R$** | Operação brasileira |
| **EUA** | **US$** | Operação americana |

**Nomenclatura oficial:** em toda a interface e documentação do projeto, os mercados devem ser apresentados exclusivamente como **Brasil** e **EUA**.

**Importante:** a aplicação preserva as moedas originais. Não existe conversão cambial automática. Por isso, comparações entre os mercados priorizam **margens, crescimento e indicadores relativos**, evitando comparar valores nominais em moedas diferentes como se fossem equivalentes.

---

## 🖼 Prévia do dashboard

<details open>
<summary><strong>Visão Geral</strong> — KPIs, evolução mensal e detalhamento, Brasil e EUA lado a lado</summary>
<br/>

<img src="docs/screenshots/visao_geral_mockup.png" alt="Prévia da Visão Geral do dashboard" width="100%" />

<sub>⚠️ Esta imagem é um <strong>mock-up gerado a partir dos dados reais e dos mesmos cálculos do dashboard</strong> — não é um print literal da tela do Streamlit.</sub>

</details>

<br/>

<table>
<tr>
<td width="50%">

**Evolução Mensal — Brasil**

<img src="docs/screenshots/evolucao_brasil.png" alt="Evolução Mensal — Brasil" width="100%" />

</td>
<td width="50%">

**Evolução Mensal — EUA**

<img src="docs/screenshots/evolucao_eua.png" alt="Evolução Mensal — EUA" width="100%" />

</td>
</tr>
<tr>
<td width="50%">

**Composição de Custos — Brasil**

<img src="docs/screenshots/composicao_brasil.png" alt="Composição de Custos — Brasil" width="100%" />

</td>
<td width="50%">

**Composição de Custos — EUA**

<img src="docs/screenshots/composicao_eua.png" alt="Composição de Custos — EUA" width="100%" />

</td>
</tr>
</table>

<details>
<summary>💵 Ver também: <strong>Fluxo de Caixa Mensal — EUA</strong></summary>
<br/>

<img src="docs/screenshots/fluxo_caixa_eua.png" alt="Fluxo de Caixa Mensal — EUA" width="100%" />

<sub>O Brasil não aparece aqui porque a aba <code>Caixa mensal</code> dessa base não tem movimentação real registrada.</sub>

</details>

<br/>

## ✨ Funcionalidades

| | |
|---|---|
| 🌎 **Brasil + EUA lado a lado** | Duas bases, duas moedas (R$ / US$), sem conversão forçada — comparação estrutural, não nominal |
| 💰 **KPIs de DRE** | Receita, Custos, Despesas, Impostos, Resultado Operacional e Margem |
| 📈 **Indicadores avançados** | Receita Bruta/Líquida, Margem de Contribuição, EBITDA (proxy), Margem Líquida |
| 🏦 **Fluxo de Caixa** | Saldo Atual, Burn Rate médio e Runway, com gráfico de Entradas × Saídas × Saldo |
| 🧭 **Filtros dinâmicos** | Empresa e período de competência, aplicados aos gráficos |
| 🔍 **Detalhamento** | Tabela navegável por Grupo DRE e Categoria |
| ⚠️ **Transparência de dados** | O app sinaliza quando um indicador não pode ser calculado com confiança |

---

## 🧠 Diferencial técnico

Este projeto não foi construído apenas para **"mostrar gráficos"**. A arquitetura representa o ciclo completo de uma solução analítica:

```text
             DADOS BRUTOS
                  │
       ┌──────────┴──────────┐
       │                     │
     Brasil                  EUA
       │                     │
       └──────────┬──────────┘
                  ▼
             🧹 ETL
        Limpeza + Padronização
                  │
                  ▼
          🧩 Modelo Analítico
       Grupo DRE + Dimensões
                  │
                  ▼
          🧮 Business Metrics
       KPIs + Margens + Caixa
                  │
                  ▼
          📊 VISUALIZAÇÃO
         Streamlit + Plotly
                  │
                  ▼
          🎯 DECISÃO GERENCIAL
```

---

## 🏗 Arquitetura

```mermaid
flowchart TB
    BR["DRE Brasil\nDRE_BR_DNC.xlsx"]
    US["DRE EUA\nDRE_US_DNC.xlsx"]
    CBR["Caixa Brasil"]
    CUS["Caixa EUA"]
    ETL["🧹 ETL & Data Preparation\netl.py"]
    CFG["⚙️ Configuration\nconfig.py"]
    MODEL["🧩 Modelo Analítico\nDRE + Caixa + Dimensões"]
    KPI["🧮 Business Metrics\nKPIs + Margens + Indicadores"]
    APP["📊 Streamlit App\napp.py"]
    BR --> ETL
    US --> ETL
    CBR --> ETL
    CUS --> ETL
    ETL --> MODEL
    MODEL --> KPI
    CFG --> APP
    KPI --> APP
    APP --> V1["Visão Geral"]
    APP --> V2["DRE & Performance"]
    APP --> V3["Fluxo de Caixa"]
    APP --> V4["Detalhamento"]
```

### 🧱 Camadas do projeto

#### `etl.py` · Dados & regras de negócio

Responsável por leitura, limpeza, padronização, taxonomia DRE, dimensões temporais, KPIs e preparação do fluxo de caixa.

#### `config.py` · Configuração central

Mantém a identidade dos mercados em um único ponto:

```text
Brasil → BR → R$
EUA    → US → US$
```

**Brasil** e **EUA** são os únicos nomes de mercado exibidos na interface.

#### `app.py` · Experiência analítica

Responsável pela interface Streamlit, filtros, cards executivos, gráficos Plotly, indicadores, insights, navegação e responsividade.

---

## 📁 Estrutura do projeto

```text
dashboard_dre_sg_global/
│
├── app.py                    # Aplicação Streamlit
├── etl.py                    # ETL, padronização e métricas
├── config.py                 # Configuração de Brasil, EUA e moedas
├── gerar_graficos.py         # Scripts auxiliares de visualização
├── requirements.txt          # Dependências Python
├── README.md                 # Documentação
│
├── data/
│   ├── DRE_BR_DNC.xlsx       # Base Brasil
│   └── DRE_US_DNC.xlsx       # Base EUA
│
└── docs/
    └── screenshots/          # Imagens da documentação
```

---

## 📈 Indicadores financeiros

| Indicador | Cálculo / conceito |
|---|---|
| **Receita Bruta** | Soma das receitas classificadas na base |
| **Devoluções** | Valores classificados como devolução |
| **Receita Líquida** | Receita Bruta − Devoluções |
| **Custos** | Custos Variáveis + Custos Fixos |
| **Despesas** | Despesas Fixas + Despesas Variáveis |
| **Resultado Operacional** | Receita Líquida − Custos − Despesas |
| **Resultado Líquido** | Resultado Operacional − Impostos |
| **Margem Operacional** | Resultado Operacional / Receita Líquida |
| **Margem de Contribuição** | (Receita Líquida − Custos Variáveis) / Receita Líquida |
| **Margem Líquida** | Resultado Líquido / Receita Líquida |
| **EBITDA (proxy)** | Estimativa operacional baseada nas categorias disponíveis |
| **Net Cash** | Entradas − Saídas |
| **Burn Rate** | Média do consumo de caixa nos períodos negativos |
| **Runway** | Saldo Atual / Burn Rate médio |

### ⚠️ Transparência sobre o EBITDA

A base fornecida não apresenta todas as informações necessárias para calcular um EBITDA contábil estrito, especialmente depreciação e amortização.

Por isso, o dashboard utiliza deliberadamente a nomenclatura **EBITDA (proxy)**.

> **Princípio:** quando os dados não suportam uma conclusão confiável, a aplicação deve sinalizar a limitação em vez de criar falsa precisão.

---

## 🧹 Qualidade dos dados

O processo realiza seleção das colunas necessárias, tratamento de datas inválidas, conversão de valores financeiros, tratamento de ausências, padronização das classificações, taxonomia comum para Brasil e EUA, dimensões temporais e identificação de ausência de movimentação real no caixa.

### Limitações conhecidas

| Situação | Tratamento |
|---|---|
| Caixa Brasil sem movimentação suficiente | Burn Rate e Runway não são tratados como indicadores confiáveis |
| Squad sem variação significativa | Não gerar conclusões artificiais por equipe |
| Orçado sem dados suficientes | Comparação Orçado × Realizado permanece limitada |
| Despesas possivelmente incompletas | Margens elevadas devem ser interpretadas com cautela |
| Moedas diferentes | Valores permanecem em R$ e US$; comparação nominal direta é evitada |

---

## 🎨 Princípios de UX

A experiência visual segue uma abordagem **executiva, limpa e orientada à leitura rápida**:

- hierarquia visual clara;
- KPIs destacados antes dos gráficos;
- **Brasil** e **EUA** apresentados de forma consistente;
- cores utilizadas com função semântica;
- gráficos com leitura objetiva;
- filtros acessíveis;
- layout adaptável a diferentes larguras de tela;
- mensagens de alerta quando a qualidade da informação exigir cautela.

---

## 🚀 Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/AdrianoJesusDeveloper/Dashboard_de_DRE_SG-Global_Group_DNC.git
cd Dashboard_de_DRE_SG-Global_Group_DNC
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv
```

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute o dashboard

```bash
streamlit run app.py
```

A aplicação será disponibilizada normalmente em `http://localhost:8501`.

### 📂 Bases padrão

```text
data/DRE_BR_DNC.xlsx
data/DRE_US_DNC.xlsx
```

A aplicação também possui suporte ao envio manual das bases pela interface.

---

## 🗺 Roadmap

### ✅ Implementado

- [x] ETL das bases Brasil e EUA
- [x] Padronização da taxonomia DRE
- [x] Receita Bruta e Receita Líquida
- [x] Margem Operacional
- [x] Margem Líquida
- [x] Margem de Contribuição
- [x] EBITDA identificado como proxy
- [x] Fluxo de Caixa
- [x] Burn Rate e Runway quando suportados pela base
- [x] Filtros por empresa e período
- [x] Responsividade
- [x] Configuração centralizada de mercados
- [x] Nomenclatura oficial **Brasil** e **EUA**

### 🔜 Próximos passos

- [ ] Testes automatizados das métricas financeiras
- [ ] Camada formal de Data Quality
- [ ] Refinamento da experiência mobile
- [ ] Filtros avançados de período
- [ ] Comparação Orçado × Realizado quando houver dados confiáveis
- [ ] Segmentação por Squad quando houver dados confiáveis
- [ ] Deploy público
- [ ] Autenticação e controle de acesso

---

## 💼 Competências demonstradas

**Python · Pandas · ETL · Data Analysis · Business Intelligence · Financial Analytics · Plotly · Streamlit · Data Quality · Git/GitHub**

> **Extrair → Limpar → Padronizar → Modelar → Calcular → Visualizar → Interpretar → Decidir**

---

## 👤 Autor

<div align="center">

### **Adriano Jesus da Costa**

**Data & Analytics · Python · SQL · Business Intelligence**

Projeto I · Escola de Dados · DNC

[![GitHub](https://img.shields.io/badge/GitHub-AdrianoJesusDeveloper-181717?style=for-the-badge&logo=github)](https://github.com/AdrianoJesusDeveloper)

<br>

**Construído com Python, Pandas, Plotly e Streamlit.**

</div>
