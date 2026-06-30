import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import io
import json

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES REALES CON GOOGLE SHEETS
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbziw6YYHEJ_d7nLBuigxNidoRzmePytvhxWR5gIpPZLYAibkf179ae9IHjOKvORUAGlQw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="

def enviar_datos(datos):
    try:
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
            "Datos_Destiladores": "826367168",
            "Evaluaciones": "482282527"
        }
        gid_seleccionado = gids.get(nombre_hoja, "0")
        url = BASE_URL_SHEET + gid_seleccionado
            
        res = requests.get(url, timeout=10)
        texto_puro = res.text
        
        if "<html" in texto_puro.lower() or "<doctype" in texto_puro.lower():
            return {"error": "Permisos insuficientes en Sheets.", "datos": []}
            
        df = pd.read_csv(io.StringIO(texto_puro))
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return {"error": None, "datos": df.to_dict(orient="records"), "columnas": list(df.columns)}
    except Exception as e:
        return {"error": str(e), "datos": [], "columnas": []}

# ==============================================================================
# 🥃 INTERFAZ Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Sistema Integral de Catas", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None
    st.session_state["mesa"] = "Mesa 1"

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 24px; margin-bottom: 10px; }
    .card-info { background-color: #F3F4F6; padding: 10px; border-radius: 6px; border-left: 4px solid #3B82F6; margin-bottom: 5px; }
    .card-warning { background-color: #FEF3C7; padding: 12px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 10px; }
    .card-danger { background-color: #FEE2E2; padding: 12px; border-radius: 6px; border-left: 4px solid #EF4444; margin-bottom: 10px; color: #991B1B; }
</style>
""", unsafe_allow_html=True)

usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

categorias_disponibles = []
mapa_abreviaturas = {}
if not df_config.empty and "Categorias" in df_config.columns:
    df_c_clean = df_config.dropna(subset=["Categorias"])
    categorias_disponibles = [str(x).strip() for x in df_c_clean["Categorias"].unique() if str(x).strip() != ""]
    if "Abreviatura" in df_c_clean.columns:
        for _, fila in df_c_clean.iterrows():
            cat_nom = str(fila["Categorias"]).strip()
            abrev = str(fila["Abreviatura"]).strip() if pd.notna(fila["Abreviatura"]) else cat_nom[:3].upper()
            mapa_abreviaturas[cat_nom] = abrev
else:
    categorias_disponibles = ["Gin", "Whisky", "Vodka", "Ron"]
    mapa_abreviaturas = {"Gin": "GIN", "Whisky": "WHI", "Vodka": "VOD", "Ron": "RON"}

# ==============================================================================
# 🔐 PANTALLA LOGUEO / REGISTRO
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
                usr_input = str(usr).strip().lower()
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "").strip().lower() == usr_input:
                        if row_clean.get("contrasena", "").split('.')[0] == str(pwd).strip():
                            st.session_state["rol"] = row_clean.get("rol", "Destilador").strip()
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            st.session_state["mesa"] = row_clean.get("mesa", "Mesa 1").strip()
                            st.rerun()
            st.error("Credenciales inválidas.")
    elif choice == "Registrarse como Nuevo Destilador":
        st.subheader("Formulario de Auto-Registro")
        nuevo_usr = st.text_input("Usuario").strip()
        nueva_pwd = st.text_input("Contraseña", type="password").strip()
        if st.button("📝 Confirmar Registro"):
            if usuarios_db and any(str(r.get("usuario","")).lower() == nuevo_usr.lower() for r in usuarios_db):
                st.error("Este nombre de usuario ya se encuentra ocupado.")
            else:
                if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.success("¡Cuenta creada! Cambia a 'Iniciar Sesión' para ingresar.")

# ==============================================================================
# NÚCLEO DE INTERFACES LOGUEADAS
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']} ({st.session_state['rol']})")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

    # ==========================================================================
    # --- INTERFAZ: DESTILADOR ---
    # ==========================================================================
    if st.session_state["rol"] == "Destilador":
        st.title("🚀 Panel del Destilador")
        tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 Perfil Destilería", "🥃 Inscribir Muestra", "📄 Mis Muestras y Certificados"])
        
        with tab_perfil:
            st.subheader("📋 Información del Establecimiento y Responsables")
            n_resp = st.text_input("Nombre del Destilador / Responsable Técnico", key="prof_resp").strip()
            c_resp = st.text_input("Correo Electrónico Oficial", key="prof_corr").strip()
            n_dest = st.text_input("Nombre de la Destilería / Razón Social", key="prof_dest").strip()
            m_com = st.text_input("Marca Comercial Principal", key="prof_marc").strip()
            n_rne = st.text_input("Número de Registro (RNE / Equivalente)", key="prof_rne").strip()
            u_loc = st.text_input("📍 Ubicación (Ciudad y Provincia)", key="prof_ub").strip()
            t_tel = st.text_input("📞 Teléfono de Contacto (WhatsApp)", key="prof_tel").strip()
            
            if st.button("💾 Guardar Datos del Perfil"):
                if not n_dest or not n_rne or not n_resp or not c_resp:
                    st.error("❌ Por favor, completa los campos obligatorios (Responsable, Correo, Destilería y RNE).")
                else:
                    payload_perfil = {
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
                    if enviar_datos(payload_perfil):
                        st.success("🎉 ¡Perfil guardado con éxito en la base central!")
                    else:
                        st.error("Error al sincronizar con Google Sheets.")
                    
        with tab_muestra:
            st.markdown("<div class='card-warning'><h4>⚠️ REGLAMENTO OBLIGATORIO</h4>Por cada muestra, enviar dos (2) botellas de al menos 300 ml. El comprobante físico se valida en la recepción; puedes pre-registrar la muestra aquí para reservar su lugar. Su código ciego se mantendrá estrictamente oculto.</div>", unsafe_allow_html=True)
            p_nom = st.text_input("Nombre del Producto", key="m_prod").strip()
            p_cat = st.selectbox("Categoría", categorias_disponibles, key="m_cat")
            p_rnpa = st.text_input("RNPA / Registro de Producto", key="m_rnpa").strip()
            
            # Reemplazo seguro: Declaración jurada de pago para evitar la traba del binario pesado en Sheets
            marcar_pago = st.checkbox("Confirmar que ya realicé el pago de arancel correspondiente")
            
            if st.button("🔒 Confirmar e Inscribir Muestra"):
                if not p_nom or not p_rnpa:
                    st.error("❌ Por favor completa el Nombre y el RNPA del producto.")
                else:
                    est = "Pendiente de Aprobación" if marcar_pago else "Falta Comprobante"
                    payload_muestra = {
                        "action_real": "guardar_muestra",
                        "usuario": st.session_state["usuario"],
                        "producto": p_nom,
                        "categoria": p_cat,
                        "rnpa": p_rnpa,
                        "volumen": 750,
                        "estado": est
                    }
                    if enviar_datos(payload_muestra):
                        st.success(f"🎉 ¡Muestra guardada con éxito en estado: '{est}'!")
                        st.rerun()

        with tab_estado:
            st.subheader("📋 Gestión y Estado de Mis Muestras")
            df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
            if not df_m.empty:
                df_m.columns = [c.lower() for c in df_m.columns]
                mis_m = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
                
                if mis_m.empty:
                    st.info("Aún no tienes muestras cargadas.")
                else:
                    cols_seguras = ["id_muestra", "producto", "categoría", "estado", "fecha"]
                    cols_presentes = [c for c in cols_seguras if c in mis_m.columns]
                    st.dataframe(mis_m[cols_presentes], use_container_width=True)
                    
                    muestras_sin_pago = mis_m[mis_m["estado"].astype(str).str.lower() == "falta comprobante"]
                    if not muestras_sin_pago.empty:
                        st.markdown("<div class='card-danger'><b>⚠️ TIENES MUESTRAS PENDIENTES DE PAGO:</b> Si ya realizaste la transferencia, marca la regularización abajo.</div>", unsafe_allow_html=True)
                        opciones = [f"{row['id_muestra']} - {row['producto']}" for _, row in muestras_sin_pago.iterrows()]
                        seleccion = st.selectbox("Muestra a regularizar:", opciones, key="sel_reg")
                        
                        id_sel = seleccion.split(" - ")[0]
                        if st.button("💾 Declarar Pago y Adjuntar"):
                            if enviar_datos({"action_real": "actualizar_pago_muestra", "id_muestra": id_sel}):
                                st.success(f"🎉 Muestra {id_sel} actualizada a 'Pendiente de Aprobación'.")
                                st.rerun()

    # ==========================================================================
    # --- INTERFAZ: DIRECTOR ---
    # ==========================================================================
    elif st.session_state["rol"] == "Director":
        st.title("📊 Panel del Director de la Competencia")
        st.markdown("### 🎲 Asignador Automático de Códigos de Cata Ciega")
        
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        if df_m.empty:
            st.info("No hay muestras en el sistema.")
        else:
            df_m.columns = [c.lower() for c in df_m.columns]
            col_id = "id_muestra"
            col_cat = "categoría" if "categoría" in df_m.columns else "categoria"
            col_cod = "código_muestra" if "código_muestra" in df_m.columns else "codigo_muestra"
            
            if col_cod not in df_m.columns:
                df_m[col_cod] = ""
            
            df_m[col_cod] = df_m[col_cod].fillna("").astype(str).str.strip()
            muestras_sin_codigo = df_m[df_m[col_cod] == ""]
            
            st.metric("Muestras pendientes de Código:", len(muestras_sin_codigo))
            
            st.write("**Historial completo de códigos asignados (Vista del Director):**")
            cols_vista = [col_id, "usuario", "producto", col_cat, "estado", col_cod]
            cols_vista_presentes = [c for c in cols_vista if c in df_m.columns]
            st.dataframe(df_m[cols_vista_presentes], use_container_width=True)
            
            if len(muestras_sin_codigo) > 0:
                if st.button("🎲 Generar Códigos Aleatorios Restantes", key="btn_director_gen"):
                    codigos_existentes = set(df_m[df_m[col_cod] != ""][col_cod].unique())
                    nuevos_codigos_payload = {}
                    
                    for _, fila in muestras_sin_codigo.iterrows():
                        id_m = str(fila[col_id]).strip()
                        cat_m = str(fila[col_cat]).strip()
                        prefix = mapa_abreviaturas.get(cat_m, cat_m[:3].upper())
                        
                        while True:
                            num_azar = random.randint(100, 999)
                            codigo_propuesto = f"{prefix}-{num_azar}"
                            if codigo_propuesto not in codigos_existentes and codigo_propuesto not in nuevos_codigos_payload.values():
                                nuevos_codigos_payload[id_m] = codigo_propuesto
                                break
                    
                    # Mandamos el JSON serializado limpio bajo la acción real mapeada
                    if enviar_datos({"action_real": "guardar_codigos_masivos", "codigos_json": json.dumps(nuevos_codigos_payload)}):
                        st.success(f"🎉 Códigos generados y guardados con éxito en la nube.")
                        st.rerun()
                    else:
                        st.error("Error al transmitir los nuevos códigos generados al Sheet.")
            else:
                st.success("✅ Todas las muestras cuentan con su código oficial de cata.")

    # ==========================================================================
    # --- INTERFAZ: JUEZ ---
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.title("🧠 Panel del Juez")
        st.info("Evaluación a ciegas activa y protegida.")
