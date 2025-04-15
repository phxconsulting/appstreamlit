import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO

# 🔐 Coloque sua chave da OpenAI aqui diretamente
api_key = "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"

# Inicializar cliente OpenAI
client = openai.OpenAI(api_key=api_key)

# Configuração inicial do Streamlit
st.set_page_config(page_title="Relatório de Campanhas com IA", layout="wide")
st.title("📈 Relatório de Campanhas - Análise com IA")

# Upload do CSV
uploaded_file = st.file_uploader("📂 Faça o upload do CSV das campanhas", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Converter colunas de data
    df["Reporting starts"] = pd.to_datetime(df["Reporting starts"], errors="coerce")
    df["Reporting ends"] = pd.to_datetime(df["Reporting ends"], errors="coerce")

    # Filtros na barra lateral
    with st.sidebar:
        st.header("🔍 Filtros")
        date_range = st.date_input("Período", [df["Reporting starts"].min(), df["Reporting ends"].max()])
        selected_names = st.multiselect("Campanhas", df["Campaign name"].unique(), default=list(df["Campaign name"].unique()))

    # Aplicar filtros
    df_filtered = df[
        (df["Reporting starts"] >= pd.to_datetime(date_range[0])) &
        (df["Reporting ends"] <= pd.to_datetime(date_range[1])) &
        (df["Campaign name"].isin(selected_names))
    ]

    # Converter colunas numéricas
    df_filtered["Results"] = pd.to_numeric(df_filtered["Results"], errors="coerce").fillna(0)
    df_filtered["Cost per results"] = pd.to_numeric(df_filtered["Cost per results"], errors="coerce").fillna(0)
    df_filtered["Amount spent (BRL)"] = pd.to_numeric(df_filtered["Amount spent (BRL)"], errors="coerce").fillna(0)
    df_filtered["CTR (link click-through rate)"] = pd.to_numeric(df_filtered["CTR (link click-through rate)"], errors="coerce").fillna(0)

    # KPIs
    total_spent = df_filtered["Amount spent (BRL)"].sum()
    total_results = df_filtered["Results"].sum()
    avg_cpr = df_filtered["Cost per results"].mean()
    avg_ctr = df_filtered["CTR (link click-through rate)"].mean()
    best_camp_by_result = df_filtered.loc[df_filtered["Results"].idxmax(), "Campaign name"]
    best_camp_by_cpr = df_filtered.loc[df_filtered["Cost per results"].idxmin(), "Campaign name"]
    best_ctr_campaign = df_filtered.loc[df_filtered["CTR (link click-through rate)"].idxmax(), "Campaign name"]

    # Mostrar métricas principais
    st.subheader("📊 Indicadores de Campanhas")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("💸 Investimento Total", f"R$ {total_spent:,.2f}")
    col2.metric("📬 Total de Resultados", int(total_results))
    col3.metric("📊 Custo Médio por Resultado", f"R$ {avg_cpr:.2f}")
    col4.metric("🥇 Maior Resultado", best_camp_by_result)
    col5.metric("🔥 Melhor Custo/Resultado", best_camp_by_cpr)
    col6.metric("🚀 Melhor CTR", best_ctr_campaign)

    # Gráfico por campanha
    st.subheader("📈 Desempenho por Campanha")
    chart_data = df_filtered[["Campaign name", "Results", "Amount spent (BRL)"]].set_index("Campaign name")
    st.bar_chart(chart_data)

    # Gráfico de tipo de conversão
    st.subheader("🥧 Tipo de Conversão")
    result_types = df_filtered["Result indicator"].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(result_types, labels=result_types.index.str.extract(r'actions:onsite_conversion.(.*)')[0], autopct='%1.1f%%')
    st.pyplot(fig1)

    # Tabela
    st.subheader("📋 Tabela de Dados Filtrados")
    st.dataframe(df_filtered)

    # Análise com IA
    st.subheader("🤖 Insights Estratégicos com IA")

    prompt = f"""
    Sou gestor de marketing analisando campanhas:

    - Investimento total: R$ {total_spent:,.2f}
    - Total de resultados: {int(total_results)}
    - Custo médio por resultado: R$ {avg_cpr:.2f}
    - Melhor campanha (resultados): {best_camp_by_result}
    - Melhor campanha (custo/resultado): {best_camp_by_cpr}
    - Melhor CTR: {best_ctr_campaign} ({avg_ctr:.2f}%)

    Quais insights e estratégias posso adotar para escalar resultados e reduzir custos?
    """

    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um estrategista de marketing digital focado em performance."},
            {"role": "user", "content": prompt}
        ]
    )

    analise_ia = resposta.choices[0].message.content
    st.write(analise_ia)

    # Geração de PDF
    st.subheader("📄 Exportar Relatório em PDF")

    if st.button("📥 Baixar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Relatório de Campanhas de Marketing", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Período: {date_range[0]} até {date_range[1]}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 10, f"Total investido: R$ {total_spent:,.2f}", ln=True)
        pdf.cell(0, 10, f"Total de resultados: {int(total_results)}", ln=True)
        pdf.cell(0, 10, f"Custo médio por resultado: R$ {avg_cpr:.2f}", ln=True)
        pdf.cell(0, 10, f"Melhor campanha por resultado: {best_camp_by_result}", ln=True)
        pdf.cell(0, 10, f"Melhor campanha por custo: {best_camp_by_cpr}", ln=True)
        pdf.cell(0, 10, f"Melhor CTR: {best_ctr_campaign} ({avg_ctr:.2f}%)", ln=True)
        pdf.ln(10)
        pdf.multi_cell(0, 10, f"Análise com IA:\n\n{analise_ia}")

        buffer = BytesIO()
        pdf.output(buffer)
        st.download_button(
            label="📤 Clique para baixar o PDF",
            data=buffer.getvalue(),
            file_name="relatorio_campanhas.pdf",
            mime="application/pdf"
        )

else:
    st.info("📂 Faça o upload do arquivo CSV para visualizar o relatório.")








