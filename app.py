import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Control P2P & Banesco Pro", layout="wide", initial_sidebar_state="collapsed")

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
        "Fecha", "Origen", "Tipo", "Monto USDT", 
        "Tasa (Bs/FIAT)", "Total Neto (Bs/FIAT)", 
        "Método / Banco", "Referencia / Nota"
    ])

def guardar_datos(df):
    df.to_json(DB_FILE, orient="records", date_format="iso")

df_actual = cargar_datos()

tab1, tab2, tab3 = st.tabs(["⚡ Registro Banesco / Pago Móvil", "📥 Cargar CSV Binance", "📊 Resumen y Caja"])

# ==========================================
# TAB 1: REGISTRO RÁPIDO BANESCO / PAGO MÓVIL
# ==========================================
with tab1:
    st.subheader("✍️ Registro Rápido (Banesco, Pago Móvil, etc.)")
    
    with st.form("form_banesco", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            tipo = st.selectbox("Tipo de Operación", ["Compra USDT", "Venta USDT"])
            metodo = st.selectbox("Método / Banco", ["Banesco", "Pago Móvil", "Zinli", "Ubii", "Otro"])
            monto_usdt = st.number_input("Monto en USDT", min_value=0.0, step=10.0, value=0.0)
        
        with col_b:
            tasa = st.number_input("Tasa (Bs por USDT)", min_value=0.0, step=0.1, value=0.0)
            referencia = st.text_input("N° Referencia o Nota (Opcional)", placeholder="Ej: Ref 123456 / Pago Móvil")

        total_bs = monto_usdt * tasa
        st.info(f"💰 Total a transferir/recibir en Bs: **{total_bs:,.2f} Bs.**")
        
        submitted = st.form_submit_button("💾 Registrar Operación", use_container_width=True)
        
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
                    "Referencia / Nota": referencia
                }])
                
                df_actualizado = pd.concat([df_actual, nueva_op], ignore_index=True)
                guardar_datos(df_actualizado)
                st.success("¡Transacción registrada y guardada con éxito!")
                st.rerun()
            else:
                st.error("Por favor ingresa un monto USDT y una tasa mayores a 0.")

# ==========================================
# TAB 2: IMPORTADOR INTELIGENTE DE BINANCE CSV
# ==========================================
with tab2:
    st.subheader("📥 Importar Historial de Órdenes P2P de Binance")
    st.caption("Sube tu archivo CSV descargado de Binance para agregarlo al sistema.")
    
    uploaded_file = st.file_uploader("Selecciona el archivo CSV descargado de Binance", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                try:
                    df_raw = pd.read_csv(uploaded_file, encoding="utf-8", dtype=str)
                except Exception:
                    uploaded_file.seek(0)
                    df_raw = pd.read_csv(uploaded_file, encoding="latin-1", dtype=str)
            else:
                df_raw = pd.read_excel(uploaded_file, dtype=str)
                
            df_raw.columns = df_raw.columns.str.strip()
            
            primer_valor = str(df_raw.iloc[0, 0]) if not df_raw.empty else ""
            if "No hay datos" in primer_valor or df_raw.empty:
                st.warning("⚠️ El archivo de Binance no contiene operaciones registradas.")
            else:
                st.write("🔍 **Vista previa del archivo cargado:**")
                st.dataframe(df_raw.head(5).astype(str), use_container_width=True)
                
                if st.button("🚀 Procesar e Importar al Sistema"):
                    df_binance = pd.DataFrame()
                    
                    def buscar_col(lista_nombres):
                        for col in df_raw.columns:
                            for name in lista_nombres:
                                if name.lower() in col.lower():
                                    return col
                        return None
                    
                    c_fecha = buscar_col(["Hora de creación", "created", "date", "fecha"])
                    df_binance["Fecha"] = df_raw[c_fecha].astype(str) if c_fecha else pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
                    
                    df_binance["Origen"] = "Importación Binance"
                    
                    c_tipo = buscar_col(["Tipo de orden", "type", "side", "tipo"])
                    if c_tipo:
                        df_binance["Tipo"] = df_raw[c_tipo].apply(lambda x: "Compra USDT" if any(k in str(x).lower() for k in ["buy", "compra", "comprar", "b"]) else "Venta USDT")
                    else:
                        df_binance["Tipo"] = "Compra USDT"
                    
                    c_monto = buscar_col(["Cantidad", "amount", "quantity", "usdt"])
                    if c_monto:
                        df_binance["Monto USDT"] = pd.to_numeric(df_raw[c_monto].astype(str).str.replace(",", "").str.extract(r'([\d\.]+)')[0], errors="coerce").fillna(0.0)
                    else:
                        df_binance["Monto USDT"] = 0.0
                    
                    c_tasa = buscar_col(["Precio", "price", "tasa"])
                    if c_tasa:
                        df_binance["Tasa (Bs/FIAT)"] = pd.to_numeric(df_raw[c_tasa].astype(str).str.replace(",", "").str.extract(r'([\d\.]+)')[0], errors="coerce").fillna(0.0)
                    else:
                        df_binance["Tasa (Bs/FIAT)"] = 0.0
                    
                    c_total = buscar_col(["Precio Total", "total price", "total"])
                    if c_total:
                        df_binance["Total Neto (Bs/FIAT)"] = pd.to_numeric(df_raw[c_total].astype(str).str.replace(",", "").str.extract(r'([\d\.]+)')[0], errors="coerce").fillna(0.0)
                    else:
                        df_binance["Total Neto (Bs/FIAT)"] = df_binance["Monto USDT"] * df_binance["Tasa (Bs/FIAT)"]
                    
                    c_metodo = buscar_col(["Tipo de Fiat", "method", "fiat"])
                    df_binance["Método / Banco"] = df_raw[c_metodo].astype(str) if c_metodo else "Binance P2P"
                    df_binance["Referencia / Nota"] = "Orden Binance"
                    
                    df_actualizado = pd.concat([df_actual, df_binance], ignore_index=True)
                    guardar_datos(df_actualizado)
                    st.success(f"¡Se importaron y guardaron {len(df_binance)} operaciones con éxito!")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# ==========================================
# TAB 3: RESUMEN CONTABLE Y CAJA
# ==========================================
with tab3:
    df = cargar_datos()
    
    if not df.empty and len(df) > 0:
        df["Monto USDT"] = pd.to_numeric(df["Monto USDT"], errors="coerce").fillna(0.0)
        df["Total Neto (Bs/FIAT)"] = pd.to_numeric(df["Total Neto (Bs/FIAT)"], errors="coerce").fillna(0.0)
        
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
        
        st.subheader("📋 Historial Contable Registrado")
        st.dataframe(df.astype(str), use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Reporte en Excel / CSV",
            data=csv,
            file_name="Reporte_Contable_P2P.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Aún no hay transacciones guardadas. Utiliza la pestaña de Registro o Cargar CSV para comenzar.")
