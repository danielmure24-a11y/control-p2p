import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Control P2P", layout="wide", initial_sidebar_state="collapsed")

st.title("📊 Control P2P & Contador")

# Inicializar almacenamiento local en la sesión
if "transacciones" not in st.session_state:
    st.session_state["transacciones"] = pd.DataFrame(
        columns=["Fecha", "Tipo", "Monto USDT", "Tasa", "Total FIAT", "Método", "Comisión (%)", "Neto FIAT"]
    )

tab1, tab2 = st.tabs(["📝 Registrar", "📈 Resumen y Caja"])

with tab1:
    st.subheader("Nueva Operación")
    with st.form("form_p2p", clear_on_submit=True):
        tipo = st.selectbox("Tipo de Operación", ["Compra USDT", "Venta USDT"])
        monto = st.number_input("Monto en USDT", min_value=0.0, step=1.0)
        tasa = st.number_input("Tasa (Precio por USDT)", min_value=0.0, step=0.1)
        metodo = st.selectbox("Método de Pago", ["Banesco", "Pago Móvil", "Zinli", "Ubii", "Otro"])
        comision = st.number_input("Comisión %", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
        
        submitted = st.form_submit_button("💾 Guardar Transacción", use_container_width=True)
        
        if submitted and monto > 0 and tasa > 0:
            total_fiat = monto * tasa
            desc = total_fiat * (comision / 100)
            neto = total_fiat + desc if tipo == "Compra USDT" else total_fiat - desc
            
            nueva_tx = {
                "Fecha": datetime.now().strftime("%d/%m %H:%M"),
                "Tipo": tipo,
                "Monto USDT": monto,
                "Tasa": tasa,
                "Total FIAT": total_fiat,
                "Método": metodo,
                "Comisión (%)": comision,
                "Neto FIAT": neto
            }
            st.session_state["transacciones"] = pd.concat(
                [st.session_state["transacciones"], pd.DataFrame([nueva_tx])], ignore_index=True
            )
            st.success("¡Registrado con éxito!")

with tab2:
    df = st.session_state["transacciones"]
    if not df.empty:
        compras = df[df["Tipo"] == "Compra USDT"]
        ventas = df[df["Tipo"] == "Venta USDT"]
        
        usdt_comprado = compras["Monto USDT"].sum()
        usdt_vendido = ventas["Monto USDT"].sum()
        caja_usdt = usdt_comprado - usdt_vendido
        
        fiat_gastado = compras["Neto FIAT"].sum()
        fiat_recibido = ventas["Neto FIAT"].sum()
        pnl = fiat_recibido - fiat_gastado
        
        col1, col2 = st.columns(2)
        col1.metric("Caja USDT", f"{caja_usdt:,.2f}")
        col2.metric("Ganancia (PnL)", f"{pnl:,.2f} FIAT")
        
        st.markdown("---")
        st.subheader("Historial")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no has registrado transacciones.")
