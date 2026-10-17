import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Control P2P & Banesco",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.title("⚡ Control P2P Binance & Banesco Pro")

# Inicialización del almacenamiento local
if "transacciones" not in st.session_state:
  st.session_state["transacciones"] = pd.DataFrame(
      columns=[
          "Fecha",
          "Origen",
          "Tipo",
          "Monto USDT",
          "Tasa (Bs/FIAT)",
          "Total Neto (Bs/FIAT)",
          "Método / Banco",
          "Referencia / Nota",
      ]
  )

tab1, tab2, tab3 = st.tabs(
    ["⚡ Registro Banesco / Pago Móvil", "📥 Cargar CSV Binance", "📊 Resumen y Caja"]
)

# ==========================================
# TAB 1: REGISTRO RÁPIDO BANESCO / PAGO MÓVIL
# ==========================================
with tab1:
  st.subheader("✍️ Registro Rápido (Banesco, Pago Móvil, etc.)")

  with st.form("form_banesco", clear_on_submit=True):
    col_a, col_b = st.columns(2)

    with col_a:
      tipo = st.selectbox("Tipo de Operación", ["Compra USDT", "Venta USDT"])
      metodo = st.selectbox(
          "Método / Banco", ["Banesco", "Pago Móvil", "Zinli", "Ubii", "Otro"]
      )
      monto_usdt = st.number_input(
          "Monto en USDT", min_value=0.0, step=10.0, value=0.0
      )

    with col_b:
      tasa = st.number_input(
          "Tasa (Bs por USDT)", min_value=0.0, step=0.1, value=0.0
      )
      referencia = st.text_input(
          "N° Referencia o Nota (Opcional)",
          placeholder="Ej: Ref 123456 / Pago Móvil",
      )

    total_bs = monto_usdt * tasa
    st.info(f"💰 Total a transferir/recibir en Bs: **{total_bs:,.2f} Bs.**")

    submitted = st.form_submit_button(
        "💾 Registrar Operación", use_container_width=True
    )

    if submitted:
      if monto_usdt > 0 and tasa > 0:
        nueva_op = {
            "Fecha": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),