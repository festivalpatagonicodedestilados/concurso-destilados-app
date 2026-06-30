import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES CON GOOGLE SHEETS
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxUj67JHjqpIjtbV3mxtz4QBRSH9Mu31Bcls9OuH2nllncpIq-6mvvH4sxEO_3ao2faIw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="
NUMERO_WHATSAPP = "5491123456789"  # 📱 REEMPLAZA CON TU NÚMERO (Formato internacional, sin el + ni espacios)

def enviar_datos(datos):
    """ Envía los datos de forma tradicional (Form/Data) a Google Sheets """
    try:
        response = requests.post(URL_SCRIPT, data=datos, timeout=25)
        if "OK" in response.text:
            return True
        return False
    except Exception as e:
        st.error(f"Error de red central: {str(e)}")
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
# 🥃 INTERFAZ Y ESTILOS VISUALES
# ==============================================================================
st.set_page_config(page_title="Inscripciones - Concurso Destilados", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

# Variables de control para los carteles de confirmación (Modals)
if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False
if "mostrar_confirmacion_muestra" not in st.session_state:
    st.session_state["mostrar_confirmacion_muestra"] = False
if "info_muestra_creada" not in st.session_state:
    st.session_state["info_muestra_creada"] = {}

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1E3A8A; color: white; font-weight: bold; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 26px; text-align: center; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
    .card-danger { background-color: #FEE2E2; padding: 12px; border-radius: 6px; border-left: 4px solid #EF4444; margin-bottom: 10px; color: #991B1B; }
    .success-box { background-color: #D1FAE5; padding: 20px; border-radius: 8px; border: 2px solid #10B981; color: #065F46; text-align: center; margin-bottom: 20px; }
    .whatsapp-btn { background-color: #25D366; color: white !important; font-weight: bold; padding: 12px; border-radius: 6px; text-align: center; text-decoration: none; display: inline-block; margin-top: 10px; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
destiladores_db = leer_hoja("Datos_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

categorias_disponibles = [str(x).strip() for x in df_config["Categorias"].dropna().unique() if str(x).strip() != ""] if not df_config.empty and "Categorias" in df_config.columns else ["Gin", "Whisky", "Vodka", "Ron"]

# ==============================================================================
# 🔐 PANTALLA DE ACCESO (DISEÑO EN PESTAÑAS CENTRALES)
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Portal Oficial de Inscripciones</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Concurso Nacional de Destilados - Gestión de Muestras</p>", unsafe_allow_html=True)
    
    # Mostrar cartel de confirmación de registro si corresponde
    if st.session_state["mostrar_confirmacion_registro"]:
        st.markdown("""
        <div class='success-box'>
            <h3>🎉 ¡Cuenta Creada de Forma Exitosa!</h3>
            <p>Tu usuario ha sido registrado en la base central. Ya puedes pasar a la pestaña de <b>Iniciar Sesión</b> con tus credenciales.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👍 Entendido"):
            st.session_state["mostrar_confirmacion_registro"] = False
            st.rerun()

    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse como Nuevo Destilador"])
    
    with tab_login:
        st.markdown("### Acceso al Panel de Control")
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
            st.error("❌ Credenciales inválidas o usuario no registrado.")
            
    with tab_registro:
        st.markdown("### Formulario de Alta de Destilería")
        nuevo_usr = st.text_input("Elige tu Nombre de Usuario (Minúsculas, sin espacios)", key="reg_user").strip().lower()
        nueva_pwd = st.text_input("Elige tu Contraseña de Acceso", type="password", key="reg_pass").strip()
        
        if st.button("✨ Confirmar y Crear Cuenta", key="btn_registro"):
            if not nuevo_usr or not nueva_pwd:
                st.error("❌ Todos los campos son obligatorios.")
            elif " " in nuevo_usr:
                st.error("❌ El nombre de usuario no puede contener espacios en blanco.")
            elif usuarios_db and any(str(r.get("usuario","")).lower() == nuevo_usr for r in usuarios_db):
                st.error("❌ Este nombre de usuario ya está tomado.")
            else:
                with st.spinner("Creando cuenta..."):
                    if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                        st.session_state["mostrar_confirmacion_registro"] = True
                        st.rerun()
                    else:
                        st.error("❌ Error de comunicación con el servidor al registrar.")

# ==============================================================================
# 🚀 PANEL ACTIVO DEL DESTILADOR (LOGUEADO)
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

    st.title("🚀 Panel Técnico de Gestión")
    
    # Pop-up de confirmación de muestra agregada con botón de WhatsApp directo
    if st.session_state["mostrar_confirmacion_muestra"]:
        info = st.session_state["info_muestra_creada"]
        texto_wa = f"Hola! Registré la muestra {info['producto']} ({info['categoria']}) en el portal. Adjunto el comprobante de pago."
        texto_encoded = urllib.parse.quote(texto_wa)
        url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={texto_encoded}"
        
        st.markdown(f"""
        <div class='success-box'>
            <h2>🎉 ¡Muestra Registrada Exitosamente!</h2>
            <p style='font-size: 16px;'>Tu muestra ha ingresado a la base de datos central de forma segura.</p>
            <hr style='border: 1px solid #10B981;'>
            <p style='font-weight: bold;'>⚠️ PASO FINAL OBLIGATORIO:</p>
            <p>Para validar tu inscripción, haz clic en el siguiente botón para enviar el comprobante de pago directamente al Director del Concurso por WhatsApp:</p>
            <a href='{url_wa}' target='_blank' class='whatsapp-btn'>📱 Enviar Comprobante por WhatsApp</a>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ Ya envié el comprobante / Cerrar"):
            st.session_state["mostrar_confirmacion_muestra"] = False
            st.session_state["info_muestra_creada"] = {}
            st.rerun()

    tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 1. Perfil Destilería", "🥃 2. Inscribir Muestra", "📄 3. Estado de Mis Muestras"])
    
    perfil_existente = {}
    if destiladores_db:
        for row in destiladores_db:
            if str(row.get("usuario", "")).lower() == st.session_state["usuario"].lower():
                perfil_existente = row
                break

    # --------------------------------------------------------------------------
    # TAB 1: PERFIL DESTILERÍA
    # --------------------------------------------------------------------------
    with tab_perfil:
        st.subheader("📋 Información de Contacto y Establecimiento")
        if perfil_existente:
            st.info("💡 Tus datos ya están registrados. Puedes actualizarlos si lo deseas.")
            
        n_resp = st.text_input("Nombre del Destilador / Responsable Técnico", value=str(perfil_existente.get("responsable", "")), key="p_resp").strip()
        c_resp = st.text_input("Correo Electrónico Oficial", value=str(perfil_existente.get("correo", "")), key="p_corr").strip()
        n_dest = st.text_input("Nombre de la Destilería / Razón Social", value=str(perfil_existente.get("destileria", "")), key="p_dest").strip()
        m_com = st.text_input("Marca Comercial Principal", value=str(perfil_existente.get("marca", "")), key="p_marc").strip()
        n_rne = st.text_input("Número de Registro (RNE / Equivalente)", value=str(perfil_existente.get("rne", "")), key="p_rne").strip()
        u_loc = st.text_input("📍 Ubicación (Ciudad y Provincia)", value=str(perfil_existente.get("ubicacion", "")), key="p_ub").strip()
        t_tel = st.text_input("📞 Teléfono de Contacto (WhatsApp)", value=str(perfil_existente.get("telefono", "")), key="p_tel").strip()
        
        if st.button("💾 Guardar / Actualizar Datos del Perfil"):
            if not n_dest or not n_rne or not n_resp or not c_resp:
                st.error("❌ Los campos Responsable, Correo, Destilería y RNE son obligatorios.")
            else:
                payload = {
                    "action_real": "guardar_perfil", 
                    "usuario": st.session_state["usuario"], 
                    "responsable": n_resp, 
                    "correo": c_resp, 
                    "destileria": n_dest, 
                    "marca": m_com, 
                    "rne": n_rne, 
                    "ubicacion": u_loc, 
                    "telefono": t_tel
                }
                if enviar_datos(payload):
                    st.success("🎉 ¡Perfil guardado con éxito!")
                    st.rerun()
                else:
                    st.error("Error al guardar perfil.")
                
    # --------------------------------------------------------------------------
    # TAB 2: INSCRIBIR MUESTRA
    # --------------------------------------------------------------------------
    with tab_muestra:
        # Texto corregido con tus bases y requerimientos exactos
        st.markdown("""
        <div class='card-warning'>
            <h4>⚠️ BASES LOGÍSTICAS</h4>
            Enviar físicamente dos (2) botellas por muestra (o más para llegar al mínimo de 600 ml). 
            Sube los datos de la muestra abajo. Al finalizar el registro, se te habilitará un botón para enviar la captura del comprobante directamente por WhatsApp.
        </div>
        """, unsafe_allow_html=True)
        
        p_nom = st.text_input("Nombre Comercial del Producto (Ej: Gin London Dry Serrano)", key="m_prod").strip()
        p_cat = st.selectbox("Categoría del Producto", categorias_disponibles, key="m_cat")
        p_rnpa = st.text_input("Registro de Producto (RNPA / Trámite)", key="m_rnpa").strip()
        p_vol = st.number_input("Volumen de la botella (en ml)", min_value=50, max_value=5000, value=750, step=50, key="m_vol")
        
        if st.button("🔒 Confirmar e Inscribir Producto"):
            if not p_nom or not p_rnpa:
                st.error("❌ Por favor completa el Nombre y el RNPA del producto.")
            else:
                with st.spinner("Registrando muestra en la base central..."):
                    payload_muestra = {
                        "action_real": "guardar_muestra",
                        "usuario": st.session_state["usuario"],
                        "producto": p_nom,
                        "categoria": p_cat,
                        "rnpa": p_rnpa,
                        "volumen": str(p_vol)
                    }
                    if enviar_datos(payload_muestra):
                        # Guardamos la info temporalmente para armar el botón de WhatsApp dinámico
                        st.session_state["info_muestra_creada"] = {
                            "producto": p_nom,
                            "categoria": p_cat
                        }
                        st.session_state["mostrar_confirmacion_muestra"] = True
                        st.rerun()
                    else:
                        st.error("Fallo al conectar con el servidor.")

    # --------------------------------------------------------------------------
    # TAB 3: ESTADO DE MIS MUESTRAS
    # --------------------------------------------------------------------------
    with tab_estado:
        st.subheader("📄 Historial e Inscripciones Realizadas")
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        if not df_m.empty:
            df_m.columns = [c.lower() for c in df_m.columns]
            mis_m = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
            
            if mis_m.empty:
                st.info("No registraste productos aún.")
            else:
                cols_seguras = ["id_muestra", "producto", "categoría", "estado", "fecha"]
                cols_presentes = [c for c in cols_seguras if c in mis_m.columns]
                
                df_limpio_vista = mis_m[cols_presentes].copy()
                df_limpio_vista["estado"] = df_limpio_vista["estado"].apply(lambda x: str(x).split(" (")[0])
                st.dataframe(df_limpio_vista, use_container_width=True)
