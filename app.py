import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Control P2P & Banesco Pro",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- OCULTAR MENÚ Y ELEMENTOS DE STREAMLIT ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# SISTEMA DE CONTRASEÑA Y LOGIN
# ==========================================
# Define tu contraseña personalizada aquí (puedes cambiar "1234" por la que prefieras)
CONTRASEÑA_CORRECTA = "1234"


def verificar_clave():
  if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

  if not st.session_state["autenticado"]:
    st.title("🔒 Acceso Restringido")
    st.caption("Ingresa tu clave de seguridad para ver el panel contable.")

    with st.form("form_login"):
      clave = st.text_input("Contraseña", type="password")
      submitted = st.form_submit_button(
          "Ingresar", use_container_width=True
      )

      if submitted:
        if clave == CONTRASEÑA_CORRECTA:
          st.session_state["autenticado"] = True
          st.success("¡Acceso concedido!")
          st.rerun()
        else:
          st.error("❌ Contraseña incorrecta. Inténtalo de nuevo.")
    return False
  return True


# Si no está autenticado, detiene la ejecución aquí
if not verificar_clave():
  st.stop()

# ==========================================
# CÓDIGO PRINCIPAL DE LA APLICACIÓN
# ==========================================

st.title("⚡ Control P2P Binance & Banesco Pro")

# Archivo local persistente en el servidor de la app
DB_FILE = "registros_p2p.json"


def cargar_datos():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r") as f:
        data = json.load(f)
      return pd.DataFrame(data)
    except Exception:
      pass
  return pd.DataFrame(columns=[
      "Fecha",
      "Origen",
      "Tipo",
      "Monto USDT",
      "Tasa (Bs/FIAT)",
      "Total Neto (Bs/FIAT)",
      "Método / Banco",
      "Referencia / Nota",
  ])


def guardar_datos(df):
  df.to_json(DB_FILE, orient="records", date_format="iso")


df_actual = cargar_datos()

# Botón para cerrar sesión en la parte superior
col_header1, col_header2 = st.columns([0.8, 0.2])
with col_header2:
  if st.button("🔒 Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()

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
        nueva_op = pd.DataFrame([{
            "Fecha": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
            "Origen": "Manual / Banesco",
            "Tipo": tipo,
            "Monto USDT": monto_usdt,
            "Tasa (Bs/FIAT)": tasa,
            "Total Neto (Bs/FIAT)": total_bs,
            "Método / Banco": metodo,
            "Referencia / Nota": referencia,
        }])

        df_actualizado = pd.concat([df_actual, nueva_op], ignore_index=True)
        guardar_datos(df_actualizado)
        st.success("¡Transacción registrada y guardada con éxito!")
        st.rerun()
