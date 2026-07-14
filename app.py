import streamlit as st
import pandas as pd
import requests
import io
import time

# Configuración de la página
st.set_page_config(
    page_title="Copa Espíritu del Sur - Portal de Destiladores",
    page_icon="🥃",
    layout="wide"
)

# Estilos CSS personalizados para la interfaz
st.markdown("""
<style>
    .main-header {
        font-size: 38px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 📊 CONFIGURACIÓN DE DATOS & MONITOREO HTTP
# ==============================================================================
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

# GIDs de las pestañas de Google Sheets
GID_USUARIOS = "728286132"
GID_REGLAMENTO = "0"  # Cambiar por el GID real de tu reglamento si difiere

if "http_logs" not in st.session_state:
    st.session_state["http_logs"] = []

def monitored_get(url, timeout=10):
    """Realiza una petición GET registrando latencia, estado y endpoint para el monitor."""
    inicio = time.time()
    try:
        res = requests.get(url, timeout=timeout)
        latencia = time.time() - inicio
        st.session_state["http_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "metodo": "GET",
            "endpoint": url,
            "estado": res.status_code,
            "latencia": f"{latencia:.2f}s",
            "payload": "-"
        })
        return res
    except Exception as e:
        latencia = time.time() - inicio
        st.session_state["http_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "metodo": "GET",
            "endpoint": url,
            "estado": "Error de Conexión",
            "latencia": f"{latencia:.2f}s",
            "payload": str(e)[:50]
        })
        raise e

@st.cache_data(ttl=60)
def cargar_datos_sheet(gid):
    """Carga y procesa datos de Google Sheets de forma segura."""
    try:
        url = BASE_URL_SHEET + gid
        respuesta = monitored_get(url)
        if respuesta.status_code == 200:
            df = pd.read_csv(io.StringIO(respuesta.text))
            return df.to_dict(orient="records")
        else:
            st.error(f"Error al acceder a los datos (Código {respuesta.status_code}). Verifica permisos.")
            return []
    except Exception as e:
        st.error(f"No se pudo conectar con la base de datos: {e}")
        return []

# Carga de base de datos de usuarios de forma global
usuarios_db = cargar_datos_sheet(GID_USUARIOS)

# ==============================================================================
# 🧠 CONTROL DE ESTADOS DE SESIÓN (SESSION STATE)
# ==============================================================================
if "rol" not in st.session_state:
    st.session_state["rol"] = None
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN (LOGIN & REGISTRO)
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Festival de Destiladores Patagónicos<br><span style='font-size:24px;color:#D97706;font-weight:bold;'>Copa Espíritu del Sur</span></h1>", unsafe_allow_html=True)
    
    if st.session_state["mostrar_confirmacion_registro"]:
        st.success("🎉 ¡Cuenta Creada de Forma Exitosa! Procede a ingresar tus datos en la pestaña de inicio de sesión.")
        if st.button("👍 Entendido"):
            st.session_state["mostrar_confirmacion_registro"] = False
            st.rerun()

    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse como Nuevo Destilador"])
    
    with tab_login:
        usr = st.text_input("Nombre de Usuario", key="login_user").strip()
        pwd = st.text_input("Contraseña", type="password", key="login_pass").strip()
        
        if st.button("🚀 Ingresar al Portal", key="btn_login"):
            if usuarios_db:
                # Normalizamos las entradas para evitar fallos por espacios o mayúsculas
                usr_input = str(usr).strip().lower()
                pwd_input = str(pwd).strip()
                
                autenticado = False
                for row in usuarios_db:
                    # Limpiamos los encabezados de columnas y valores
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    
                    db_usuario = row_clean.get("usuario", "").strip().lower()
                    db_contrasena = row_clean.get("contrasena", "").strip()
                    
                    # Verificación exacta de usuario
                    if db_usuario == usr_input:
                        # UPGRADE: Comparamos la contraseña de forma directa para soportar puntos (.)
                        # Mantenemos compatibilidad con split por punto si tu base de datos previa lo requería
                        if db_contrasena == pwd_input or db_contrasena.split('.')[0] == pwd_input:
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            autenticado = True
                            st.rerun()
                            break
                            
                if not autenticado:
                    st.error("❌ Credenciales inválidas. Verifica mayúsculas, minúsculas o espacios extra en tu usuario/contraseña.")
            else:
                st.error("❌ La base de datos de usuarios está vacía o no se pudo leer.")
                
    with tab_registro:
        st.subheader("Formulario de Registro")
        st.info("Para completar tu registro de destilador, por favor contacta al administrador del sistema para que añada tus credenciales a la planilla central de Google Sheets.")

# ==============================================================================
# 🏠 PORTAL DE DESTILADORES (SESIÓN INICIADA)
# ==============================================================================
else:
    # Barra lateral de navegación y logout
    with st.sidebar:
        st.markdown(f"### Bienvenido,\n**{st.session_state['usuario']}**")
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state["rol"] = None
            st.session_state["usuario"] = None
            st.rerun()

    # Contenido principal del Portal
    st.markdown(f"<h1 class='main-header'>🥃 Portal de Destiladores - Copa Espíritu del Sur</h1>", unsafe_allow_html=True)
    st.write(f"Has ingresado con éxito. Este es tu panel de control personalizado.")
    
    # Vista de logs de red (Monitor HTTP integrado)
    with st.expander("📡 Monitor de Peticiones HTTP (Herramienta de Diagnóstico)"):
        if st.session_state["http_logs"]:
            logs_df = pd.DataFrame(st.session_state["http_logs"])
            st.dataframe(logs_df, use_container_width=True)
            
            # Botón de exportación rápida
            csv_logs = logs_df.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="📥 Exportar Log de Peticiones",
                data=csv_logs,
                file_name=f"{time.strftime('%Y-%m-%d_H%M')}_export.csv",
                mime="text/csv"
            )
        else:
            st.info("No se han registrado peticiones HTTP en esta sesión.")
