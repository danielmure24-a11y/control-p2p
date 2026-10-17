import streamlit as st
import pandas as pd

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
                    "Origen": "Manual / Banesco",
                    "Tipo": tipo,
                    "Monto USDT": monto_usdt,
                    "Tasa (Bs/FIAT)": tasa,
                    "Total Neto (Bs/FIAT)": total_bs,
                    "Método / Banco": metodo,
                    "Referencia / Nota": referencia,
                }
                st.session_state["transacciones"] = pd.concat(
                    [st.session_state["transacciones"], pd.DataFrame([nueva_op])],
                    ignore_index=True,
                )
                st.success("¡Transacción registrada exitosamente!")
                st.rerun()
            else:
                st.error("Por favor ingresa un monto USDT y una tasa mayores a 0.")

# ==========================================
# TAB 2: IMPORTADOR INTELIGENTE DE BINANCE CSV
# ==========================================
with tab2:
    st.subheader("📥 Importar Historial de Órdenes P2P de Binance")
    st.caption(
        "Descarga tu reporte CSV de órdenes P2P desde Binance y súbelo aquí para"
        " registrarlas automáticamente."
    )

    uploaded_file = st.file_uploader(
        "Selecciona el archivo CSV descargado de Binance", type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)

            st.write("🔍 **Vista previa del archivo cargado:**")
            st.dataframe(df_raw.head(3), use_container_width=True)

            if st.button("🚀 Procesar e Importar Transacciones"):
                df_binance = pd.DataFrame()

                col_fecha = [
                    c
                    for c in df_raw.columns
                    if "Created" in c or "Date" in c or "Time" in c
                ]
                df_binance["Fecha"] = (
                    df_raw[col_fecha[0]]
                    if col_fecha
                    else pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                )

                df_binance["Origen"] = "Importación Binance"

                col_tipo = [c for c in df_raw.columns if "Type" in c or "Side" in c]
                if col_tipo:
                    df_binance["Tipo"] = df_raw[col_tipo[0]].apply(
                        lambda x: (
                            "Compra USDT"
                            if "Buy" in str(x) or "Compra" in str(x)
                            else "Venta USDT"
                        )
                    )
                else:
                    df_binance["Tipo"] = "Compra USDT"

                col_monto = [
                    c
                    for c in df_raw.columns
                    if "Amount" in c or "Quantity" in c or "Crypto Amount" in c
                ]
                df_binance["Monto USDT"] = (
                    pd.to_numeric(df_raw[col_monto[0]], errors="coerce").fillna(0)
                    if col_monto
                    else 0.0
                )

                col_tasa = [c for c in df_raw.columns if "Price" in c or "Tasa" in c]
                df_binance["Tasa (Bs/FIAT)"] = (
                    pd.to_numeric(df_raw[col_tasa[0]], errors="coerce").fillna(0)
                    if col_tasa
                    else 0.0
                )

                col_total = [c for c in df_raw.columns if "Total" in c]
                if col_total:
                    df_binance["Total Neto (Bs/FIAT)"] = pd.to_numeric(
                        df_raw[col_total[0]], errors="coerce"
                    ).fillna(0)
                else:
                    df_binance["Total Neto (Bs/FIAT)"] = (
                        df_binance["Monto USDT"] * df_binance["Tasa (Bs/FIAT)"]
                    )

                col_metodo = [
                    c for c in df_raw.columns if "Method" in c or "Payment" in c
                ]
                df_binance["Método / Banco"] = (
                    df_raw[col_metodo[0]] if col_metodo else "Binance P2P"
                )
                df_binance["Referencia / Nota"] = "Orden Binance"

                st.session_state["transacciones"] = pd.concat(
                    [st.session_state["transacciones"], df_binance], ignore_index=True
                )
                st.success(f"¡Se importaron {len(df_binance)} operaciones con éxito!")
                st.rerun()

        except Exception as e:
            st.error(
                "Error al procesar el archivo. Asegúrate de que es el reporte de"
                f" Binance. Detalle: {e}"
            )

# ==========================================
# TAB 3: RESUMEN CONTABLE Y CAJA
# ==========================================
with tab3:
    df = st.session_state["transacciones"]

    if not df.empty:
        compras = df[df["Tipo"] == "Compra USDT"]
        ventas = df[df["Tipo"] == "Venta USDT"]

        total_comprado = compras["Monto USDT"].sum()
        total_vendido = ventas["Monto USDT"].sum()
        balance_caja_usdt = total_comprado - total_vendido

        bs_gastados = compras["Total Neto (Bs/FIAT)"].sum()
        bs_recibidos = ventas["Total Neto (Bs/FIAT)"].sum()
        pnl_bs = bs_recibidos - bs_gastados

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 USDT en Caja", f"{balance_caja_usdt:,.2f} USDT")
        col2.metric("💸 Total Bs Movilizados", f"{bs_gastados + bs_recibidos:,.2f} Bs")
        col3.metric("📈 Ganancia/Pérdida (PnL)", f"{pnl_bs:,.2f} Bs")

        st.markdown("---")

        st.subheader("📋 Historial Contable")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar Reporte en Excel / CSV",
            data=csv,
            file_name="Reporte_Contable_P2P.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info(
            "Aún no hay transacciones registradas. Utiliza la pestaña de Registro o"
            " Cargar CSV para comenzar."
        )
