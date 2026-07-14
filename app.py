import streamlit as st
import pandas as pd
import requests
import io
import time

# ==============================================================================
# ⚙️ CONFIGURACIÓN DE LA PÁGINA E INTERFAZ
# ==============================================================================
st.set_page_config(
    page_title="Copa Espíritu del Sur - Portal de Destiladores",
    page_icon="🥃",
    layout="wide"
)

# Estilos CSS para mantener la estética de la app
st.markdown("""
<style>
    .main-header {
        font-size: 38px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
    }
    .section-header {
        color: #D97706;
        border-bottom: 2px solid #F3F4F6;
        padding-bottom: 8px;
        margin-top: 20px;
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
# 📊 CONEXIÓN CON GOOGLE SHEETS & MONITOREO HTTP
# ==============================================================================
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

# GIDs de las pestañas de tu Google Sheets
GID_USUARIOS = "728286132"
GID_REGLAMENTO = "0"  # ID de la pestaña de reglamento

# Inicialización del log de peticiones en el estado de la sesión
if "http_logs" not in st.session_state:
    st.session_state["http_logs"] = []

def monitored_get(url, timeout=10):
    """Realiza peticiones GET registrando la latencia y respuestas para el monitor."""
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
    """Carga de datos optimizada con caché."""
    try:
        url = BASE_URL_SHEET + gid
        respuesta = monitored_get(url)
        if respuesta.status_code == 200:
            df = pd.read_csv(io.StringIO(respuesta.text))
            return df
        else:
            st.error(f"Error {respuesta.status_code} al leer la pestaña {gid}.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

# Carga global de la base de datos de usuarios
df_usuarios = cargar_datos_sheet(GID_USUARIOS)

# ==============================================================================
# 🧠 CONTROL DE ESTADOS (SESSION STATE)
# ==============================================================================
if "rol" not in st.session_state:
    st.session_state["rol"] = None
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False

# ==============================================================================
# 🔐 PANTALLA DE INICIO DE SESIÓN
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Festival de Destiladores Patagónicos<br><span style='font-size:24px;color:#D97706;font-weight:bold;'>Copa Espíritu del Sur</span></h1>", unsafe_allow_html=True)
    
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse como Nuevo Destilador"])
    
    with tab_login:
        usr = st.text_input("Nombre de Usuario", key="login_user").strip()
        pwd = st.text_input("Contraseña", type="password", key="login_pass").strip()
        
        if st.button("🚀 Ingresar al Portal", key="btn_login"):
            if not df_usuarios.empty:
                # Normalización de entradas
                usr_input = str(usr).strip().lower()
                pwd_input = str(pwd).strip()
                
                autenticado = False
                
                for _, row in df_usuarios.iterrows():
                    # Limpieza y mapeo de las columnas de la fila
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    
                    db_usuario = row_clean.get("usuario", "").strip().lower()
                    db_contrasena = row_clean.get("contrasena", "").strip()
                    
                    if db_usuario == usr_input:
                        # UPGRADE: Validación robusta compatible con contraseñas complejas (con puntos, guiones y asteriscos)
                        if db_contrasena == pwd_input or db_contrasena.split('.')[0] == pwd_input:
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            autenticado = True
                            st.success("¡Acceso concedido!")
                            st.rerun()
                            break
                
                if not autenticado:
                    st.error("❌ Credenciales incorrectas. Comprueba mayúsculas, minúsculas o caracteres especiales.")
            else:
                st.error("❌ No se pudo cargar la base de datos de usuarios de Google Sheets.")
                
    with tab_registro:
        st.subheader("Registro de Nuevos Destiladores")
        st.info("Para darte de alta en el sistema, por favor solicita al administrador del evento que registre tus datos de usuario en la planilla central de Google Sheets.")

# ==============================================================================
# 🏠 PORTAL DE TRABAJO (SESIÓN INICIADA)
# ==============================================================================
else:
    # 1. BARRA LATERAL (Menú de Navegación del Usuario)
    with st.sidebar:
        st.image("https://img.icons8.com/papercut/120/whiskey-bottle.png", width=100)
        st.markdown(f"### Bienvenido/a,\n**{st.session_state['usuario']}**")
        st.markdown("---")
        
        # Selección de la pantalla activa en la app
        opcion_menu = st.radio(
            "Selecciona una Sección:",
            ["📜 Reglamento del Certamen", "🧪 Mis Muestras y Evaluaciones", "📊 Resultados Generales"]
        )
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["rol"] = None
            st.session_state["usuario"] = None
            st.rerun()

    # 2. CONTENIDO PRINCIPAL SEGÚN LA SECCIÓN SELECCIONADA
    if opcion_menu == "📜 Reglamento del Certamen":
        st.markdown("<h2 class='section-header'>📜 Reglamento Oficial - Copa Espíritu del Sur</h2>", unsafe_allow_html=True)
        st.write("A continuación puedes visualizar y descargar las bases y condiciones del certamen de destilados:")
        
        # Carga dinámica del reglamento desde Google Sheets
        df_reglamento = cargar_datos_sheet(GID_REGLAMENTO)
        if not df_reglamento.empty:
            st.dataframe(df_reglamento, use_container_width=True, hide_index=True)
        else:
            st.warning("No se pudo cargar el reglamento desde la base de datos en este momento.")

    elif opcion_menu == "🧪 Mis Muestras y Evaluaciones":
        st.markdown("<h2 class='section-header'>🧪 Registro y Evaluación de Muestras</h2>", unsafe_allow_html=True)
        st.write("Aquí puedes realizar el seguimiento de tus muestras presentadas para la evaluación de los jurados.")
        
        # Simulación / Visualización de las muestras del usuario
        st.info("Próximamente se habilitará el formulario de carga técnica de muestras en esta sección.")

    elif opcion_menu == "📊 Resultados Generales":
        st.markdown("<h2 class='section-header'>📊 Resultados y Medallero del Certamen</h2>", unsafe_allow_html=True)
        st.write("Resultados parciales y consolidados del panel de cata:")
        
        # Contenedores métricos limpios
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='metric-box'><h4>Total Muestras</h4><h2>12</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='metric-box'><h4>Categorías</h4><h2>3</h2></div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<div class='metric-box'><h4>Muestras Oro</h4><h2>2</h2></div>", unsafe_allow_html=True)

    # 3. MONITOR DE PETICIONES HTTP (Ubicado al pie de la página de forma oculta/desplegable)
    st.markdown("---")
    with st.expander("📡 Monitor de Peticiones HTTP (Herramienta de Diagnóstico Técnico)"):
        if st.session_state["http_logs"]:
            logs_df = pd.DataFrame(st.session_state["http_logs"])
            st.dataframe(logs_df, use_container_width=True)
            
            csv_logs = logs_df.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="📥 Descargar Logs de Peticiones",
                data=csv_logs,
                file_name=f"log_sistema_{time.strftime('%Y-%m-%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Aún no se han registrado peticiones de red en esta sesión.")
