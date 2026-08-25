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
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxnP6vgIdWGi9YYCU6aiRml4EpoHVJtP-ScirCafrvXXmyX7Vo2J-twgJGqQSa5uECO4w/exec"
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
# 🥃 CONFIGURACIÓN DE INTERFAZ Y ESTILOS
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
if "tab_activa" not in st.session_state:
    st.session_state["tab_activa"] = 0

# Estilos CSS corregidos para dar máxima visibilidad a las pestañas superiores
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem !important; padding-bottom: 5rem !important; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 28px; text-align: center; margin-bottom: 5px; }
    .sub-header { color: #D97706; font-size: 22px; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .poetic-text { font-style: italic; text-align: center; color: #475569; max-width: 800px; margin: 0 auto 15px auto; font-size: 15px; line-height: 1.4; }
    .date-badge { text-align: center; font-weight: bold; color: #1e3a8a; background-color: #e0f2fe; padding: 8px; border-radius: 20px; max-width: 450px; margin: 0 auto 20px auto; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
    .box-pago { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; padding: 10px 16px; border-radius: 6px 6px 0 0; }
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
# 📖 DICCIONARIO DE CATEGORÍAS Y ACLARACIONES (REGLAMENTO OFICIAL)
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
    st.markdown("<h1 class='main-header'>1° Festival de Destiladores Patagónicos</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>Copa Espíritu del Sur</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p class='poetic-text'>
    "El espíritu del Sur se destila aquí. Donde la pureza cristalina del agua de deshielo andino y los botánicos de nuestra cordillera florecida se funden en el bronce y cobre de los alambiques."
    </p>
    <div class='date-badge'>📍 5, 6 y 7 de Diciembre | Predio Sociedad Rural de Bariloche</div>
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
        st.write("El Festival de Destiladores Patagónicos - Copa Espíritu del Sur es una iniciativa destinada a promover, reconocer y premiar la excelencia en la elaboración de bebidas espirituosas, aperitivos, vermuts, licores y productos afines.")
        st.write("El festival busca fortalecer la cultura de los destilados, impulsar el desarrollo de productores artesanales e industriales, y posicionar a la Patagonia como un polo de referencia industrial.")
        st.markdown("#### 🎯 Objetivos Estratégicos")
        st.markdown("* 🎖️ **Excelencia:** Reconocer y premiar la calidad de los productos.")
        st.markdown("* 📈 **Mejora Continua:** Promover la evolución técnica de destilados y aperitivos.")
        st.markdown("* 🔬 **Formación:** Generar instancias de capacitación y devoluciones de los jueces.")
        st.markdown("* 🗺️ **Identidad Regional:** Impulsar el uso de materias primas e ingredientes locales.")
        
    elif "Sección II:" in capitulo_sel:
        st.markdown("### 🏢 Sección II: Categorías de Participantes y Requisitos Legales")
        st.write("Podrán participar productores nacionales e internacionales bajo las siguientes subcategorías:")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🏭 3.1 Destilerías Oficiales")
            st.write("Empresas habilitadas legalmente. Deberán contar con RNE y RNPA vigentes o documentación equivalente.")
            st.markdown("#### 🔬 3.2 Micro Destiladores")
            st.write("Productores en escala inicial. Declaran obligatoriamente: materia prima, alcohol base y método.")
        with col_p2:
            st.markdown("#### 🏠 3.3 Home Destillery")
            st.write("Pequeña escala experimental. Deben presentar análisis de laboratorio. No computan para Grandes Premios de Destilería del Año.")
            st.markdown("#### 🌍 3.4 Participantes Internacionales")
            st.write("Productores extranjeros que cumplan las normativas vigentes en su país de origen.")
        st.error("⚠️ **Cláusula Legal:** Los productos deben ajustarse al Código Alimentario. Si no cumplen requisitos legales, recibirán devolución técnica pero NO medallas ni premios.")

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
            st.markdown("* ⚖️ **Evaluación Técnica:** Durante el mes de noviembre de 2026.")
            st.markdown("* 🍾 **Ceremonia de Premiación:** 5, 6 y 7 de diciembre de 2026 en la Sociedad Rural de Bariloche, Río Negro.")

    elif "Sección IV:" in capitulo_sel:
        st.markdown("### 🧪 Sección IV: Criterios de Envío, Custodia y Cata a Ciegas")
        st.markdown("#### 📦 Requisitos Estrictos del Envío")
        st.write("Cada muestra inscripta deberá enviarse siguiendo estas especificaciones físicas:")
        st.markdown("1. 🍾 **Cantidad:** Dos (2) botellas por muestra.")
        st.markdown("2. 🧪 **Volumen Mínimo:** 300 ml por unidad.")
        st.markdown("3. 🏷️ **Identificación:** Todas las botellas deben contar con su etiqueta comercial original. La ausencia de etiqueta comercial implicará la descalificación automática.")
        st.warning("🔒 **Protocolo de Cata a Ciegas:** La evaluación se realizará sin que los jueces conozcan las marcas ni la procedencia geográfica.")

    elif "Sección V:" in capitulo_sel:
        st.markdown("### 🥇 Sección V: Sistema de Premiación, Medallas y Distinciones Especiales")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown("<div style='text-align:center; background:#FEF3C7; padding:10px; border-radius:5px;'>🏅 <b>Medalla de Oro</b><br>90 a 100 Puntos</div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown("<div style='text-align:center; background:#E2E8F0; padding:10px; border-radius:5px;'>🥈 <b>Medalla de Plata</b><br>86 a 89.9 Puntos</div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown("<div style='text-align:center; background:#FFEDD5; padding:10px; border-radius:5px;'>🥉 <b>Medalla de Bronce</b><br>82 a 85.9 Puntos</div>", unsafe_allow_html=True)

# ==============================================================================
# 🛟 BLOQUE DE SOPORTE PERMANENTE EN SIDEBAR
# ==============================================================================
st.sidebar.markdown("---")
with st.sidebar.expander("🚨 ¿Reportar Error o Consultas?", expanded=True):
    st.sidebar.markdown(f"""
    <div style="background-color: #fee2e2; padding: 12px; border-radius: 6px; border-left: 4px solid #ef4444; color: #991b1b; font-size: 13px; margin-bottom: 10px;">
        ⚠️ <b>¿La app no responde o detectaste un error?</b><br>
        Escríbenos a nuestro correo oficial de soporte:
        <br><a href="mailto:{EMAIL_ORGANIZACION}" style="color:#b91c1c; font-weight:bold; font-family:monospace; text-decoration:underline;">{EMAIL_ORGANIZACION}</a>
    </div>
    """, unsafe_allow_html=True)
    
    tipo_reporte = st.selectbox("Motivo del contacto:", ["Falla Técnica / Error en App", "Duda sobre Aranceles", "Consulta de Inscripción", "Otro"], key="sop_tipo")
    detalle_reporte = st.text_area("Describe el problema detalladamente:", height=70, key="sop_desc")
    
    if detalle_reporte.strip() != "":
        usuario_actual_tag = st.session_state["usuario"] if st.session_state["usuario"] else "Usuario no autenticado"
        asunto_mail = f"Soporte App +soporte - {tipo_reporte} ({usuario_actual_tag})"
        cuerpo_mail = f"Hola Organización,\n\nSe ha enviado una solicitud de soporte desde el portal:\n\n• Usuario: {usuario_actual_tag}\n• Motivo: {tipo_reporte}\n• Descripción:\n{detalle_reporte}"
        
        asunto_enc = urllib.parse.quote(asunto_mail)
        cuerpo_enc = urllib.parse.quote(cuerpo_mail)
        url_mailto = f"mailto:{EMAIL_ORGANIZACION}?subject={asunto_enc}&body={cuerpo_enc}"
        
        st.link_button("📧 Redactar Correo Automático", url_mailto, use_container_width=True)

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN / PORTADA PÚBLICA
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

    if st.session_state["mostrar_confirmacion_muestra"] and st.session_state["info_muestra_creada"]:
        info = st.session_state["info_muestra_creada"]
        st.success("🏆 ¡Muestra Registrada Exitosamente!")
        st.markdown(f"""
        <div style="background-color:#f0fdf4; padding:12px; border-radius:6px; margin-bottom:15px; border:1px solid #bbf7d0;">
            <p style="margin:0; font-size:15px; color:#374151;"><b>Concurso:</b> 1° Festival de Destiladores Patagónicos</p>
            <p style="margin:5px 0 0 0; font-size:24px; color:#D97706; font-weight:bold;">🏆 Copa Espíritu del Sur</p>
            <p style="margin:8px 0 0 0; font-size:16px; color:#1e3a8a;"><b>Código asignado:</b> {info['id_muestra']}</p>
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
        n_rne = st.text_input("Número RNE (Escribir Registro u Origen si es Internacional/Home):", value=str(perfil_existente.get("rne", ""))).strip()
        u_loc = st.text_input("📍 Ubicación", value=str(perfil_existente.get("ubicacion", ""))).strip()
        t_tel = st.text_input("📞 WhatsApp", value=str(perfil_existente.get("telefono", ""))).strip()
        
        if st.session_state["perfil_guardado_exito"]:
            st.success("✨ ¡Tus datos están guardados exitosamente!")
            st.markdown("👇 **Haz clic abajo para ir directamente al siguiente paso:**")
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
            <h4>⚠️ BASES LOGÍSTICAS - FESTIVAL DE DESTILADORES PATAGÓNICOS</h4>
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
                        "tiempo": p_anej
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
        st.subheader("🔗 Reportar Pago de una Muestra")
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        mis_muestras_lista = []
        if not df_m.empty:
            df_m.columns = [c.lower().replace('categoría','categoria') for c in df_m.columns]
            mis_m_filtradas = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
            mis_muestras_lista = mis_m_filtradas.to_dict(orient="records")
            
        if not mis_muestras_lista:
            st.info("Aún no tienes muestras registradas para pagar.")
        else:
            # Cartel de advertencia para muestras sin pagar
            muestras_pendientes = [m for m in mis_muestras_lista if str(m.get('id_muestra', '')) not in st.session_state["muestras_notificadas"] and str(m.get('estado', '')).lower() in ['pendiente', '', 'nan', 's/d']]
            if muestras_pendientes:
                st.warning(f"⚠️ **Atención:** Tienes {len(muestras_pendientes)} muestra(s) pendiente(s) de reporte de pago. Selecciona la muestra abajo y reporta el comprobante por WhatsApp.")

            opciones_muestra = {f"{m.get('id_muestra', 'S/D')} — {m.get('producto', 'S/P')} ({m.get('categoria', 'S/C')})": m for m in mis_muestras_lista}
            seleccion_label = st.selectbox("👉 Selecciona la muestra específica que deseas abonar:", list(opciones_muestra.keys()))
            
            muestra_elegida = opciones_muestra[seleccion_label]
            idx_muestra = mis_muestras_lista.index(muestra_elegida) + 1
            valor_usd, lote_nro = calcular_arancel_muestra(idx_muestra)
            monto_pesos = valor_usd * cotizacion_hoy
            id_actual = str(muestra_elegida.get('id_muestra', ''))
            
            st.markdown(f"""
            <div class="box-pago">
                <p style="margin:0 0 8px 0; font-size:18px; color:#1E3A8A; font-weight:bold;">📋 Liquidación Muestra N° {idx_muestra} de tu cuenta — Código: {id_actual}</p>
                • <b>Arancel de Inscripción:</b> <span style="font-size: 16px; color: #065F46; font-weight:bold;">USD {valor_usd} (${monto_pesos:,.0f} ARS)</span><br>
                • 📊 <i>Cotización del día: $ {cotizacion_hoy:,.2f} ARS por Dólar</i><br><br>
                • 🇺🇸 <b>CBU Dólares:</b> <span style="font-family: monospace; background:#e2e8f0; padding:3px 6px; font-weight: bold; color:#1e3a8a;">{CBU_DOLARES}</span><br>
                • 🇦🇷 <b>Alias Pesos:</b> <span style="font-family: monospace; background:#f4f4f4; padding:3px 6px; font-weight: bold; color:#065f46;">{ALIAS_PESOS}</span><br>
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
            
            if st.link_button(f"📱 Enviar Comprobante de {id_actual} por WhatsApp", url_wa, use_container_width=True):
                st.session_state["muestras_notificadas"].add(id_actual)
            
        st.markdown("---")
        st.subheader("📄 Historial General de Mis Muestras")
        if not df_m.empty:
            mis_m_filtradas = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()].copy()
            if not mis_m_filtradas.empty:
                def optimizar_estado(fila):
                    id_m = str(fila.get("id_muestra", ""))
                    estado_original = str(fila.get("estado", "Pendiente"))
                    if id_m in st.session_state["muestras_notificadas"] and estado_original.lower() in ["pendiente", "", "nan", "s/d"]:
                        return "⏳ Por comprobar"
                    return estado_original

                if "estado" in mis_m_filtradas.columns:
                    mis_m_filtradas["estado"] = mis_m_filtradas.apply(optimizar_estado, axis=1)
                
                # Muestra únicamente las del usuario activo
                cols_seguras = ["id_muestra", "producto", "categoria", "estado", "fecha"]
                cols_presentes = [c for c in cols_seguras if c in mis_m_filtradas.columns]
                st.dataframe(mis_m_filtradas[cols_presentes], use_container_width=True)
            else:
                st.info("No hay muestras registradas para tu cuenta.")
        else:
            st.info("Aún no has registrado ninguna muestra.")

    with tab_reglamento:
        renderizar_reglamento_oficial(key_prefix="interno")
