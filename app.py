import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import io

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES REALES CON GOOGLE SHEETS (VÍA GID DIRECTO)
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbwfds8TIlD9Ed2f-Cz8p3Qf3RZcC3gc27Lnb-EaHDicMNu0rFkyPvi5op2JcIGv_TIBoA/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

def enviar_datos(datos):
    try:
        response = requests.post(URL_SCRIPT, data=datos)
        if response.text == "OK" or response.status_code == 200:
            return response.text
        return False
    except:
        return False

def leer_hoja(nombre_hoja):
    try:
        # Diccionario de enrutamiento por GID para blindar el sistema
        gids = {
            "Usuarios": "728286132",
            "Configuracion": "0",
            "Muestras_Destiladores": "1664128347",
            "Datos_Destiladores": "826367168",
            "Evaluaciones": "482282527"
        }
        
        # Conseguimos el GID asignado, si no existe usamos el por defecto (0)
        gid_seleccionado = gids.get(nombre_hoja, "0")
        url = BASE_URL_SHEET + gid_seleccionado
            
        res = requests.get(url, timeout=10)
        texto_puro = res.text
        
        if "<html" in texto_puro.lower() or "<doctype" in texto_puro.lower():
            return {"error": "Google Sheets bloqueó la respuesta pública. Revisa los permisos de compartir.", "datos": []}
            
        df = pd.read_csv(io.StringIO(texto_puro))
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return {"error": None, "datos": df.to_dict(orient="records"), "columnas": list(df.columns)}
    except Exception as e:
        return {"error": str(e), "datos": [], "columnas": []}

# ==============================================================================
# 🥃 CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Sistema Integral de Catas", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None
    st.session_state["mesa"] = "Mesa 1"

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stSlider { padding-bottom: 0px; margin-bottom: -10px; }
    .reportview-container { background: #fafafa; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 24px; margin-bottom: 10px; }
    .card-info { background-color: #F3F4F6; padding: 10px; border-radius: 6px; border-left: 4px solid #3B82F6; margin-bottom: 5px; }
    .card-score { background-color: #ECFDF5; padding: 10px; border-radius: 6px; border-left: 4px solid #10B981; text-align: center; color: #065F46; font-size: 18px; font-weight: bold; margin-bottom: 5px; }
    .card-warning { background-color: #FEF3C7; padding: 12px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 10px; }
    div[data-testid="stBlock"] { padding: 5px 10px; }
</style>
""", unsafe_allow_html=True)

# LECTURA EN TIEMPO REAL PARA EL LOGUEO
resultado_lectura = leer_hoja("Usuarios")
usuarios_db = resultado_lectura["datos"]

# ==============================================================================
# 🔍 MONITOR DE DESARROLLADOR INTERNO (Mesa de Trabajo)
# ==============================================================================
with st.expander("🛠️ PANEL DE CONTROL Y AUDITORÍA EN VIVO (Mesa de Trabajo)"):
    if resultado_lectura["error"]:
        st.error(f"Fallo crítico de conexión: {resultado_lectura['error']}")
    else:
        st.success("✅ Red de Vinculación de GIDs: OPERATIVA Y ESTABLE")
        st.write("**Columnas detectadas en 'Usuarios':**", resultado_lectura.get("columnas", []))
        st.write("**Filas leídas en tiempo real por la App:**", usuarios_db)

# ==============================================================================
# 🔐 PANTALLA DE LOGUEO DIRECTO Y TOLERANTE
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Plataforma Tecnológica - Concurso Destilados</h1>", unsafe_allow_html=True)
    
    menu = ["Iniciar Sesión", "Registrarse como Nuevo Destilador"]
    choice = st.sidebar.selectbox("Navegación", menu)
    
    if choice == "Iniciar Sesión":
        st.subheader("Acceso de Miembros del Concurso")
        usr = st.text_input("Nombre de Usuario").strip()
        pwd = st.text_input("Contraseña", type="password").strip()
        
        if st.button("🚀 Ingresar al Sistema"):
            if usuarios_db:
                usuario_encontrado = False
                usr_input = str(usr).strip().lower()
                pwd_input = str(pwd).strip()
                
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    user_val = row_clean.get("usuario", row_clean.get("user", "")).strip().lower()
                    
                    pass_raw = row_clean.get("contrasena", row_clean.get("contraseña", row_clean.get("pass", ""))).strip()
                    pass_val = pass_raw.split('.')[0] if '.' in pass_raw else pass_raw
                    
                    role_val = row_clean.get("rol", row_clean.get("role", "Destilador")).strip()
                    mesa_val = row_clean.get("mesa", "Mesa 1").strip()
                    
                    if user_val == usr_input:
                        usuario_encontrado = True
                        if pass_val == pwd_input:
                            st.session_state["rol"] = role_val
                            st.session_state["usuario"] = usr
                            st.session_state["mesa"] = mesa_val
                            st.success(f"¡Bienvenido {usr}!")
                            st.rerun()
                        else:
                            st.error(f"🔒 Contraseña incorrecta. (Ingresado: '{pwd_input}' | En BD: '{pass_val}')")
                        break
                
                if not usuario_encontrado:
                    st.error("❌ Usuario no registrado en la base de datos.")
            else:
                st.error("❌ La base de datos no contiene registros legibles o está vacía.")
                
    elif choice == "Registrarse como Nuevo Destilador":
        st.subheader("Formulario de Auto-Registro Autónomo")
        st.write("Crea tu cuenta corporativa para poder inscribir tus muestras.")
        nuevo_usr = st.text_input("Elige un Nombre de Usuario (Sin espacios)").strip()
        nueva_pwd = st.text_input("Crea tu Contraseña de Acceso", type="password").strip()
        confirmar_pwd = st.text_input("Repite tu Contraseña", type="password").strip()
        
        if st.button("📝 Confirmar Registro"):
            if nuevo_usr == "" or nueva_pwd == "":
                st.warning("⚠️ Todos los campos son obligatorios.")
            elif nueva_pwd != confirmar_pwd:
                st.error("❌ Las contraseñas ingresadas no coinciden.")
            else:
                existe = False
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "") == nuevo_usr.lower():
                        existe = True
                        break
                
                if existe:
                    st.error("⚠️ Este nombre de usuario ya se encuentra ocupado. Intenta con otro.")
                else:
                    payload = {
                        "action": "registro_usuario",
                        "usuario": nuevo_usr,
                        "contrasena": nueva_pwd
                    }
                    res = enviar_datos(payload)
                    st.success("🎉 ¡Cuenta creada con éxito! Ya puedes cambiar a 'Iniciar Sesión' en el menú de la izquierda.")

# ==============================================================================
# INTERFAZ PARA USUARIOS AUTENTICADOS
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 Miembro Oficial")
    st.sidebar.info(f"**Usuario:** {st.session_state['usuario']}\n\n**Rol:** {st.session_state['rol']}\n\n**Ubicación:** {st.session_state['mesa']}")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.session_state["usuario"] = None
        st.rerun()
        
    resultado_config = leer_hoja("Configuracion")
    df_config = pd.DataFrame(resultado_config["datos"]) if resultado_config["datos"] else pd.DataFrame(columns=["Sección", "Parámetro", "Peso", "Categorias"])
    
    categorias_disponibles = []
    if "Categorias" in df_config.columns:
        categorias_disponibles = [str(cat).strip() for cat in df_config["Categorias"].dropna().unique() if str(cat).strip() != "" and str(cat).strip().lower() != "nan"]
    if not categorias_disponibles:
        categorias_disponibles = ["Gin", "Whisky", "Vodka", "Ron"]

    # ==========================================================================
    # 🚀 INTERFAZ: ROL DESTILADOR
    # ==========================================================================
    if st.session_state["rol"] == "Destilador":
        st.title("🚀 Panel Técnico del Destilador")
        tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 Perfil Destilería", "🥃 Inscribir Muestra", "📄 Constancias y Descargas"])
        
        with tab_perfil:
            st.subheader("📋 Información del Establecimiento")
            st.write("Mantén actualizados los datos oficiales de tu empresa para las declaraciones juradas del concurso.")
            
            nombre_destileria = st.text_input("Nombre de la Destilería / Razón Social").strip()
            marca_comercial = st.text_input("Marca Comercial Principal").strip()
            nro_rne = st.text_input("Número de Registro de Establecimiento (RNE / Equivalente local)").strip()
            localidad_provincia = st.text_input("📍 Ubicación (Ciudad y Provincia/Estado)").strip()
            telefono_contacto = st.text_input("📞 Teléfono / WhatsApp de Contacto").strip()
            
            if st.button("💾 Guardar Datos del Perfil"):
                if not nombre_destileria or not nro_rne or not localidad_provincia:
                    st.error("❌ Por favor, completa al menos el Nombre, el Registro (RNE) y la Ubicación.")
                else:
                    payload_perfil = {
                        "action": "registro_usuario",
                        "action_real": "guardar_perfil",
                        "usuario": st.session_state["usuario"],
                        "destileria": nombre_destileria,
                        "marca": marca_comercial,
                        "rne": nro_rne,
                        "ubicacion": localidad_provincia,
                        "telefono": telefono_contacto
                    }
                    
                    con_exito = enviar_datos(payload_perfil)
                    if con_exito:
                        st.success("🎉 ¡Perfil de la destilería guardado y sincronizado con éxito!")
                    else:
                        st.error("⚠️ El perfil se procesó localmente, pero hubo un desfase al conectar con Google Sheets.")
            
        with tab_muestra:
            st.markdown("""
            <div class='card-warning'>
                <h4>⚠️ REGLAMENTO DE LOGÍSTICA OBLIGATORIO</h4>
                <p>Por cada muestra comercial inscrita, la destilería se compromete a enviar físico de <b>dos (2) botellas de al menos 300 ml cada una</b>.</p>
            </div>
            """, unsafe_allow_html=True)
            
            nombre_dist = st.text_input("Nombre comercial del Destilado / Producto")
            cat_seleccionada = st.selectbox("Categoría de Producto", categorias_disponibles)
            nro_insc_prod = st.text_input("Número de Inscripción del Producto (RNPA / Registro local)")
            volumen = st.number_input("Volumen exacto de la botella (en ML)", min_value=0, value=750, step=50)
            comprobante = st.file_uploader("Subir foto o PDF del comprobante de pago", type=["jpg", "png", "pdf"])
            
            if st.button("🔒 Confirmar e Inscribir Muestra"):
                if not nombre_dist.strip() or not nro_insc_prod.strip():
                    st.error("❌ Por favor completa todos los campos técnicos requeridos.")
                elif volumen < 300:
                    st.error("❌ El volumen de la muestra física debe ser de al menos 300 ml por botella.")
                elif comprobante is None:
                    st.error("❌ Es obligatorio adjuntar el comprobante de pago.")
                else:
                    st.success("✅ Muestra pre-inscripta con éxito.")

        with tab_estado:
            st.subheader("Mis Muestras e Impresión de Etiquetas")
            st.info("Tus muestras aprobadas aparecerán aquí.")

    # ==========================================================================
    # 🧠 INTERFAZ: ROL JUEZ (EVALUACIÓN EN VIVO Y CONTROL DE MESA)
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.markdown("<h2 style='margin-bottom:0px;'>🧠 Evaluación Sensorial a Ciegas</h2>", unsafe_allow_html=True)
        
        resultado_muestras = leer_hoja("Muestras_Destiladores")
        df_muestras_real = pd.DataFrame(resultado_muestras["datos"]) if resultado_muestras["datos"] else pd.DataFrame(columns=["Código_Muestra", "Categoría"])
        
        if not df_muestras_real.empty and "Código_Muestra" in df_muestras_real.columns:
            df_muestras_real["Código_Muestra"] = df_muestras_real["Código_Muestra"].astype(str).str.strip()
            lista_codigos = [c for c in df_muestras_real["Código_Muestra"].unique() if c != "" and c.lower() != "nan"]
        else:
            lista_codigos = ["DST-1084", "DST-4921", "DST-8832"]
            
        col_m1, col_m2, col_m3 = st.columns([2, 2, 2])
        with col_m1:
            muestra_a_evaluar = st.selectbox("Seleccione Código de Muestra", lista_codigos)
            
       categoria_detectada = "No especificada"
        if not df_muestras_real.empty and "Código_Muestra" in df_muestras_real.columns and "Categoría" in df_muestras_real.columns:
            match_cat = df_muestras_real[df_muestras_real["Código_Muestra"] == muestra_a_evaluar]
            if not match_cat.empty:
                categoria_detectada = str(match_cat.iloc[0]["Categoría"])
        else:
            mock_cats = {"DST-1084": "Gin", "DST-4921": "Whisky", "DST-8832": "Ron"}
            categoria_detectada = mock_cats.get(muestra_a_evaluar, "Gin")
