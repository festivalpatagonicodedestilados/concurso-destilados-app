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
muestras_db = leer_hoja_datos = leer_hoja("Muestras_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

# Mapeo de categorías dinámicas
categorias_disponibles = []
mapa_abreviaturas = {}
if not df_config.empty and "Categorias" in df_config.columns:
    df_c_clean = df_config.dropna(subset=["Categorias"])
    categorias_disponibles = [str(x).strip() for x in df_c_clean["Categorias"].unique() if str(x).strip() != ""]
    
    # Armar mapa de abreviaturas seguro
    if "Abreviatura" in df_c_clean.columns:
        for _, fila in df_c_clean.iterrows():
            cat_nom = str(fila["Categorias"]).strip()
            abrev = str(fila["Abreviatura"]).strip() if pd.notna(fila["Abreviatura"]) else cat_nom[:3].upper()
            mapa_abreviaturas[cat_nom] = abrev
else:
    categorias_disponibles = ["Gin", "Whisky", "Vodka", "Ron"]
    mapa_abreviaturas = {"Gin": "GIN", "Whisky": "WHI", "Vodka": "VOD", "Ron": "RON"}

# ==============================================================================
# PANTALLA LOGUEO / REGISTRO (Omitida para optimizar espacio, se mantiene igual)
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
                st.error("Usuario ya ocupado.")
            else:
                if enviar_datos({"action": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.success("¡Creado! Inicia sesión.")

# ==============================================================================
# NÚCLEO DE INTERFACES LOGUEADAS
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']} ({st.session_state['rol']})")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.rerun()

    # --- INTERFAZ: DESTILADOR ---
    if st.session_state["rol"] == "Destilador":
        st.title("🚀 Panel del Destilador")
        tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 Perfil", "🥃 Inscribir Muestra", "📄 Mis Muestras"])
        
        with tab_perfil:
            st.subheader("Datos de la Empresa")
            n_resp = st.text_input("Responsable").strip()
            c_resp = st.text_input("Correo").strip()
            n_dest = st.text_input("Destilería").strip()
            n_rne = st.text_input("RNE").strip()
            if st.button("💾 Guardar Perfil"):
                if enviar_datos({"action_real":"guardar_perfil","usuario":st.session_state["usuario"],"responsable":n_resp,"correo":c_resp,"destileria":n_dest,"rne":n_rne}):
                    st.success("¡Perfil Guardado!")
                    
        with tab_muestra:
            st.markdown("<div class='card-warning'>Muestras físicas obligatorias. Comprobante opcional ahora; el código se asignará automáticamente al aprobarse.</div>", unsafe_allow_html=True)
            p_nom = st.text_input("Nombre del Producto").strip()
            p_cat = st.selectbox("Categoría", categorias_disponibles)
            p_rnpa = st.text_input("RNPA").strip()
            comprobante = st.file_uploader("Comprobante (Opcional)", type=["jpg","png","pdf"])
            if st.button("🔒 Inscribir Muestra"):
                est = "Pendiente de Aprobación" if comprobante else "Falta Comprobante"
                if enviar_datos({"action_real":"guardar_muestra","usuario":st.session_state["usuario"],"producto":p_nom,"categoria":p_cat,"rnpa":p_rnpa,"volumen":750,"estado":est}):
                    st.success("¡Muestra guardada!")
                    st.rerun()

        with tab_estado:
            st.subheader("Mis Muestras")
            df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
            if not df_m.empty:
                df_m.columns = [c.lower() for c in df_m.columns]
                mis_m = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
                cols = ["id_muestra", "producto", "categoría", "estado"]
                if "código_muestra" in mis_m.columns: cols.append("código_muestra")
                st.dataframe(mis_m[cols], use_container_width=True)

    # --- INTERFAZ: DIRECTOR (CON EL GENERADOR AUTOMÁTICO DE CÓDIGOS) ---
    elif st.session_state["rol"] == "Director":
        st.title("📊 Panel del Director de la Competencia")
        
        st.markdown("### 🎲 Asignador de Códigos de Cata Ciega")
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        if df_m.empty:
            st.info("No hay muestras cargadas en el sistema actualmente.")
        else:
            # Normalizar columnas
            columnas_originales = list(df_m.columns)
            mapa_columnas_minus = {c.lower(): c for c in columnas_originales}
            df_m.columns = [c.lower() for c in df_m.columns]
            
            # Identificar cuáles muestras no tienen Código asignado aún
            col_id = "id_muestra"
            col_cat = "categoría" if "categoría" in df_m.columns else "categoria"
            col_cod = "código_muestra" if "código_muestra" in df_m.columns else "codigo_muestra"
            
            # Asegurar que existan campos vacíos o nan
            if col_cod not in df_m.columns:
                df_m[col_cod] = ""
            
            df_m[col_cod] = df_m[col_cod].fillna("").astype(str).str.strip()
            muestras_sin_codigo = df_m[df_m[col_cod] == ""]
            
            st.metric("Muestras pendientes de Código de Cata:", len(muestras_sin_codigo))
            
            # Mostrar listado de control rápido
            st.write("**Muestras actuales y sus códigos asignados:**")
            cols_vista = [col_id, "usuario", "producto", col_cat, "estado", col_cod]
            st.dataframe(df_m[cols_vista], use_container_width=True)
            
            # 🔘 BOTÓN MAESTRO DE ASIGNACIÓN AUTOMÁTICA
            if len(muestras_sin_codigo) > 0:
                if st.button("🎲 Generar Códigos Aleatorios Restantes"):
                    codigos_existentes = set(df_m[df_m[col_cod] != ""][col_cod].unique())
                    nuevos_codigos_payload = {}
                    
                    for _, fila in muestras_sin_codigo.iterrows():
                        id_m = str(fila[col_id]).strip()
                        cat_m = str(fila[col_cat]).strip()
                        
                        # Obtener abreviatura reglamentaria
                        prefix = mapa_abreviaturas.get(cat_m, cat_m[:3].upper())
                        
                        # Bucle para garantizar que el número aleatorio de 3 dígitos no esté repetido
                        while True:
                            num_azar = random.randint(100, 999)
                            codigo_propuesto = f"{prefix}-{num_azar}"
                            if codigo_propuesto not in codigos_existentes and codigo_propuesto not in nuevos_codigos_payload.values():
                                nuevos_codigos_payload[id_m] = codigo_propuesto
                                break
                    
                    # Enviar el paquete comprimido JSON al Apps Script
                    payload_director = {
                        "action_real": "guardar_codigos_masivos",
                        "codigos_json": json.dumps(nuevos_codigos_payload)
                    }
                    
                    if enviar_datos(payload_director):
                        st.success(f"🎉 ¡Éxito! Se generaron y guardaron {len(nuevos_codigos_payload)} códigos de cata de forma aleatoria.")
                        st.rerun()
                    else:
                        st.error("Error de comunicación al guardar los códigos en el servidor.")
            else:
                st.success("✅ Todas las muestras inscriptas ya cuentan con su código oficial de cata asignado.")

    # --- INTERFAZ: JUEZ ---
    elif st.session_state["rol"] == "Juez":
        st.title("🧠 Panel del Juez")
        st.info("Cata ciega activa.")
