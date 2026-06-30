import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse
import random
from datetime import datetime
import os

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES CON GOOGLE SHEETS
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxUj67JHjqpIjtbV3mxtz4QBRSH9Mu31Bcls9OuH2nllncpIq-6mvvH4sxEO_3ao2faIw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="
NUMERO_WHATSAPP = "5492914737608"

def enviar_datos(datos):
    try:
        response = requests.post(URL_SCRIPT, data=datos, timeout=25)
        if "OK" in response.text:
            return True
        return False
    except Exception as e:
        st.error(f"Error de red: {str(e)}")
        return False

def leer_hoja(nombre_hoja):
    try:
        gids = {
            "Usuarios": "728286132",
            "Configuracion": "0",
            "Muestras_Destiladores": "1664128347",
            "Datos_Destiladores": "826367168"
        }
        gid_seleccionado = gids.get(nombre_hoja, "0")
        url = BASE_URL_SHEET + gid_seleccionado
        res = requests.get(url, timeout=10)
        df = pd.read_csv(io.StringIO(res.text))
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return {"datos": df.to_dict(orient="records")}
    except:
        return {"datos": []}

# ==============================================================================
# 🥃 CONFIGURACIÓN DE INTERFAZ Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Inscripciones - Festival de Destiladores", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False
if "mostrar_confirmacion_muestra" not in st.session_state:
    st.session_state["mostrar_confirmacion_muestra"] = False
if "info_muestra_creada" not in st.session_state:
    st.session_state["info_muestra_creada"] = {}

# CSS Limpio para el espaciado
st.markdown("""
<style>
    .stApp { margin-top: 50px !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 26px; text-align: center; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
</style>
""", unsafe_allow_html=True)

# Carga inicial de datos desde el Sheet
usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
destiladores_db = leer_hoja("Datos_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

# 📈 CONTROL DE COTIZACIÓN (Lectura robusta sin importar mayúsculas o acentos en el Excel)
cotizacion_hoy = 1000.0
categorias_disponibles = ["Gin", "Whisky", "Vodka", "Ron"]

if not df_config.empty:
    # Creamos un mapeo de columnas normalizadas
    columnas_originales = {c.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').strip(): c for c in df_config.columns}
    
    if "cotizacion" in columnas_originales:
        col_real = columnas_originales["cotizacion"]
        try:
            cotizacion_hoy = float(df_config[col_real].dropna().iloc[0])
        except:
            pass
            
    if "categorias" in columnas_originales:
        col_cat_real = columnas_originales["categorias"]
        categorias_disponibles = [str(x).strip() for x in df_config[col_cat_real].dropna().unique() if str(x).strip() != ""]

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 1° Festival de Destiladores Argentinos<br><span style='font-size:20px;color:#D97706;'>Copa Espíritu del Sur</span></h1>", unsafe_allow_html=True)
    
    if st.session_state["mostrar_confirmacion_registro"]:
        st.success("🎉 ¡Cuenta Creada de Forma Exitosa! El registro se completó en el servidor. Procede a ingresar tus datos en la pestaña de inicio de sesión.")
        if st.button("👍 Entendido"):
            st.session_state["mostrar_confirmacion_registro"] = False
            st.rerun()

    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse como Nuevo Destilador"])
    
    with tab_login:
        usr = st.text_input("Nombre de Usuario", key="login_user").strip()
        pwd = st.text_input("Contraseña", type="password", key="login_pass").strip()
        
        if st.button("🚀 Ingresar al Portal", key="btn_login"):
            if usuarios_db:
                usr_input = str(usr).strip().lower()
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "").strip().lower() == usr_input:
                        if row_clean.get("contrasena", "").split('.')[0] == str(pwd).strip():
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            st.rerun()
            st.error("❌ Credenciales inválidas.")
            
    with tab_registro:
        nuevo_usr = st.text_input("Elige tu Nombre de Usuario", key="reg_user").strip().lower()
        nueva_pwd = st.text_input("Elige tu Contraseña", type="password", key="reg_pass").strip()
        
        if st.button("✨ Confirmar y Crear Cuenta", key="btn_registro"):
            if not nuevo_usr or not nueva_pwd:
                st.error("❌ Todos los campos son obligatorios.")
            elif " " in nuevo_usr:
                st.error("❌ El nombre de usuario no puede contener espacios.")
            elif usuarios_db and any(str(r.get("usuario", "")).strip().lower() == nuevo_usr for r in usuarios_db):
                st.error("❌ Nombre de usuario no disponible. Ya se encuentra registrado.")
            else:
                if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.session_state["mostrar_confirmacion_registro"] = True
                    st.rerun()

# ==============================================================================
# 🚀 ENTORNO INTERNO DEL USUARIO AUTENTICADO
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

    perfil_existente = {}
    nombre_destileria_global = "Sin especificar"
    if destiladores_db:
        for row in destiladores_db:
            if str(row.get("usuario", "")).lower() == st.session_state["usuario"].lower():
                perfil_existente = row
                if row.get("destileria", ""):
                    nombre_destileria_global = str(row.get("destileria", ""))
                break

    # 🛠️ VENTANA DE CONFIRMACIÓN CON COMPONENTES NATIVOS DE STREAMLIT (SEGURO E INDESTRUCTIBLE)
    if st.session_state["mostrar_confirmacion_muestra"] and st.session_state["info_muestra_creada"]:
        info = st.session_state["info_muestra_creada"]
        
        if "producto" in info and "categoria" in info and "id_muestra" in info:
            monto_pesos = info['valor_usd'] * cotizacion_hoy
            
            # Texto adaptado al 1° Festival oficial
            texto_wa = (
                f"🏆 *1° FESTIVAL DE DESTILADORES ARGENTINOS - COPA ESPÍRITU DEL SUR*\n"
                f"Hola! Envío el comprobante de pago de mi inscripción:\n\n"
                f"🆔 *Código:* {info['id_muestra']}\n"
                f"🏬 *Destilería:* {nombre_destileria_global}\n"
                f"🥃 *Muestra:* {info['producto']} ({info['categoria']})\n"
                f"📊 *Muestra N°:* {info['nro_muestra']} (Lote {info['lote_nro']})\n"
                f"💰 *Arancel:* USD {info['valor_usd']} (${monto_pesos:,.0f} ARS)\n\n"
                f"⚠️ *Nota:* Adjunto el comprobante correspondiente a este código identificador."
            )
            texto_encoded = urllib.parse.quote(texto_wa)
            url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={texto_encoded}"
            
            st.success(f"🏆 ¡Muestra Registrada Exitosamente!\n\n**Concurso:** 1° Festival de Destiladores Argentinos — Copa Espíritu del Sur\n\n**Código asignado:** {info['id_muestra']}")
            
            st.info(f"""
            📌 **Instrucciones de Pago y Aranceles:**
            
            • **Arancel de Inscripción:** USD {info['valor_usd']} (${monto_pesos:,.0f} ARS)
            • 📊 *Calculado al cambio de tu Excel: $ {cotizacion_hoy:,.2f} ARS por Dólar*
            
            • 🏦 **Alias Cuenta Pesos:** festivaldestiladores
            • 🏦 **Alias Cuenta Dólares:** festivaldestiladores.usd
            
            ⚠️ **PAGOS MÚLTIPLES:** Si decides abonar varias muestras juntas en una misma transferencia, **debes ingresar el flujo de WhatsApp de cada muestra individualmente** y adjuntar el mismo comprobante en cada una. Esto es indispensable para asociar el pago al código **{info['id_muestra']}**.
            """)
            
            st.warning("⚠️ **PASO FINAL OBLIGATORIO:** Haz clic abajo para notificar el pago por WhatsApp:")
            
            # Botón de redirección nativo
            st.link_button("📱 Enviar Comprobante por WhatsApp", url_wa, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Hubo un problema al procesar los datos de la muestra de forma local.")
        
        if st.button("✅ Procesado / Cerrar Ventana", type="primary"):
            st.session_state["mostrar_confirmacion_muestra"] = False
            st.session_state["info_muestra_creada"] = {}
            st.rerun()

    tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 1. Perfil Destilería", "🥃 2. Inscribir Muestra", "📄 3. Estado de Mis Muestras"])

    with tab_perfil:
        st.subheader("📋 Información de Contacto")
        n_resp = st.text_input("Responsable Técnico", value=str(perfil_existente.get("responsable", ""))).strip()
        c_resp = st.text_input("Correo Oficial", value=str(perfil_existente.get("correo", ""
