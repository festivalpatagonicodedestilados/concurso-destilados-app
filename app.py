import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse
import random
from datetime import datetime
import os

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES CON GOOGLE SHEETS Y SOPORTE
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbwMSnJgoyYDUBL4j1AxVqrHy7oBw65_sdcy_oNQBBik7oaowIxsgbr8AFeB69_PC5Lyew/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="
NUMERO_WHATSAPP = "5492914737608"
CBU_DOLARES = "3220001888027640440018"
ALIAS_PESOS = "festivaldestiladores"
EMAIL_ORGANIZACION = "festivalpatagonicodedestilados@gmail.com"
TITULAR_CUENTA = "Matias Miconi"

def enviar_datos(datos):
    """Envía un diccionario de datos mediante un POST Request al Google Apps Script."""
    try:
        response = requests.post(URL_SCRIPT, data=datos, timeout=25)
        if "OK" in response.text:
            return True
        return False
    except Exception as e:
        st.error(f"Error de red: {str(e)}")
        return False

def leer_hoja(nombre_hoja):
    """Lee una pestaña específica de Google Sheets exportándola como CSV."""
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

def mostrar_logo_encabezado():
    """Muestra el logo.png centrado en la parte superior si existe en el repositorio."""
    if os.path.exists("logo.png"):
        col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
        with col_l2:
            st.image("logo.png", use_container_width=True)

# ==============================================================================
# 🥃 CONFIGURACIÓN DE INTERFAZ Y ESTILOS AVANZADOS
# ==============================================================================
st.set_page_config(page_title="1° Festival de Destiladores Patagónicos", page_icon="🥃", layout="wide")

# Inicialización de variables de sesión
if "rol" not in st.session_state:
    st.session_state["rol"] = None
if "usuario" not in st.session_state:
    st.session_state["usuario"] = None
if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False
if "mostrar_confirmacion_muestra" not in st.session_state:
    st.session_state["mostrar_confirmacion_muestra"] = False
if "info_muestra_creada" not in st.session_state:
    st.session_state["info_muestra_creada"] = {}
if "muestras_notificadas" not in st.session_state:
    st.session_state["muestras_notificadas"] = set()
if "perfil_guardado_exito" not in st.session_state:
    st.session_state["perfil_guardado_exito"] = False

# Estilos CSS Personalizados
st.markdown("""
<style>
    /* Estructura general */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 5rem !important; }
    
    /* Contenedor del Banner Principal */
    .hero-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #f59e0b;
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.4);
        margin-bottom: 20px;
    }
    
    .main-header {
        color: #f59e0b;
        font-weight: 800;
        font-size: 32px;
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .sub-header {
        color: #f8fafc;
        font-size: 22px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 12px;
    }
    
    .poetic-text {
        font-style: italic;
        text-align: center;
        color: #cbd5e1;
        max-width: 800px;
        margin: 0 auto 15px auto;
        font-size: 15px;
        line-height: 1.5;
    }
    
    .date-badge {
        display: inline-block;
        text-align: center;
        font-weight: bold;
        color: #1e293b;
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        padding: 8px 18px;
        border-radius: 20px;
        font-size: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Tarjetas fijas de advertencia y pagos */
    .card-warning {
        background-color: #1e293b;
        padding: 18px;
        border-radius: 8px;
        border-left: 5px solid #f59e0b;
        margin-bottom: 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .box-pago {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #334155;
        margin-bottom: 20px;
        color: #f8fafc;
    }
    
    /* Pestañas estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #334155;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: bold;
        padding: 12px 20px;
        border-radius: 8px 8px 0 0;
        background-color: #0f172a;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e293b !important;
        color: #f59e0b !important;
        border-top: 2px solid #f59e0b;
    }

    /* Botón de WhatsApp Ultra Remarcado */
    .stLinkButton a {
        background: linear-gradient(135deg, #25d366 0%, #128c7e 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 18px !important;
        border-radius: 50px !important;
        padding: 14px 28px !important;
        border: 2px solid #34d399 !important;
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.5) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        text-align: center !important;
        display: block !important;
    }
    .stLinkButton a:hover {
        background: linear-gradient(135deg, #1fbe5c 0%, #0e6f64 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 211, 102, 0.8) !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# Lectura de la base de datos
usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
destiladores_db = leer_hoja("Datos_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

cotizacion_hoy = 1000.0

if not df_config.empty:
    columnas_originales = {c.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').strip(): c for c in df_config.columns}
    if "cotizacion" in columnas_originales:
        col_real = columnas_originales["cotizacion"]
        try:
            cotizacion_hoy = float(df_config[col_real].dropna().iloc[0])
        except:
            pass

def calcular_arancel_muestra(nro_muestra):
    """Calcula el costo en USD según la fecha actual (Lote 1, 2 o 3) y la cantidad de muestras del mismo productor."""
    hoy = datetime.now().date()
    lote = 1
    if datetime(2026, 8, 1).date() <= hoy <= datetime(2026, 8, 31).date():
        lote = 2
    elif hoy >= datetime(2026, 9, 1).date():
        lote = 3
        
    if nro_muestra <= 3:
        precios = {1: 60, 2: 70, 3: 80}
    elif 4 <= nro_muestra <= 7:
        precios = {1: 50, 2: 60, 3: 70}
    else:
        precios = {1: 45, 2: 55, 3: 65}
    return precios[lote], lote

# ==============================================================================
# 📖 DICCIONARIO DE CATEGORÍAS Y REGLAMENTO
# ==============================================================================
ACLARACIONES_CATEGORIAS = {
    "London Dry Gin": "Gin de alcohol neutro y botánicos naturales (predominio enebro). Sin saborizantes artificiales post-destilación.",
    "Dry Gin": "Gin seco con predominio de enebro. Permite ciertos ajustes posteriores de sabor y botánicos.",
    "Old Tom Gin": "Estilo tradicional ligeramente más dulce que el Dry Gin. Perfil suave y especiado.",
    "Gin de Autor": "Receta propia y distintiva del productor, utilizando botánicos particulares o métodos originales.",
    "Vodka Neutro": "Destilado de alta pureza (cereales, papa, etc.) con sabor y aroma muy suaves o casi neutros.",
    "Vodka Aromatizado": "Vodka con incorporación de sabores naturales o artificiales (frutas, especias, hierbas, vainilla).",
    "Vermut Dulce": "Vino fortificado y aromatizado con hierbas/especias, mayor contenido de azúcar y perfil dulce.",
    "Vermut Seco": "Vino aromatizado con hierbas que posee menor cantidad de azúcar y un perfil seco y herbal.",
    "Vermut de Autor": "Vermut elaborado con recetas propias y perfiles aromáticos únicos desarrollados por el productor.",
    "Single Malt": "Whisky producido en una sola destilería utilizando únicamente cebada malteada.",
    "Whisky de Grano": "Whisky elaborado con granos distintos o mezclados (maíz, trigo, centeno) y perfil más ligero.",
    "Blend": "Mezcla de distintos whiskies (maltas y/o granos) para lograr un perfil equilibrado y consistente.",
    "Ron Liviano": "Ron de cuerpo ligero, generalmente filtrado y de sabor suave. Utilizado en coctelería.",
    "Ron Pesado": "Ron de cuerpo intenso y sabor más robusto, con mayor presencia aromática y estructura.",
    "Ron Añejo": "Ron envejecido en barricas, desarrollando notas de madera, vainilla y especias.",
    "Licor Seco": "Licor con bajo contenido de azúcar y perfil menos dulce.",
    "Licor Fino": "Elaborado con materias primas seleccionadas, buscando mayor delicadeza aromática.",
    "Licor Cream": "Incorpora crema láctea u otros componentes que aportan textura cremosa.",
    "Fernet": "Licor amargo elaborado mediante maceración de hierbas, raíces y especias en alcohol.",
    "Bitter": "Bebida o concentrado de sabor amargo elaborado con hierbas, raíces y elementos botánicos.",
    "Aperitivo de Autor": "Bebida aperitiva creada con receta propia y perfil distintivo del productor.",
    "Aperitivo sin Alcohol": "Diseñado para el consumo pre-comida, con notas aromáticas tradicionales pero sin alcohol.",
    "RTD (Ready To Drink)": "Bebida lista para consumir, previamente mezclada y envasada (cócteles preparados o combinados).",
    "Brandy": "Destilado obtenido a partir de vino o jugos fermentados de frutas, generalmente envejecido.",
    "Pisco": "Destilado de uva obtenido de la destilación de vino fermentado, tradicional de la región.",
    "Grappa": "Destilado elaborado a partir del orujo de uva (pieles, semillas y restos de la vinificación).",
    "Destilados de Frutas": "Obtenidos de la fermentación y destilación de frutas distintas a la uva (manzana, pera, ciruela).",
    "Otros Destilados": "Categoría general para destilados menos comunes que no encajan en clasificaciones tradicionales."
}
categorias_disponibles = list(ACLARACIONES_CATEGORIAS.keys())

def renderizar_encabezado_oficial():
    """Renderiza la marquesina institucional oficial del evento."""
    mostrar_logo_encabezado()
    st.markdown("""
    <div class="hero-card">
        <h1 class="main-header">1° Festival de Destiladores Patagónicos</h1>
        <h2 class="sub-header">Copa Espíritu del Sur</h2>
        <p class="poetic-text">
        "El espíritu del Sur se destila aquí. Donde la pureza cristalina del agua de deshielo andino y los botánicos de nuestra cordillera florecida se funden en el bronce y cobre de los alambiques."
        </p>
        <div class="date-badge">📍 5, 6 y 7 de Diciembre | Predio Sociedad Rural de Bariloche</div>
    </div>
    """, unsafe_allow_html=True)

def renderizar_reglamento_oficial(key_prefix=""):
    """Renderiza el texto completo del Reglamento Oficial de la Copa."""
    renderizar_encabezado_oficial()
    st.markdown("---")
    
    capitulo_sel = st.selectbox("📖 Navegar por los Capítulos del Reglamento Oficial:", [
        "Sección I: Presentación y Objetivos del Certamen",
        "Sección II: Categorías de Participantes y Requisitos Legales",
        "Sección III: Cronograma Oficial y Aranceles de Inscripción",
        "Sección IV: Criterios de Envío, Custodia y Cata a Ciegas",
        "Sección V: Sistema de Premiación, Medallas y Distinciones Especiales"
    ], key=f"{key_prefix}_reg_nav")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "Sección I:" in capitulo_sel:
        st.markdown("### ✨ Sección I: Presentación y Objetivos del Certamen")
        st.write("El Festival de Destiladores Patagónicos - Copa Espíritu del Sur es una iniciativa destinada a promover, reconocer y premiar la excelencia en la elaboración de bebidas espirituosas.")
        st.markdown("#### 🎯 Objetivos Estratégicos")
        st.markdown("* 🎖️ **Excelencia:** Reconocer y premiar la calidad de los productos.")
        st.markdown("* 📈 **Mejora Continua:** Promover la evolución técnica de destilados y aperitivos.")
        st.markdown("* 🔬 **Formación:** Generar instancias de capacitación y devoluciones de los jueces.")
        st.markdown("* 🗺️ **Identidad Regional:** Impulsar el uso de materias primas e ingredientes locales.")
        
    elif "Sección II:" in capitulo_sel:
        st.markdown("### 🏢 Sección II: Categorías de Participantes y Requisitos Legales")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🏭 3.1 Destilerías Oficiales")
            st.write("Empresas habilitadas legalmente. Deberán contar con RNE y RNPA vigentes.")
            st.markdown("#### 🔬 3.2 Micro Destiladores")
            st.write("Productores en escala inicial. Declaran obligatoriamente: materia prima, alcohol base y método.")
        with col_p2:
            st.markdown("#### 🏠 3.3 Home Destillery")
            st.write("Pequeña escala experimental. Deben presentar análisis de laboratorio.")
            st.markdown("#### 🌍 3.4 Participantes Internacionales")
            st.write("Productores extranjeros que cumplan las normativas de su país de origen.")

    elif "Sección III:" in capitulo_sel:
        st.markdown("### 📅 Sección III: Cronograma Oficial y Aranceles de Inscripción")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### ⏳ Ventanas de Inscripción (Año 2026)")
            st.markdown("* 🟢 **Primer Lote:** Del 1 de julio al 31 de julio de 2026.")
            st.markdown("* 🟡 **Segundo Lote:** Del 1 de agosto al 31 de agosto de 2026.")
            st.markdown("* 🔴 **Tercer Lote:** Del 1 de septiembre al 30 de septiembre de 2026.")
        with col_c2:
            st.markdown("#### 📦 Logística y Recepción")
            st.markdown("* 📥 **Recepción de Muestras:** Del 1 de octubre al 15 de noviembre de 2026.")
            st.markdown("* 🍾 **Ceremonia de Premiación:** 5, 6 y 7 de diciembre de 2026 en la Sociedad Rural de Bariloche.")

    elif "Sección IV:" in capitulo_sel:
        st.markdown("### 🧪 Sección IV: Criterios de Envío, Custodia y Cata a Ciegas")
        st.markdown("1. 🍾 **Cantidad:** Dos (2) botellas por muestra.")
        st.markdown("2. 🧪 **Volumen Mínimo:** 300 ml por unidad.")
        st.markdown("3. 🏷️ **Identificación:** Todas las botellas deben contar con su etiqueta comercial original.")

    elif "Sección V:" in capitulo_sel:
        st.markdown("### 🥇 Sección V: Sistema de Premiación")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown("<div style='text-align:center; background:#FEF3C7; padding:12px; border-radius:8px; color:#78350f;'>🏅 <b>Medalla de Oro</b><br>90 a 100 Puntos</div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown("<div style='text-align:center; background:#E2E8F0; padding:12px; border-radius:8px; color:#1e293b;'>🥈 <b>Medalla de Plata</b><br>86 a 89.9 Puntos</div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown("<div style='text-align:center; background:#FFEDD5; padding:12px; border-radius:8px; color:#7c2d12;'>🥉 <b>Medalla de Bronce</b><br>82 a 85.9 Puntos</div>", unsafe_allow_html=True)

def renderizar_tutorial_inscripcion():
    """Renderiza la guía interactiva paso a paso para la confirmación de pago."""
    st.markdown("### 📚 Guía Rápida: ¿Cómo confirmar tu Muestra?")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div style="background-color:#1e293b; padding:15px; border-radius:10px; border-top:4px solid #f59e0b; height:100%;">
            <h4 style="color:#f59e0b; margin-top:0;">1. Registrar</h4>
            <p style="font-size:14px; color:#cbd5e1;">
                Ve a <b>"🥃 2. Inscribir Muestra"</b>, completa los datos técnicos y presiona <b>Confirmar e Inscribir</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background-color:#1e293b; padding:15px; border-radius:10px; border-top:4px solid #38bdf8; height:100%;">
            <h4 style="color:#38bdf8; margin-top:0;">2. Liquidar</h4>
            <p style="font-size:14px; color:#cbd5e1;">
                Ve a <b>"📄 3. Estado de Mis Muestras"</b>. Selecciona la muestra para obtener el monto en Pesos y datos de CBU/Alias.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div style="background-color:#1e293b; padding:15px; border-radius:10px; border-top:4px solid #22c55e; height:100%;">
            <h4 style="color:#22c55e; margin-top:0;">3. Confirmar</h4>
            <p style="font-size:14px; color:#cbd5e1;">
                Haz la transferencia, presiona <b>Enviar por WhatsApp</b> para adjuntar el comprobante y luego haz clic en <b>✅ Registrar Envío WA</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# 🛟 BLOQUE DE SOPORTE PERMANENTE EN SIDEBAR
# ==============================================================================
st.sidebar.markdown("---")
with st.sidebar.expander("🚨 ¿Reportar Error o Consultas?", expanded=True):
    st.sidebar.markdown(f"""
    <div style="background-color: #7f1d1d; padding: 12px; border-radius: 6px; border-left: 4px solid #ef4444; color: #fecdd3; font-size: 13px; margin-bottom: 10px;">
        ⚠️ <b>¿Tienes dudas o detectaste un error?</b><br>
        Escríbenos a nuestro correo oficial:
        <br><a href="mailto:{EMAIL_ORGANIZACION}" style="color:#f87171; font-weight:bold; font-family:monospace; text-decoration:underline;">{EMAIL_ORGANIZACION}</a>
    </div>
    """, unsafe_allow_html=True)
    
    tipo_reporte = st.selectbox("Motivo del contacto:", ["Falla Técnica / Error en App", "Duda sobre Aranceles", "Consulta de Inscripción", "Otro"], key="sop_tipo")
    detalle_reporte = st.text_area("Describe la consulta:", height=70, key="sop_desc")
    
    if detalle_reporte.strip() != "":
        usuario_actual_tag = st.session_state["usuario"] if st.session_state["usuario"] else "Usuario no autenticado"
        asunto_mail = f"Soporte App - {tipo_reporte} ({usuario_actual_tag})"
        cuerpo_mail = f"Hola Organización,\n\nSolicitud de soporte de {usuario_actual_tag}:\n• Motivo: {tipo_reporte}\n• Descripción:\n{detalle_reporte}"
        
        asunto_enc = urllib.parse.quote(asunto_mail)
        cuerpo_enc = urllib.parse.quote(cuerpo_mail)
        url_mailto = f"mailto:{EMAIL_ORGANIZACION}?subject={asunto_enc}&body={cuerpo_enc}"
        
        st.link_button("📧 Redactar Correo Automático", url_mailto, use_container_width=True)

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN
# ==============================================================================
if st.session_state["rol"] is None:
    renderizar_encabezado_oficial()
    
    if st.session_state["mostrar_confirmacion_registro"]:
        st.success("🎉 ¡Cuenta Creada de Forma Exitosa! Procede a ingresar tus datos en la pestaña de inicio de sesión.")
        if st.button("👍 Entendido"):
            st.session_state["mostrar_confirmacion_registro"] = False
            st.rerun()

    tab_login, tab_registro, tab_reglamento_publico = st.tabs([
        "🔑 Iniciar Sesión", 
        "📝 Registrarse como Nuevo Destilador",
        "📜 Reglamento Oficial (Abierto)"
    ])
    
    with tab_login:
        usr = st.text_input("Nombre de Usuario", key="login_user").strip()
        pwd = st.text_input("Contraseña", type="password", key="login_pass").strip()
        
        if st.button("🚀 Ingresar al Portal", key="btn_login"):
            if usuarios_db:
                usr_input = str(usr).strip().lower()
                pwd_input = str(pwd).strip()
                
                autenticado = False
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "").strip().lower() == usr_input:
                        db_contrasena = row_clean.get("contrasena", "").strip()
                        if db_contrasena == pwd_input or db_contrasena.split('.')[0] == pwd_input:
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            autenticado = True
                            st.rerun()
                            
                if not autenticado:
                    st.error("❌ Credenciales inválidas.")
            else:
                st.error("❌ La base de datos de usuarios no está disponible.")
            
    with tab_registro:
        nuevo_usr = st.text_input("Elige tu Nombre de Usuario", key="reg_user").strip().lower()
        nueva_pwd = st.text_input("Elige tu Contraseña", type="password", key="reg_pass").strip()
        confirmar_pwd = st.text_input("Confirmar Contraseña", type="password", key="reg_pass_confirm").strip()
        
        if st.button("✨ Confirmar y Crear Cuenta", key="btn_registro"):
            if not nuevo_usr or not nueva_pwd or not confirmar_pwd:
                st.error("❌ Todos los campos son obligatorios.")
            elif " " in nuevo_usr:
                st.error("❌ El nombre de usuario no puede contener espacios.")
            elif nueva_pwd != confirmar_pwd:
                st.error("❌ Las contraseñas ingresadas no coinciden.")
            elif usuarios_db and any(str(r.get("usuario", "")).strip().lower() == nuevo_usr for r in usuarios_db):
                st.error("❌ Nombre de usuario no disponible.")
            else:
                if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.session_state["mostrar_confirmacion_registro"] = True
                    st.rerun()

    with tab_reglamento_publico:
        renderizar_reglamento_oficial(key_prefix="publico")

# ==============================================================================
# 🚀 ENTORNO INTERNO DEL USUARIO AUTENTICADO
# ==============================================================================
else:
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.session_state["perfil_guardado_exito"] = False
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

    renderizar_encabezado_oficial()

    # --------------------------------------------------------------------------
    # 🔔 AVISO AUTOMÁTICO DE MUESTRAS PENDIENTES
    # --------------------------------------------------------------------------
    df_m_check = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
    muestras_pendientes_usuario = []
    if not df_m_check.empty:
        df_m_check.columns = [c.lower().replace('categoría','categoria') for c in df_m_check.columns]
        mis_m_check = df_m_check[df_m_check["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()].to_dict(orient="records")
        muestras_pendientes_usuario = [
            m for m in mis_m_check 
            if str(m.get('estado', '')).strip().upper() in ['PENDIENTE', '', 'NAN', 'S/D']
            and str(m.get('id_muestra', '')) not in st.session_state["muestras_notificadas"]
        ]

    if muestras_pendientes_usuario:
        st.markdown(f"""
        <div style="background-color: #7f1d1d; padding: 16px; border-radius: 10px; border-left: 6px solid #ef4444; color: #fecdd3; margin-bottom: 20px;">
            <h4 style="margin: 0 0 5px 0; color: #ffffff;">⚠️ Tienes {len(muestras_pendientes_usuario)} muestra(s) pendiente(s) de confirmación</h4>
            Para completar tu participación en la Copa Espíritu del Sur, debes reportar tu pago. Ve a la pestaña <b>"📄 3. Estado de Mis Muestras"</b>.
        </div>
        """, unsafe_allow_html=True)

    if st.session_state["mostrar_confirmacion_muestra"] and st.session_state["info_muestra_creada"]:
        info = st.session_state["info_muestra_creada"]
        st.success("🏆 ¡Muestra Registrada Exitosamente!")
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:15px; border-radius:8px; margin-bottom:15px; border:1px solid #f59e0b;">
            <p style="margin:0; font-size:15px; color:#cbd5e1;"><b>Concurso:</b> 1° Festival de Destiladores Patagónicos</p>
            <p style="margin:5px 0 0 0; font-size:24px; color:#f59e0b; font-weight:bold;">🏆 Copa Espíritu del Sur</p>
            <p style="margin:8px 0 0 0; font-size:16px; color:#38bdf8;"><b>Código asignado:</b> {info['id_muestra']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("💡 **¿Qué sigue ahora?** Puedes registrar otra muestra o ir a **'3. Estado de Mis Muestras'** para efectuar el pago.")
        if st.button("👍 Entendido / Continuar", type="primary"):
            st.session_state["mostrar_confirmacion_muestra"] = False
            st.session_state["info_muestra_creada"] = {}
            st.rerun()

    # Pestañas principales
    tab_perfil, tab_muestra, tab_estado, tab_reglamento = st.tabs([
        "📋 1. Perfil Destilería", 
        "🥃 2. Inscribir Muestra", 
        "📄 3. Estado de Mis Muestras",
        "📜 4. Reglamento Oficial"
    ])

    with tab_perfil:
        st.subheader("📋 Información de Contacto")
        tipo_part = st.selectbox("Tipo de Participante (Según Reglamento):", ["Destilería Tradicional", "Micro Destilador", "Home Destillery", "Participante Internacional"], index=0)
        n_resp = st.text_input("Responsable Técnico", value=str(perfil_existente.get("responsable", ""))).strip()
        c_resp = st.text_input("Correo Oficial", value=str(perfil_existente.get("correo", ""))).strip()
        n_dest = st.text_input("Destilería / Razón Social", value=str(perfil_existente.get("destileria", ""))).strip()
        m_com = st.text_input("Marca Comercial", value=str(perfil_existente.get("marca", ""))).strip()
        n_rne = st.text_input("Número RNE:", value=str(perfil_existente.get("rne", ""))).strip()
        u_loc = st.text_input("📍 Ubicación", value=str(perfil_existente.get("ubicacion", ""))).strip()
        t_tel = st.text_input("📞 WhatsApp", value=str(perfil_existente.get("telefono", ""))).strip()
        
        if st.session_state["perfil_guardado_exito"]:
            st.success("✨ ¡Tus datos están guardados exitosamente!")
            st.info("➡️ Selecciona la pestaña superior **'🥃 2. Inscribir Muestra'** para registrar tus productos.")

        if st.button("💾 Guardar Datos del Perfil"):
            if not n_dest or not n_rne or not n_resp or not c_resp:
                st.error("❌ Los campos clave son obligatorios.")
            else:
                payload = {"action_real": "guardar_perfil", "usuario": st.session_state["usuario"], "responsable": n_resp, "correo": c_resp, "destileria": n_dest, "marca": m_com, "rne": n_rne, "ubicacion": u_loc, "telefono": t_tel}
                if enviar_datos(payload):
                    st.session_state["perfil_guardado_exito"] = True
                    st.rerun()

    with tab_muestra:
        txt_cotizacion_banner = f"$ {cotizacion_hoy:,.2f} ARS"
        st.markdown(f"""
        <div class="card-warning">
            <h4 style="color:#f59e0b; margin-bottom:5px;">⚠️ BASES LOGÍSTICAS - FESTIVAL DE DESTILADORES PATAGÓNICOS</h4>
            Recuerda enviar físicamente las muestras requeridas por el reglamento (2 botellas de mínimo 300 ml con etiqueta comercial).
            <br><b>Cotización actual: {txt_cotizacion_banner}</b>
        </div>
        """, unsafe_allow_html=True)
        
        p_nom = st.text_input("Nombre Comercial de la Muestra (Ej: Gin London Dry, Vermut Rojo...)", key="m_prod").strip()
        
        def formatear_con_aclaracion(opcion):
            return f"{opcion} — ({ACLARACIONES_CATEGORIAS[opcion][:55]}...)"
            
        p_cat = st.selectbox(
            "Categoría del Espíritu:", 
            categorias_disponibles, 
            format_func=formatear_con_aclaracion,
            key="m_cat"
        )
        
        with st.expander("🔍 Ver descripción reglamentaria completa de la categoría seleccionada"):
            st.info(ACLARACIONES_CATEGORIAS[p_cat])
            
        st.markdown("### 🧬 Datos Técnicos Obligatorios (Art. 5 Reglamento)")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            p_grad = st.number_input("Graduación Alcohólica (% Vol):", min_value=0.0, max_value=100.0, value=40.0, step=0.1)
        with col_t2:
            p_mat = st.text_input("Materias Primas:", value="Enebro y Alcohol Neutro").strip()
        with col_t3:
            p_anej = st.text_input("Tiempo de Añejamiento:", value="No aplica").strip()
            
        p_rnpa = st.text_input("Registro RNPA, Trámite o Declaración Base:", key="m_rnpa").strip()
        p_vol = st.number_input("Volumen de la Botella (ml):", min_value=50, max_value=5000, value=750, step=50)
        
        if st.button("🔒 Confirmar e Inscribir Muestra"):
            if not p_nom or not p_rnpa or not p_mat:
                st.error("❌ Completa los campos obligatorios.")
            else:
                with st.spinner("Procesando inscripción..."):
                    df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
                    muestras_previas = 0
                    if not df_m.empty:
                        df_m.columns = [c.lower() for c in df_m.columns]
                        mis_m = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
                        muestras_previas = len(mis_m)
                    
                    total_muestras = muestras_previas + 1
                    valor_usd, lote = calcular_arancel_muestra(total_muestras)
                    id_generado = f"DST-{random.randint(1000, 9999)}"
                    
                    payload_muestra = {
                        "action_real": "guardar_muestra", 
                        "id_muestra": id_generado,
                        "usuario": st.session_state["usuario"], 
                        "producto": p_nom, 
                        "categoria": p_cat, 
                        "rnpa": p_rnpa, 
                        "volumen": str(p_vol),
                        "graduacion": str(p_grad),
                        "materias": p_mat,
                        "tiempo": p_anej,
                        "estado": "PENDIENTE"
                    }
                    
                    if enviar_datos(payload_muestra):
                        st.session_state["info_muestra_creada"] = {"id_muestra": id_generado}
                        st.session_state["mostrar_confirmacion_muestra"] = True
                        st.rerun()

        st.markdown("---")
        st.subheader("📊 Cuadro Tarifario de Aranceles")
        tabla_valores = pd.DataFrame({
            "Cantidad de Muestras": ["1 a 3 muestras", "4 a 7 muestras", "8 o más muestras"],
            "Lote 1 (Hasta 31/Jul)": ["USD 60 / muestra", "USD 50 / muestra", "USD 45 / muestra"],
            "Lote 2 (Agosto)": ["USD 70 / muestra", "USD 60 / muestra", "USD 55 / muestra"],
            "Lote 3 (Septiembre)": ["USD 80 / muestra", "USD 70 / muestra", "USD 65 / muestra"]
        })
        st.table(tabla_valores)

    with tab_estado:
        renderizar_tutorial_inscripcion()
        st.markdown("---")
        
        st.subheader("🔗 Reportar Pago de una Muestra")
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        mis_muestras_lista = []
        if not df_m.empty:
            df_m.columns = [c.lower().replace('categoría','categoria') for c in df_m.columns]
            mis_m_filtradas = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
            mis_muestras_lista = mis_m_filtradas.to_dict(orient="records")
            
        muestras_para_desplegable = [
            m for m in mis_muestras_lista 
            if str(m.get('estado', '')).strip().upper() != "CONFIRMADO"
        ]
            
        if not muestras_para_desplegable:
            st.success("🎉 ¡Todas tus muestras están confirmadas o no tienes pendientes de pago!")
        else:
            opciones_muestra = {
                f"{m.get('id_muestra', 'S/D')} — {m.get('producto', 'S/P')} ({m.get('categoria', 'S/C')})": m 
                for m in muestras_para_desplegable
            }
            
            seleccion_label = st.selectbox("👉 Selecciona la muestra específica que deseas abonar:", list(opciones_muestra.keys()))
            
            muestra_elegida = opciones_muestra[seleccion_label]
            idx_muestra = mis_muestras_lista.index(muestra_elegida) + 1
            valor_usd, lote_nro = calcular_arancel_muestra(idx_muestra)
            monto_pesos = valor_usd * cotizacion_hoy
            id_actual = str(muestra_elegida.get('id_muestra', ''))
            
            st.markdown(f"""
            <div class="box-pago">
                <p style="margin:0 0 8px 0; font-size:18px; color:#f59e0b; font-weight:bold;">📋 Liquidación Muestra N° {idx_muestra} — Código: {id_actual}</p>
                • <b>Arancel de Inscripción:</b> <span style="font-size: 16px; color: #34d399; font-weight:bold;">USD {valor_usd} (${monto_pesos:,.0f} ARS)</span><br>
                • 📊 <i>Cotización del día: $ {cotizacion_hoy:,.2f} ARS por Dólar</i><br><br>
                • 🇺🇸 <b>CBU Dólares:</b> <span style="font-family: monospace; background:#334155; padding:3px 6px; font-weight: bold; color:#f8fafc;">{CBU_DOLARES}</span><br>
                • 🇦🇷 <b>Alias Pesos:</b> <span style="font-family: monospace; background:#334155; padding:3px 6px; font-weight: bold; color:#34d399;">{ALIAS_PESOS}</span><br>
                • 👤 <b>Titular:</b> <b>{TITULAR_CUENTA}</b><br>
            </div>
            """, unsafe_allow_html=True)
            
            texto_wa = (
                f"🏆 *1° FESTIVAL DE DESTILADORES PATAGÓNICOS - COPA ESPÍRITU DEL SUR*\n"
                f"Hola! Envío el comprobante de pago de mi inscripción:\n\n"
                f"🆔 *Código:* {id_actual}\n"
                f"🏬 *Destilería:* {nombre_destileria_global}\n"
                f"🥃 *Muestra:* {muestra_elegida.get('producto')} ({muestra_elegida.get('categoria')})\n"
                f"💰 *Arancel:* USD {valor_usd} (${monto_pesos:,.0f} ARS)\n\n"
                f"⚠️ *Nota:* Adjunto el comprobante correspondiente."
            )
            texto_encoded = urllib.parse.quote(texto_wa)
            url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={texto_encoded}"
            
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                st.link_button(f"📲 ENVIAR COMPROBANTE DE {id_actual} POR WHATSAPP", url_wa, use_container_width=True)
            with col_b2:
                if st.button("✅ Registrar Envío WA", key=f"btn_confirm_wa_{id_actual}"):
                    st.session_state["muestras_notificadas"].add(id_actual)
                    payload_actualizar = {
                        "action_real": "actualizar_estado_muestra",
                        "id_muestra": id_actual,
                        "estado": "ENVIADO"
                    }
                    enviar_datos(payload_actualizar)
                    st.success("¡Estado actualizado a ENVIADO!")
                    st.rerun()

        st.markdown("---")
        st.subheader("📄 Historial General de Mis Muestras")
        if not df_m.empty:
            mis_m_filtradas = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()].copy()
            if not mis_m_filtradas.empty:
                def calcular_estado_final(fila):
                    id_m = str(fila.get("id_muestra", ""))
                    estado_orig = str(fila.get("estado", "PENDIENTE")).strip().upper()
                    if estado_orig == "CONFIRMADO":
                        return "CONFIRMADO"
                    elif id_m in st.session_state["muestras_notificadas"] or estado_orig == "ENVIADO":
                        return "ENVIADO"
                    return "PENDIENTE"

                mis_m_filtradas["estado_calculado"] = mis_m_filtradas.apply(calcular_estado_final, axis=1)
                
                cols_seguras = ["id_muestra", "producto", "categoria", "estado_calculado", "fecha"]
                cols_presentes = [c for c in cols_seguras if c in mis_m_filtradas.columns]
                df_mostrar = mis_m_filtradas[cols_presentes].copy()
                df_mostrar.rename(columns={"estado_calculado": "estado"}, inplace=True)

                def colorear_filas(row):
                    estado_val = str(row["estado"]).strip().upper()
                    if estado_val == "CONFIRMADO":
                        return ['background-color: #14532d; color: #bbf7d0; font-weight: bold;'] * len(row)
                    elif estado_val == "ENVIADO":
                        return ['background-color: #713f12; color: #fef08a; font-weight: bold;'] * len(row)
                    else:
                        return ['background-color: #7f1d1d; color: #fecdd3; font-weight: bold;'] * len(row)

                df_estilizado = df_mostrar.style.apply(colorear_filas, axis=1)
                st.dataframe(df_estilizado, use_container_width=True)
            else:
                st.info("No hay muestras registradas para tu cuenta.")
        else:
            st.info("Aún no has registrado ninguna muestra.")

    with tab_reglamento:
        renderizar_reglamento_oficial(key_prefix="interno")
