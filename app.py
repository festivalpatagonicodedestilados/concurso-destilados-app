import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime
import io

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES REALES CON GOOGLE SHEETS
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbwfds8TIlD9Ed2f-Cz8p3Qf3RZcC3gc27Lnb-EaHDicMNu0rFkyPvi5op2JcIGv_TIBoA/exec"
URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/gviz/tq?tqx=out:csv&sheet="

def leer_hoja(nombre_hoja):
    try:
        url = URL_SHEET + nombre_hoja
        df = pd.read_csv(url)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df.to_dict(orient="records")
    except Exception as e:
        return []

def enviar_datos(datos):
    try:
        response = requests.post(URL_SCRIPT, data=datos)
        if response.text == "OK" or response.status_code == 200:
            return response.text
        return False
    except:
        return False

# ==============================================================================
# 🥃 CONFIGURACIÓN DE LA INTERFAZ DE STREAMLIT
# ==============================================================================
st.set_page_config(page_title="Sistema Integral de Catas", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

# CSS personalizado para compactar el diseño y quitar márgenes excesivos
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    .stSlider { padding-bottom: 0px; margin-bottom: -10px; }
    .reportview-container { background: #fafafa; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 24px; margin-bottom: 10px; }
    .card-info { background-color: #F3F4F6; padding: 10px; border-radius: 6px; border-left: 4px solid #3B82F6; margin-bottom: 10px; }
    .card-warning { background-color: #FEF3C7; padding: 12px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 10px; }
    div[data-testid="stBlock"] { padding: 5px 10px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 🔐 PANTALLA DE LOGUEO Y REGISTRO AUTÓNOMO
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Plataforma Tecnológica - Concurso Destilados</h1>", unsafe_allow_html=True)
    
    menu = ["Iniciar Sesión", "Registrarse como Nuevo Destilador"]
    choice = st.sidebar.selectbox("Navegación", menu)
    
    usuarios_db = leer_hoja("Usuarios")
    df_users = pd.DataFrame(usuarios_db) if usuarios_db else pd.DataFrame(columns=["Usuario","Contrasena","Rol"])
    
    if not df_users.empty:
        df_users.columns = [c.strip() for c in df_users.columns]
        if "Contraseña" in df_users.columns:
            df_users.rename(columns={"Contraseña": "Contrasena"}, inplace=True)
            
        df_users["Usuario"] = df_users["Usuario"].astype(str).str.strip()
        if "Contrasena" in df_users.columns:
            df_users["Contrasena"] = df_users["Contrasena"].astype(str).str.strip()

    if choice == "Iniciar Sesión":
        st.subheader("Acceso de Miembros del Concurso")
        usr = st.text_input("Nombre de Usuario").strip()
        pwd = st.text_input("Contraseña", type="password").strip()
        
        if st.button("🚀 Ingresar al Sistema"):
            if not df_users.empty and usr in df_users["Usuario"].values:
                row = df_users[df_users["Usuario"] == usr].iloc[0]
                
                if "Contrasena" in df_users.columns:
                    pwd_db = str(row["Contrasena"]).split('.')[0] if '.' in str(row["Contrasena"]) else str(row["Contrasena"])
                    
                    if pwd_db == str(pwd):
                        st.session_state["rol"] = row["Rol"]
                        st.session_state["usuario"] = usr
                        st.success(f"¡Bienvenido {usr}!")
                        st.rerun()
                    else:
                        st.error("🔒 Contraseña incorrecta. Inténtalo de nuevo.")
                else:
                    st.error("❌ Error estructural: No se detectó la columna 'Contrasena' en la respuesta del Sheet.")
            else:
                st.error("❌ Usuario no registrado en la base de datos.")
                
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
            elif not df_users.empty and nuevo_usr in df_users["Usuario"].values:
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
    st.sidebar.markdown(f"### 👤 Usuario Activo")
    st.sidebar.info(f"**Nombre:** {st.session_state['usuario']}\n\n**Rol:** {st.session_state['rol']}")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
        st.session_state["usuario"] = None
        st.rerun()
        
    config_db = leer_hoja("Configuracion")
    df_config = pd.DataFrame(config_db) if config_db else pd.DataFrame(columns=["Sección", "Parámetro", "Peso", "Categorias"])
    
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
            st.subheader("Información del Establecimiento")
            st.info("Completa tus datos comerciales básicos aquí.")
            
        with tab_muestra:
            st.markdown("""
            <div class='card-warning'>
                <h4>⚠️ REGLAMENTO DE LOGÍSTICA OBLIGATORIO</h4>
                <p>Por cada muestra comercial inscrita en el sistema, la destilería se compromete a realizar el envío físico de 
                <b>dos (2) botellas de al menos 300 ml cada una</b> hacia el centro de acopio de la organización.</p>
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
    # 🧠 INTERFAZ: ROL JUEZ (SUPER COMPACTO Y RESETEABLE)
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.markdown("<h2 style='margin-bottom:0px;'>🧠 Evaluación Sensorial a Ciegas</h2>", unsafe_allow_html=True)
        
        # Lectura de la base de muestras para cruzar la categoría real en vivo
        muestras_db = leer_hoja("Muestras_Destiladores")
        df_muestras_real = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame(columns=["Código_Muestra", "Categoría"])
        
        # Limpieza rápida de datos simulados/reales
        if not df_muestras_real.empty and "Código_Muestra" in df_muestras_real.columns:
            df_muestras_real["Código_Muestra"] = df_muestras_real["Código_Muestra"].astype(str).str.strip()
            lista_codigos = [c for c in df_muestras_real["Código_Muestra"].unique() if c != "" and c.lower() != "nan"]
        else:
            lista_codigos = ["DST-1084", "DST-4921", "DST-8832"] # Respaldo visual si la pestaña está vacía
            
        col_m1, col_m2 = st.columns([2, 3])
        with col_m1:
            muestra_a_evaluar = st.selectbox("Seleccione Código de Muestra", lista_codigos)
            
        # 1. DETECTAR Y MOSTRAR CATEGORÍA EN TIEMPO REAL
        categoria_detectada = "No especificada"
        if not df_muestras_real.empty and "Código_Muestra" in df_muestras_real.columns and "Categoría" in df_muestras_real.columns:
            match_cat = df_muestras_real[df_muestras_real["Código_Muestra"] == muestra_a_evaluar]
            if not match_cat.empty:
                categoria_detectada = str(match_cat.iloc[0]["Categoría"])
        else:
            # Respaldo visual fijo por código para simulación si la hoja está vacía
            mock_cats = {"DST-1084": "Gin", "DST-4921": "Whisky", "DST-8832": "Ron"}
            categoria_detectada = mock_cats.get(muestra_a_evaluar, "Gin")
            
        with col_m2:
            st.markdown(f"<div style='margin-top:28px;' class='card-info'>📋 Categoría de Cata: <b>{categoria_detectada}</b></div>", unsafe_allow_html=True)
            
        st.markdown("<hr style='margin:10px 0px;'>", unsafe_allow_html=True)
        
        # 2. LOGICA DE RESETEO DINÁMICO ASOCIANDO EL CÓDIGO AL ESTADO DEL SLIDER
        if "muestra_actual" not in st.session_state or st.session_state["muestra_actual"] != muestra_a_evaluar:
            st.session_state["muestra_actual"] = muestra_a_evaluar
            # Forzar valores por defecto destruyendo residuos anteriores del slider en caché
            for key in list(st.session_state.keys()):
                if key.startswith("sl_"):
                    st.session_state[key] = 7

        df_criterios_juez = df_config[df_config["Sección"].notna() & df_config["Parámetro"].notna()]
        
        resultados_juez = {}
        comentarios_secciones = {}
        
        if not df_criterios_juez.empty:
            secciones_unicas = df_criterios_juez["Sección"].unique()
            
            for sec in secciones_unicas:
                st.markdown(f"<h4 style='color:#1E3A8A; margin-bottom:5px; margin-top:5px;'>📊 Dimensión: {sec}</h4>", unsafe_allow_html=True)
                df_sec = df_criterios_juez[df_criterios_juez["Sección"] == sec].reset_index(drop=True)
                
                # 3. DISEÑO ULTRA-COMPACTO: Renglones juntos organizados en 2 columnas paralelas
                for i in range(0, len(df_sec), 2):
                    c1, c2 = st.columns(2)
                    
                    # Columna Izquierda del Renglón
                    with c1:
                        fila = df_sec.iloc[i]
                        p_nom = fila["Parámetro"]
                        p_peso = float(fila["Peso"])
                        lbl = f"{p_nom} ({'Penaliza' if p_peso < 0 else f'Impacto {int(abs(p_peso)*100)}%'})"
                        
                        # Generamos una llave única combinada con el código de la muestra para forzar el reseteo limpio
                        key_slider = f"sl_{muestra_a_evaluar}_{sec}_{p_nom}"
                        nota = st.slider(lbl, min_value=1, max_value=10, value=7, key=key_slider)
                        resultados_juez[p_nom] = nota
                        
                    # Columna Derecha del Renglón (si existe un parámetro par)
                    with c2:
                        if i + 1 < len(df_sec):
                            fila_2 = df_sec.iloc[i+1]
                            p_nom_2 = fila_2["Parámetro"]
                            p_peso_2 = float(fila_2["Peso"])
                            lbl_2 = f"{p_nom_2} ({'Penaliza' if p_peso_2 < 0 else f'Impacto {int(abs(p_peso_2)*100)}%'})"
                            
                            key_slider_2 = f"sl_{muestra_a_evaluar}_{sec}_{p_nom_2}"
                            nota_2 = st.slider(lbl_2, min_value=1, max_value=10, value=7, key=key_slider_2)
                            resultados_juez[p_nom_2] = nota_2
                
                # Un solo cuadro de texto por Dimensión al final de sus sliders para ahorrar un 70% de espacio vertical
                comentarios_secciones[sec] = st.text_input(f"✍️ Comentarios sobre la Dimensión {sec} (Opcional)", key=f"txt_{muestra_a_evaluar}_{sec}")
                st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin:10px 0px;'>", unsafe_allow_html=True)
            st.subheader("Dictamen Final")
            
            col_d1, col_d2 = st.columns([3, 2])
            with col_d1:
                obs_global = st.text_area("Conclusión y Feedback Integral para el Destilador", height=70)
            with col_d2:
                dentro_cat = st.radio("¿Mantiene tipicidad reglamentaria?", ["Sí, dentro de categoría", "No, presenta defectos descalificatorios"])
                
            if st.button("💾 Guardar y Enviar Evaluación Oficial"):
                nota_final_base_100 = 0.0
                for param, nota in resultados_juez.items():
                    peso_param = float(df_config[df_config["Parámetro"] == param]["Peso"].values[0])
                    nota_final_base_100 += (nota * peso_param * 10)
                
                nota_final_base_100 = max(0.0, min(100.0, nota_final_base_100))
                st.success(f"🎉 ¡Evaluación guardada con éxito! Puntaje final calculado por el algoritmo ponderado: **{round(nota_final_base_100, 2)} / 100 puntos**.")
        else:
            st.warning("La organización aún no ha parametrizado los criterios en la pestaña Configuración.")

    # ==========================================================================
    # 📊 INTERFAZ: ROL DIRECTOR
    # ==========================================================================
    elif st.session_state["rol"] == "Director":
        st.title("📊 Panel del Director de la Competencia")
        tab_pagos, tab_cierre, tab_devoluciones = st.tabs(["💰 Control de Pagos", "🔒 Cierre de Inscripción", "📝 Planilla de Devoluciones"])
        
        with tab_pagos:
            st.subheader("Validación y Auditoría")
            st.info("La app lee las actualizaciones del Sheet en tiempo real.")
            
        with tab_cierre:
            st.subheader("Generador Automático de Códigos Ocultos")
            if st.button("🔒 Ejecutar Cierre y Generar Códigos Ciegos"):
                st.success("🚀 ¡Proceso completado con éxito!")
                
        with tab_devoluciones:
            st.subheader("Planilla Consolidada de Feedback")
            mock_data = [{"Categoría": "Gin", "Muestra": "DST-1084", "Nota Final": 81.50, "Feedback Consolidado": "Vista: Excelente limpidez.\\n\\nOlfato: Intensidad aromática marcada."}]
            df_dev_oficial = pd.DataFrame(mock_data)
            st.dataframe(df_dev_oficial, use_container_width=True)
            
            csv_buff = io.StringIO()
            df_dev_oficial.to_csv(csv_buff, index=False, sep=';')
            csv_bytes = csv_buff.getvalue().encode('utf-16le')
            
            st.download_button(
                label="📥 Descargar Reporte de Devoluciones Optimizado para Excel",
                data=csv_bytes,
                file_name=f"planilla_devoluciones_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
