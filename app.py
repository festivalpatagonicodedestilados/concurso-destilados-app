import streamlit as st
import pandas as pd
import requests
import io
import base64
import mimetypes

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES CON GOOGLE SHEETS & DRIVE
# ==============================================================================
# ✅ URL de tu última implementación de Apps Script actualizada con éxito:
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxUj67JHjqpIjtbV3mxtz4QBRSH9Mu31Bcls9OuH2nllncpIq-6mvvH4sxEO_3ao2faIw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

def enviar_datos(datos, archivo=None):
    """ Envía datos normales por POST, o un JSON estructurado con binario si hay archivo """
    try:
        if archivo is not None:
            file_bytes = archivo.getvalue()
            encoded = base64.b64encode(file_bytes).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(archivo.name)
            if not mime_type:
                mime_type = "application/octet-stream"
                
            payload_completo = datos.copy()
            payload_completo["archivo_base64"] = encoded
            payload_completo["archivo_nombre"] = archivo.name
            payload_completo["archivo_mime"] = mime_type
            
            response = requests.post(URL_SCRIPT, json=payload_completo)
        else:
            response = requests.post(URL_SCRIPT, data=datos)
            
        if "OK" in response.text or response.status_code == 200:
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

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1E3A8A; color: white; font-weight: bold; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 26px; text-align: center; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
    .card-danger { background-color: #FEE2E2; padding: 12px; border-radius: 6px; border-left: 4px solid #EF4444; margin-bottom: 10px; color: #991B1B; }
</style>
""", unsafe_allow_html=True)

usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

categorias_disponibles = [str(x).strip() for x in df_config["Categorias"].dropna().unique() if str(x).strip() != ""] if not df_config.empty and "Categorias" in df_config.columns else ["Gin", "Whisky", "Vodka", "Ron"]

# ==============================================================================
# 🔐 PANTALLA DE ACCESO
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Portal Oficial de Inscripciones - Concurso Destilados</h1>", unsafe_allow_html=True)
    menu = ["Iniciar Sesión", "Registrarse como Nuevo Destilador"]
    choice = st.sidebar.selectbox("Navegación", menu)
    
    if choice == "Iniciar Sesión":
        st.subheader("Acceso Destiladores")
        usr = st.text_input("Nombre de Usuario").strip()
        pwd = st.text_input("Contraseña", type="password").strip()
        if st.button("🚀 Ingresar al Portal"):
            if usuarios_db:
                usr_input = str(usr).strip().lower()
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "").strip().lower() == usr_input:
                        if row_clean.get("contrasena", "").split('.')[0] == str(pwd).strip():
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            st.rerun()
            st.error("Credenciales inválidas.")
    elif choice == "Registrarse como Nuevo Destilador":
        st.subheader("Formulario de Alta de Destilería")
        nuevo_usr = st.text_input("Usuario (Minúsculas, sin espacios)").strip().lower()
        nueva_pwd = st.text_input("Contraseña", type="password").strip()
        if st.button("📝 Confirmar Registro"):
            if nuevo_usr and nueva_pwd:
                if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.success("🎉 ¡Cuenta creada con éxito! Ya puedes iniciar sesión.")

# ==============================================================================
# 🚀 PANEL ACTIVO DEL DESTILADOR
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

    st.title("🚀 Panel Técnico de Gestión")
    tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 1. Perfil Destilería", "🥃 2. Inscribir Muestra", "📄 3. Estado de Mis Muestras"])
    
    with tab_perfil:
        st.subheader("📋 Información de Contacto y Establecimiento")
        n_resp = st.text_input("Nombre del Destilador / Responsable Técnico", key="p_resp").strip()
        c_resp = st.text_input("Correo Electrónico Oficial", key="p_corr").strip()
        n_dest = st.text_input("Nombre de la Destilería / Razón Social", key="p_dest").strip()
        m_com = st.text_input("Marca Comercial Principal", key="p_marc").strip()
        n_rne = st.text_input("Número de Registro (RNE / Equivalente)", key="p_rne").strip()
        u_loc = st.text_input("📍 Ubicación (Ciudad y Provincia)", key="p_ub").strip()
        t_tel = st.text_input("📞 Teléfono de Contacto (WhatsApp)", key="p_tel").strip()
        
        if st.button("💾 Guardar / Actualizar Datos del Perfil"):
            if not n_dest or not n_rne or not n_resp or not c_resp:
                st.error("❌ Los campos Responsable, Correo, Destilería y RNE son obligatorios.")
            else:
                payload = {"action_real": "guardar_perfil", "usuario": st.session_state["usuario"], "responsable": n_resp, "correo": c_resp, "destileria": n_dest, "marca": m_com, "rne": n_rne, "ubicacion": u_loc, "telefono": t_tel}
                if enviar_datos(payload):
                    st.success("🎉 ¡Perfil guardado con éxito en la base central!")
                else:
                    st.error("Error de comunicación.")
                
    with tab_muestra:
        st.markdown("<div class='card-warning'><h4>⚠️ BASES LOGÍSTICAS</h4>Enviar físicamente dos (2) botellas por muestra. Sube el comprobante de pago abajo; se guardará de forma automática y permanente en nuestro Google Drive centralizado.</div>", unsafe_allow_html=True)
        p_nom = st.text_input("Nombre Comercial del Producto", key="m_prod").strip()
        p_cat = st.selectbox("Categoría del Producto", categorias_disponibles, key="m_cat")
        p_rnpa = st.text_input("Registro de Producto (RNPA)", key="m_rnpa").strip()
        
        comprobante_file = st.file_uploader("📂 Arrastra aquí el Comprobante (JPG, PNG o PDF)", type=["jpg", "png", "pdf"], key="comprobante_nuevo")
        
        if st.button("🔒 Confirmar e Inscribir Producto"):
            if not p_nom or not p_rnpa:
                st.error("❌ Por favor completa el Nombre y el RNPA del producto.")
            else:
                with st.spinner("Subiendo comprobante a Google Drive y registrando muestra..."):
                    payload_muestra = {
                        "action_real": "guardar_muestra",
                        "usuario": st.session_state["usuario"],
                        "producto": p_nom,
                        "categoria": p_cat,
                        "rnpa": p_rnpa,
                        "volumen": 750
                    }
                    if enviar_datos(payload_muestra, archivo=comprobante_file):
                        st.success("🎉 ¡Muestra guardada e imagen archivada de forma segura en tu Drive!")
                        st.rerun()
                    else:
                        st.error("Fallo al subir el archivo o conectar con el servidor.")

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
                
                muestras_sin_pago = mis_m[mis_m["estado"].astype(str).str.lower() == "falta comprobante"]
                if not muestras_sin_pago.empty:
                    st.markdown("<div class='card-danger'><b>⚠️ ADJUNTAR COMPROBANTE PENDIENTE:</b> Selecciona el producto abajo.</div>", unsafe_allow_html=True)
                    opciones = [f"{row['id_muestra']} - {row['producto']}" for _, row in muestras_sin_pago.iterrows()]
                    seleccion = st.selectbox("Producto a regularizar:", opciones, key="sel_reg")
                    id_sel = seleccion.split(" - ")[0]
                    archivo_tardio = st.file_uploader("Cargar comprobante pendiente", type=["jpg","png","pdf"], key="tardio_file")
                    
                    if st.button("💾 Subir Comprobante Pendiente"):
                        if archivo_tardio is not None:
                            with st.spinner("Subiendo a Drive..."):
                                if enviar_datos({"action_real": "actualizar_pago_muestra", "id_muestra": id_sel}, archivo=archivo_tardio):
                                    st.success(f"🎉 Muestra {id_sel} regularizada con éxito.")
                                    st.rerun()
