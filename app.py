import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Calculadora de Precificação - ML & Shopee", layout="wide"
)

st.title("📊 Calculadora de Precificação: Mercado Livre vs. Shopee")
st.markdown(
    "Insira os custos base do produto e escolha o canal de venda para calcular o preço ideal, margens e limites promocionais com as taxas atualizadas."
)

with st.sidebar:
  st.header("⚙️ Configurações e Custos")
  sku = st.text_input("SKU / Nome do Produto", "Informe o Produto")

  st.subheader("Custos Diretos")
  custo_produto = st.number_input(
      "Custo do Produto (R$)", min_value=0.0, value=0.0, step=1.0
  )
  frete_compra = st.number_input(
      "Frete de Compra / Insumo (R$)", min_value=0.0, value=0.0, step=1.0
  )
  embalagem = st.number_input(
      "Custo de Embalagem (R$)", min_value=0.0, value=0.0, step=1.0
  )
  taxa_fixa_custom = st.number_input(
      "Taxa Fixa Manual (R$)", min_value=0.0, value=0.0, step=0.5
  )

  st.subheader("Impostos e Margem")
  imposto_pct = st.number_input(
      "Imposto (%)", min_value=0.0, max_value=1.0, value=0.0, step=0.01
  )
  margem_lucro_pct = st.number_input(
      "Margem de Lucro Desejada (%)",
      min_value=0.0,
      max_value=1.0,
      value=0.20,
      step=0.01,
  )

# Escolha da Plataforma
st.header("🛒 Seleção de Canal de Venda")
canal = st.selectbox("Escolha o Marketplace:", ["Mercado Livre", "Shopee"])

comissao_pct = 0.0
taxa_fixa_canal = 0.0
detalhes_canal = ""
frete_venda = 0.0

if canal == "Mercado Livre":
  tipo_anuncio = st.radio("Tipo de Anúncio no Mercado Livre:", [
      "Clássico",
      "Premium",
  ])
  if tipo_anuncio == "Clássico":
    comissao_pct = 0.14
    detalhes_canal = "Anúncio Clássico: Comissão padrão de 14%."
  else:
    comissao_pct = 0.19
    detalhes_canal = (
        "Anúncio Premium: Comissão padrão de 19% (permite parcelamento sem"
        " juros)."
    )

  frete_venda = st.number_input(
      "Custo de Frete Grátis / Envio (R$) [Se aplicável]",
      min_value=0.0,
      value=0.0,
      step=1.0,
  )
  custo_operacional = (
      custo_produto + frete_compra + embalagem + taxa_fixa_custom + frete_venda
  )

elif canal == "Shopee":
  programa_fg = st.checkbox(
      "Participa do Programa de Frete Grátis Extra?", value=True
  )
  if programa_fg:
    comissao_pct = (
        0.20  # Comissão ajustada com o programa de frete grátis extra da Shopee
    )
    taxa_fixa_canal = 4.00  # Taxa fixa por item da Shopee
    detalhes_canal = (
        "Shopee com Frete Grátis Extra: Comissão de 20% + Taxa Fixa por item."
    )
  else:
    comissao_pct = 0.14
    taxa_fixa_canal = 4.00
    detalhes_canal = "Shopee Padrão: Comissão de 14% + Taxa Fixa por item."

  custo_operacional = (
      custo_produto
      + frete_compra
      + embalagem
      + taxa_fixa_custom
      + taxa_fixa_canal
  )

# --- CÁLCULOS ---
denominador = 1 - imposto_pct - comissao_pct - margem_lucro_pct

if denominador <= 0:
  st.error(
      "Erro: A soma de Imposto + Comissão + Margem de Lucro é maior ou igual a"
      " 100%! Ajuste os percentuais."
  )
else:
  preco_ideal = custo_operacional / denominador
  val_imposto = preco_ideal * imposto_pct
  val_comissao = preco_ideal * comissao_pct
  lucro_liquido = (
      preco_ideal - val_imposto - val_comissao - custo_operacional
  )

  # Preço Promoção Mínimo (Metade da Margem)
  denominador_promo = 1 - imposto_pct - comissao_pct - (margem_lucro_pct / 2)
  preco_promo = custo_operacional / denominador_promo
  val_imposto_promo = preco_promo * imposto_pct
  val_comissao_promo = preco_promo * comissao_pct
  lucro_liquido_promo = (
      preco_promo - val_imposto_promo - val_comissao_promo - custo_operacional
  )
  margem_promo_efetiva = (
      lucro_liquido_promo / preco_promo if preco_promo > 0 else 0
  )

  # Status
  if margem_promo_efetiva <= 0:
    status_promo = "PREJUÍZO 🔴"
  elif margem_promo_efetiva < 0.05:
    status_promo = "MARGEM BAIXA 🟡"
  else:
    status_promo = "OK 🟢"

  st.markdown("---")
  st.subheader(f"📈 Resultados da Precificação para: {sku} ({canal})")
  st.info(detalhes_canal)

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Custo Operacional Total", f"R$ {custo_operacional:.2f}")
  with col2:
    st.metric("Preço de Venda Ideal", f"R$ {preco_ideal:.2f}")
  with col3:
    st.metric(
        "Lucro Líquido Ideal",
        f"R$ {lucro_liquido:.2f}",
        f"{margem_lucro_pct*100:.1f}%",
    )
  with col4:
    st.metric("Preço Promoção Mínimo", f"R$ {preco_promo:.2f}", status_promo)

  st.markdown("### 🔍 Detalhamento dos Custos e Margens")
  df_detalhe = pd.DataFrame({
      "Componente": [
          "Custo do Produto",
          "Frete / Embalagem / Taxas Fixas",
          "Impostos",
          "Comissão Marketplace",
          "Lucro Líquido Alvo",
          "Preço de Venda Total",
      ],
      "Valor (R$)": [
          custo_produto,
          (
              frete_compra
              + embalagem
              + taxa_fixa_custom
              + frete_venda
              + taxa_fixa_canal
          ),
          val_imposto,
          val_comissao,
          lucro_liquido,
          preco_ideal,
      ],
      "Percentual (%)": [
          (custo_produto / preco_ideal) * 100,
          (
              (
                  frete_compra
                  + embalagem
                  + taxa_fixa_custom
                  + frete_venda
                  + taxa_fixa_canal
              )
              / preco_ideal
          )
          * 100,
          imposto_pct * 100,
          comissao_pct * 100,
          margem_lucro_pct * 100,
          100.0,
      ],
  })
  st.dataframe(
      df_detalhe.style.format(
          {"Valor (R$)": "R$ {:.2f}", "Percentual (%)": "{:.1f}%"}
      )
  )
