import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard de Salários na Área de Dados - Jean Papa",
    page_icon="📊",
    layout="wide",
)

# --- Carregamento dos dados ---
df = pd.read_csv("https://raw.githubusercontent.com/vqrca/dashboard_salarios_dados/refs/heads/main/dados-imersao-final.csv")

# --- Barra Lateral (Filtros) ---
st.sidebar.header("🔍 Filtros")

anos_disponiveis = sorted(df['ano'].unique())
anos_selecionados = st.sidebar.multiselect("Ano", anos_disponiveis, default=anos_disponiveis)

senioridades_disponiveis = sorted(df['senioridade'].unique())
senioridades_selecionadas = st.sidebar.multiselect("Senioridade", senioridades_disponiveis, default=senioridades_disponiveis)

contratos_disponiveis = sorted(df['contrato'].unique())
contratos_selecionados = st.sidebar.multiselect("Tipo de Contrato", contratos_disponiveis, default=contratos_disponiveis)

tamanhos_disponiveis = sorted(df['tamanho_empresa'].unique())
tamanhos_selecionados = st.sidebar.multiselect("Tamanho da Empresa", tamanhos_disponiveis, default=tamanhos_disponiveis)

# --- Filtragem do DataFrame ---
df_filtrado = df[
    (df['ano'].isin(anos_selecionados)) &
    (df['senioridade'].isin(senioridades_selecionadas)) &
    (df['contrato'].isin(contratos_selecionados)) &
    (df['tamanho_empresa'].isin(tamanhos_selecionados))
]

# --- Conteúdo Principal ---
st.title("🎲 Dashboard de Análise Salarial na Área de Dados Desenvolvido com Python – Jean Papa")
st.markdown("Explore os dados salariais na área de dados nos últimos anos. Utilize os filtros à esquerda para refinar sua análise.")

# --- Métricas Principais (KPIs) ---
st.subheader("Métricas gerais (Salário anual em USD)")

if not df_filtrado.empty:
    salario_medio = df_filtrado['usd'].mean()
    salario_maximo = df_filtrado['usd'].max()
    total_registros = df_filtrado.shape[0]
    cargo_mais_frequente = df_filtrado["cargo"].mode()[0]
else:
    salario_medio = 0
    salario_maximo = 0
    total_registros = 0
    cargo_mais_frequente = "-"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Salário médio", f"${salario_medio:,.0f}")
col2.metric("Salário máximo", f"${salario_maximo:,.0f}")
col3.metric("Total de registros", f"{total_registros:,}")
col4.metric("Cargo mais frequente", cargo_mais_frequente)

st.markdown("---")

# --- Análises Visuais com Plotly ---
st.subheader("Gráficos")

col_graf1, col_graf2 = st.columns(2)

# Top 10 cargos por salário médio (mantém color='cargo', mas sem legenda visível)
with col_graf1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado
            .groupby('cargo')['usd']
            .mean()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )

        grafico_cargos = px.bar(
            top_cargos,
            x='usd',
            y='cargo',
            orientation='h',
            color='cargo',  # mantém cores por cargo
            title="Top 10 cargos por salário médio",
            labels={'usd': 'Média salarial anual (USD)', 'cargo': ''},
            color_discrete_sequence=px.colors.qualitative.Set2
        )

        grafico_cargos.update_traces(
            text=top_cargos['usd'].round(0),
            texttemplate='%{x:,.0f}',
            textposition='outside'
        )

        grafico_cargos.update_layout(
            title_x=0.1,
            showlegend=False,  # legenda oculta por padrão
            yaxis={'categoryorder': 'array', 'categoryarray': top_cargos['cargo']},
            margin=dict(t=60, b=60, l=10, r=10)
        )

        st.plotly_chart(grafico_cargos, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de cargos.")

# Distribuição de salários anuais (histograma enxuto com bins adaptativos e linhas de média/mediana)
with col_graf2:
    if not df_filtrado.empty:
        s = df_filtrado['usd'].dropna().astype(float)
        n = s.size

        # Cálculo adaptativo de nbins: Freedman–Diaconis com fallback para Sturges
        def calcular_nbins(series: pd.Series) -> int:
            n_local = series.size
            if n_local <= 1:
                return 10
            q1, q3 = np.percentile(series, [25, 75])
            iqr = q3 - q1
            data_range = float(series.max() - series.min())
            nbins_fd = None
            if iqr > 0 and data_range > 0:
                h = 2 * iqr * (n_local ** (-1/3))
                if h > 0:
                    nbins_fd = int(np.clip(round(data_range / h), 5, 100))
            if nbins_fd and nbins_fd >= 5:
                return nbins_fd
            # Fallback Sturges
            nbins_sturges = int(np.clip(np.ceil(np.log2(max(n_local, 2)) + 1), 5, 100))
            return nbins_sturges

        nbins = calcular_nbins(s) if n > 0 else 30

        grafico_hist = px.histogram(
            df_filtrado,
            x='usd',
            nbins=nbins,
            title="Distribuição de salários anuais",
            labels={'usd': 'Faixa salarial (USD)'},
            color_discrete_sequence=px.colors.qualitative.Set2
        )

        # Linhas de referência: média e mediana
        if n > 0:
            media = float(s.mean())
            mediana = float(s.median())
            grafico_hist.add_vline(
                x=media, line_dash='dash', line_color='#1f77b4',
                annotation_text=f"Média ${media:,.0f}", annotation_position='top left'
            )
            grafico_hist.add_vline(
                x=mediana, line_dash='dot', line_color='#ff7f0e',
                annotation_text=f"Mediana ${mediana:,.0f}", annotation_position='top right'
            )

        # Formatação de eixos e hover
        grafico_hist.update_layout(
            title_x=0.1,
            margin=dict(t=60, b=60, l=10, r=10)
        )
        grafico_hist.update_yaxes(title_text='Quantidade')
        grafico_hist.update_xaxes(
            tickformat=',.0f'
        )

        grafico_hist.update_traces(
            hovertemplate="Faixa salarial: $%{x:,.0f}<br>Quantidade: %{y:,}<extra></extra>"
        )

        st.plotly_chart(grafico_hist, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico de distribuição.")

# Gráfico de proporção dos tipos de trabalho
col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    if not df_filtrado.empty:
        remoto_contagem = df_filtrado['remoto'].value_counts().reset_index()
        remoto_contagem.columns = ['tipo_trabalho', 'quantidade']
        grafico_remoto = px.pie(
            remoto_contagem,
            names='tipo_trabalho',
            values='quantidade',
            title='Proporção dos tipos de trabalho',
            hole=0.5
        )
        grafico_remoto.update_traces(textinfo='percent+label')
        grafico_remoto.update_layout(title_x=0.1)
        st.plotly_chart(grafico_remoto, use_container_width=True)
    else:
        st.warning("Nenhum dado para exibir no gráfico dos tipos de trabalho.")

# Mapa por país (exemplo com Cientista de Dados)
with col_graf4:
    if not df_filtrado.empty:
        df_ds = df_filtrado[df_filtrado['cargo'] == 'Data Scientist']
        if not df_ds.empty:
            media_ds_pais = df_ds.groupby('residencia_iso3')['usd'].mean().reset_index()
            grafico_paises = px.choropleth(
                media_ds_pais,
                locations='residencia_iso3',
                color='usd',
                color_continuous_scale='rdylgn',
                title='Salário médio de Cientista de Dados por país',
                labels={'usd': 'Salário médio (USD)', 'residencia_iso3': 'País'}
            )
            grafico_paises.update_layout(title_x=0.1)
            st.plotly_chart(grafico_paises, use_container_width=True)
        else:
            st.info("Não há registros de Cientista de Dados após os filtros selecionados.")
    else:
        st.warning("Nenhum dado para exibir no gráfico de países.")

# --- Tabela de Dados Detalhados ---
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado)
