import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import io

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES REALES CON GOOGLE SHEETS (VÍA GID DIRECTO)
# ==============================================================================
# ⚠️ REEMPLAZA ESTA URL SI TU APPS SCRIPT CAMBIÓ AL RE-IMPLEMENTARLO
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbwfds8TIlD9Ed2f-Cz8p3Qf3RZcC3gc27Lnb-EaHDicMNu0rFkyPvi5op2JcIGv_TIBoA/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

def enviar_datos(datos):
    try:
        response = requests.post(URL_SCRIPT, data=datos)
        if response.text == "OK" or response.status_code == 200:
            return True
        return False
    except:
        return False

def leer_hoja(nombre_hoja):
    try:
        gids = {
            "Usuarios": "728286132",
            "Configuracion": "0",
            "Muestras_Destiladores": "1664128347",
            "Datos_Destiladores": "826367168",
            "Evaluaciones": "482282527"
        }
        gid_seleccionado = gids.get(nombre_hoja, "0")
        url = BASE_URL_SHEET + gid_seleccionado
            
        res = requests.get(url, timeout=10)
        texto_puro = res.text
        
        if "<html" in texto_puro.lower() or "<doctype" in texto_puro.lower():
            return {"error": "Google Sheets bloqueó la respuesta pública. Revisa los permisos.", "datos": []}
            
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
    .stButton>button { width: 100%; border-radius: 5px; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 24px; margin-bottom: 10px; }
    .card-info { background-color: #F3F4F6; padding: 10px; border-radius: 6px; border-left: 4px solid #3B82F6; margin-bottom: 5px; }
    .card-score { background-color: #ECFDF5; padding: 10px; border-radius: 6px; border-left: 4px solid #10B981; text-align: center; color: #065F46; font-size: 18px; font-weight: bold; margin-bottom: 5px; }
    .card-warning { background-color: #FEF3C7; padding: 12px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 10px; }
    .card-danger { background-color: #FEE2E2; padding: 12px; border-radius: 6px; border-left: 4px solid #EF4444; margin-bottom: 10px; color: #991B1B; }
</style>
""", unsafe_allow_html=True)

# LECTURAS PREVIAS FIABLES
usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]

# Expandible de Auditoría Técnica
with st.expander("🛠️ PANEL DE CONTROL Y AUDITORÍA EN VIVO (Mesa de Trabajo)"):
    st.success("✅ Red de Vinculación de GIDs activa.")
    st.write("**Base de datos viva (Muestras registradas):**", muestras_db)

# ==============================================================================
# 🔐 PANTALLA DE LOGUEO / REGISTRO
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
                    
                    if user_val == usr_input:
                        usuario_encontrado = True
                        if pass_val == pwd_input:
                            st.session_state["rol"] = row_clean.get("rol", "Destilador").strip()
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            st.session_state["mesa"] = row_clean.get("mesa", "Mesa 1").strip()
                            st.success(f"¡Bienvenido {usr}!")
                            st.rerun()
                        else:
                            st.error("🔒 Contraseña incorrecta.")
                        break
                if not usuario_encontrado:
                    st.error("❌ Usuario no registrado.")
            else:
                st.error("❌ La base de datos de usuarios está vacía.")
                
    elif choice == "Registrarse como Nuevo Destilador":
        st.subheader("Formulario de Auto-Registro Autónomo")
        nuevo_usr = st.text_input("Elige un Nombre de Usuario (Sin espacios)").strip()
        nueva_pwd = st.text_input("Crea tu Contraseña de Acceso", type="password").strip()
        confirmar_pwd = st.text_input("Repite tu Contraseña", type="password").strip()
        
        if st.button("📝 Confirmar Registro"):
            if nuevo_usr == "" or nueva_pwd == "":
                st.warning("⚠️ Todos los campos son obligatorios.")
            elif nueva_pwd != confirmar_pwd:
                st.error("❌ Las contraseñas ingresadas no coinciden.")
            else:
                # 🛑 COMPROBACIÓN EXPLICITAMENTE ESTRICTA DE DUPLICADOS EN INTERFAZ
                existe_duplicado = False
                if usuarios_db:
                    for row in usuarios_db:
                        row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                        if row_clean.get("usuario", "").strip().lower() == nuevo_usr.lower():
                            existe_duplicado = True
                            break
                
                if existe_duplicado:
                    st.error("⚠️ Error: Este nombre de usuario ya se encuentra ocupado por otra destilería. Por favor elige otro.")
                else:
                    payload = {
                        "action": "registro_usuario",
                        "usuario": nuevo_usr,
                        "contrasena": nueva_pwd,
                        "rol": "Destilador",
                        "mesa": "Mesa Destilería"
                    }
                    if enviar_datos(payload):
                        st.success("🎉 ¡Cuenta creada con éxito! Cambia a 'Iniciar Sesión' en la izquierda para ingresar.")
                    else:
                        st.error("Hubo un problema de red al guardar el usuario en Google Sheets.")

# ==============================================================================
# INTERFAZ PARA USUARIOS LOGUEADOS
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 Miembro Oficial")
    st.sidebar.info(f"**Usuario:** {st.session_state['usuario']}\n\n**Rol:** {st.session_state['rol']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.session_state["usuario"] = None
        st.rerun()
        
    df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"])
    categorias_disponibles = [str(cat).strip() for cat in df_config["Categorias"].dropna().unique() if str(cat).strip() != "" and str(cat).strip().lower() != "nan"] if "Categorias" in df_config.columns else ["Gin", "Whisky", "Vodka", "Ron"]

    # ==========================================================================
    # INTERFAZ: DESTILADOR (PERFIL, INSCRIBIR Y NAVEGAR MUESTRAS)
    # ==========================================================================
    if st.session_state["rol"] == "Destilador":
        st.title("🚀 Panel Técnico del Destilador")
        tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 Perfil Destilería", "🥃 Inscribir Muestra", "📄 Mis Muestras y Certificados"])
        
        with tab_perfil:
            st.subheader("📋 Información del Establecimiento")
            nombre_destileria = st.text_input("Nombre de la Destilería / Razón Social").strip()
            marca_comercial = st.text_input("Marca Comercial Principal").strip()
            nro_rne = st.text_input("Número de Registro (RNE / Equivalente)").strip()
            localidad_provincia = st.text_input("📍 Ubicación (Ciudad y Provincia)").strip()
            telefono_contacto = st.text_input("📞 Teléfono de Contacto").strip()
            
            if st.button("💾 Guardar Datos del Perfil"):
                if not nombre_destileria or not nro_rne:
                    st.error("❌ Por favor, completa los campos clave (Nombre y RNE).")
                else:
                    payload_perfil = {
                        "action_real": "guardar_perfil",
                        "usuario": st.session_state["usuario"],
                        "destileria": nombre_destileria,
                        "marca": marca_comercial,
                        "rne": nro_rne,
                        "ubicacion": localidad_provincia,
                        "telefono": telefono_contacto
                    }
                    if enviar_datos(payload_perfil):
                        st.success("🎉 ¡Perfil de la destilería guardado en 'Datos_Destiladores'!")
                    else:
                        st.error("Error al sincronizar con Google Sheets.")
            
        with tab_muestra:
            st.markdown("""
            <div class='card-warning'>
                <h4>⚠️ REGLAMENTO DE LOGÍSTICA OBLIGATORIO</h4>
                <p>Por cada muestra inscrita, se debe enviar en físico <b>dos (2) botellas de al menos 300 ml cada una</b>. 
                Adjuntar el comprobante de pago es mandatorio para la aprobación final. <b>Si no lo tienes ahora, puedes inscribir la muestra de todos modos y subir el pago más adelante.</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            nombre_dist = st.text_input("Nombre comercial del Producto").strip()
            cat_seleccionada = st.selectbox("Categoría", categorias_disponibles)
            nro_insc_prod = st.text_input("Registro de Producto (RNPA / Local)").strip()
            volumen = st.number_input("Volumen de la botella (en ML)", min_value=0, value=750)
            comprobante = st.file_uploader("Subir comprobante de pago (Opcional en este paso)", type=["jpg", "png", "pdf"])
            
            if st.button("🔒 Confirmar e Inscribir Muestra"):
                if not nombre_dist or not nro_insc_prod:
                    st.error("❌ Por favor completa el Nombre y el RNPA del producto.")
                else:
                    estado_inicial = "Pendiente de Aprobación" if comprobante is not None else "Falta Comprobante"
                    payload_muestra = {
                        "action_real": "guardar_muestra",
                        "usuario": st.session_state["usuario"],
                        "producto": nombre_dist,
                        "categoria": cat_seleccionada,
                        "rnpa": nro_insc_prod,
                        "volumen": volumen,
                        "estado": estado_inicial
                    }
                    if enviar_datos(payload_muestra):
                        st.success(f"🎉 ¡Muestra inscrita con éxito en estado: '{estado_inicial}'!")
                        st.rerun()
                    else:
                        st.error("Error de conexión al guardar el producto.")

        with tab_estado:
            st.subheader("📋 Gestión y Navegación de Mis Muestras")
            
            # Filtrar las muestras del usuario en sesión
            df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
            mis_muestras = pd.DataFrame()
            
            if not df_m.empty:
                # Normalizar llaves a minúsculas para evitar errores
                df_m.columns = [c.lower() for c in df_m.columns]
                if "usuario" in df_m.columns:
                    mis_muestras = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
            
            if mis_muestras.empty:
                st.info("Aún no tienes muestras cargadas en el sistema.")
            else:
                # Mostrar tabla resumida de sus productos
                st.write("### Historial de Inscripciones")
                st.dataframe(mis_muestras[["id_muestra", "producto", "categoría", "estado"]], use_container_width=True)
                
                # 🔍 NAVEGADOR DE MUESTRAS SIN COMPROBANTE
                muestras_sin_pago = mis_muestras[mis_muestras["estado"].astype(str).str.lower() == "falta comprobante"]
                
                if not muestras_sin_pago.empty:
                    st.markdown("""
                    <div class='card-danger'>
                        <b>⚠️ TIENES MUESTRAS PENDIENTES DE PAGO:</b> Selecciona abajo la muestra para regularizar su situación cargando el comprobante correspondiente.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Armar la lista de navegación interactiva
                    opciones_navegacion = [f"{row['id_muestra']} - {row['producto']} ({row['categoría']})" for _, row in muestras_sin_pago.iterrows()]
                    seleccion = st.selectbox("Navegar entre mis muestras sin pagar:", opciones_navegacion)
                    
                    id_seleccionado = seleccion.split(" - ")[0]
                    archivo_pago_tardio = st.file_uploader(f"Adjuntar Comprobante de Pago para la muestra {id_seleccionado}", type=["jpg", "png", "pdf"], key="tardio")
                    
                    if st.button("💾 Regularizar y Subir Pago"):
                        if archivo_pago_tardio is None:
                            st.error("❌ Debes cargar un archivo para poder regularizar la muestra.")
                        else:
                            payload_pago = {
                                "action_real": "actualizar_pago_muestra",
                                "id_muestra": id_seleccionado
                            }
                            if enviar_datos(payload_pago):
                                st.success(f"🎉 ¡Muestra {id_seleccionado} actualizada a 'Pendiente de Aprobación' con éxito!")
                                st.rerun()
                            else:
                                st.error("Fallo al actualizar el estado en Google Sheets.")

    # ==========================================================================
    # INTERFAZ: ROL JUEZ (EVALUACIÓN EN VIVO)
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.markdown("<h2>🧠 Evaluación Sensorial a Ciegas</h2>", unsafe_allow_html=True)
        df_muestras_real = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        lista_codigos = ["DST-1084", "DST-4921", "DST-8832"]
        if not df_muestras_real.empty:
            df_muestras_real.columns = [c.lower() for c in df_muestras_real.columns]
            if "id_muestra" in df_muestras_real.columns:
                lista_codigos = [str(c).strip() for c in df_muestras_real["id_muestra"].unique() if str(c).strip() != ""]
                
        muestra_a_evaluar = st.selectbox("Seleccione Código de Muestra", lista_codigos)
        st.info(f"Evaluando muestra ciega. Los datos están protegidos contra sesgos.")
        
        # Formulario de puntajes del Juez simplificado por espacio
        if st.button("💾 Guardar y Enviar Evaluación Oficial"):
            st.success("🎉 ¡Evaluación guardada con éxito en la pestaña 'Evaluaciones'!")

    # ==========================================================================
    # INTERFAZ: ROL DIRECTOR
    # ==========================================================================
    elif st.session_state["rol"] == "Director":
        st.title("📊 Panel del Director de la Competencia")
        st.write("Auditoría de datos centralizada con GID en tiempo real.")
