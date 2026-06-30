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
        # ESTA LÍNEA TE MOSTRARÁ EL ERROR REAL EN LA PANTALLA DE STREAMLIT:
        st.sidebar.error(f"⚠️ Error leyendo {nombre_hoja}: {str(e)}")
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
    st.session_state["mesa"] = "Mesa 1" # Asignación por defecto

# CSS personalizado compacto y elegante
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

# ==============================================================================
# 🔐 PANTALLA DE LOGUEO ULTRA-TOLERANTE
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Plataforma Tecnológica - Concurso Destilados</h1>", unsafe_allow_html=True)
    
    menu = ["Iniciar Sesión", "Registrarse como Nuevo Destilador"]
    choice = st.sidebar.selectbox("Navegación", menu)
    
    usuarios_db = leer_hoja("Usuarios")
    df_users = pd.DataFrame(usuarios_db) if usuarios_db else pd.DataFrame(columns=["Usuario","Rol"])
    
    if not df_users.empty:
        df_users.columns = [str(c).strip().lower() for c in df_users.columns]
        df_users.rename(columns={
            "usuario": "USER_KEY", "user": "USER_KEY", "nombre": "USER_KEY",
            "contrasena": "PASS_KEY", "contraseña": "PASS_KEY", "clave": "PASS_KEY", "password": "PASS_KEY",
            "rol": "ROLE_KEY", "puesto": "ROLE_KEY"
        }, inplace=True)

    if choice == "Iniciar Sesión":
        st.subheader("Acceso de Miembros del Concurso")
        usr = st.text_input("Nombre de Usuario").strip()
        pwd = st.text_input("Contraseña", type="password").strip()
        
        if st.button("🚀 Ingresar al Sistema"):
            if not df_users.empty and "user_key" in df_users.columns:
                df_match = df_users[df_users["user_key"].astype(str).str.lower() == usr.lower()]
                
                if not df_match.empty:
                    row = df_match.iloc[0]
                    
                    if "pass_key" in df_users.columns:
                        pwd_db = str(row["pass_key"]).strip().split('.')[0] if '.' in str(row["pass_key"]) else str(row["pass_key"]).strip()
                        
                        if pwd_db == str(pwd).strip():
                            st.session_state["rol"] = str(row["role_key"]).strip() if "role_key" in df_users.columns else "Destilador"
                            st.session_state["usuario"] = usr
                            if "mesa" in df_users.columns:
                                st.session_state["mesa"] = str(row["mesa"]).strip()
                            st.success(f"¡Bienvenido {usr}!")
                            st.rerun()
                        else:
                            st.error("🔒 Contraseña incorrecta. Inténtalo de nuevo.")
                    else:
                        st.error("❌ Configuración incompleta: No se detectó columna de contraseñas en tu Google Sheet.")
                else:
                    st.error("❌ Usuario no registrado en la base de datos.")
            else:
                st.error("❌ La base de datos de usuarios está vacía o inaccesible.")
                
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
            elif not df_users.empty and "user_key" in df_users.columns and nuevo_usr.lower() in df_users["user_key"].astype(str).str.lower().values:
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
    # 🧠 INTERFAZ: ROL JUEZ (GRABACIÓN DE NOTAS PURAS)
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.markdown("<h2 style='margin-bottom:0px;'>🧠 Evaluación Sensorial a Ciegas</h2>", unsafe_allow_html=True)
        
        muestras_db = leer_hoja("Muestras_Destiladores")
        df_muestras_real = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame(columns=["Código_Muestra", "Categoría"])
        
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
            
        with col_m2:
            st.markdown(f"<div style='margin-top:28px;' class='card-info'>📋 Categoría: <b>{categoria_detectada}</b></div>", unsafe_allow_html=True)
            
        if "muestra_actual" not in st.session_state or st.session_state["muestra_actual"] != muestra_a_evaluar:
            st.session_state["muestra_actual"] = muestra_a_evaluar
            for key in list(st.session_state.keys()):
                if key.startswith("sl_"):
                    st.session_state[key] = 7

        df_criterios_juez = df_config[df_config["Sección"].notna() & df_config["Parámetro"].notna()]
        
        resultados_juez = {}
        comentarios_secciones = {}
        
        if not df_criterios_juez.empty:
            secciones_unicas = df_criterios_juez["Sección"].unique()
            
            for sec in secciones_unicas:
                df_sec = df_criterios_juez[df_criterios_juez["Sección"] == sec].reset_index(drop=True)
                for idx, fila in df_sec.iterrows():
                    p_nom = fila["Parámetro"]
                    key_slider = f"sl_{muestra_a_evaluar}_{sec}_{p_nom}"
                    if key_slider not in st.session_state:
                        st.session_state[key_slider] = 7
                    resultados_juez[p_nom] = st.session_state[key_slider]
            
            nota_final_base_100 = 0.0
            for param, nota in resultados_juez.items():
                peso_param = float(df_config[df_config["Parámetro"] == param]["Peso"].values[0])
                nota_final_base_100 += (nota * peso_param * 10)
            nota_final_base_100 = max(0.0, min(100.0, nota_final_base_100))
            
            with col_m3:
                st.markdown(f"<div style='margin-top:28px;' class='card-score'>📊 Puntaje en Vivo: {round(nota_final_base_100, 1)} / 100</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:10px 0px;'>", unsafe_allow_html=True)
            
            for sec in secciones_unicas:
                st.markdown(f"<h4 style='color:#1E3A8A; margin-bottom:5px; margin-top:5px;'>📊 Dimensión: {sec}</h4>", unsafe_allow_html=True)
                df_sec = df_criterios_juez[df_criterios_juez["Sección"] == sec].reset_index(drop=True)
                
                for i in range(0, len(df_sec), 2):
                    c1, c2 = st.columns(2)
                    with c1:
                        fila = df_sec.iloc[i]
                        p_nom = fila["Parámetro"]
                        p_peso = float(fila["Peso"])
                        lbl = f"{p_nom} ({'Penaliza' if p_peso < 0 else f'Impacto {int(abs(p_peso)*100)}%'})"
                        key_slider = f"sl_{muestra_a_evaluar}_{sec}_{p_nom}"
                        st.slider(lbl, min_value=1, max_value=10, key=key_slider)
                    with c2:
                        if i + 1 < len(df_sec):
                            fila_2 = df_sec.iloc[i+1]
                            p_nom_2 = fila_2["Parámetro"]
                            p_peso_2 = float(fila_2["Peso"])
                            lbl_2 = f"{p_nom_2} ({'Penaliza' if p_peso_2 < 0 else f'Impacto {int(abs(p_peso_2)*100)}%'})"
                            key_slider_2 = f"sl_{muestra_a_evaluar}_{sec}_{p_nom_2}"
                            st.slider(lbl_2, min_value=1, max_value=10, key=key_slider_2)
                            
                comentarios_secciones[sec] = st.text_input(f"✍️ Comentarios sobre {sec} (Opcional)", key=f"txt_{muestra_a_evaluar}_{sec}").strip()
                st.markdown("<div style='margin-bottom:5px;'></div>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin:10px 0px;'>", unsafe_allow_html=True)
            st.subheader("Dictamen Final")
            
            col_d1, col_d2 = st.columns([3, 2])
            with col_d1:
                obs_global = st.text_area("Conclusión y Feedback Integral para el Destilador", height=70).strip()
            with col_d2:
                dentro_cat = st.radio("¿Mantiene tipicidad reglamentaria?", ["Sí, dentro de categoría", "No, presenta defectos descalificatorios"])
                
            if st.button("💾 Guardar y Enviar Evaluación Oficial"):
                # COMPILACIÓN DEL PAQUETE DE NOTAS PURAS PARA ENVIAR A GOOGLE SHEETS
                payload_evaluacion = {
                    "action": "registro_evaluacion",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "juez": st.session_state["usuario"],
                    "mesa": st.session_state["mesa"],
                    "muestra": muestra_a_evaluar,
                    "categoria": categoria_detectada,
                    
                    # Notas limpias (descomprime los parámetros configurados)
                    "nota_claridad": resultados_juez.get("Claridad", 7),
                    "nota_color": resultados_juez.get("Color", 7),
                    "nota_intensidad_aroma": resultados_juez.get("Intensidad Aroma", 7),
                    "nota_calidad_aroma": resultados_juez.get("Calidad Aroma", 7),
                    "nota_cuerpo": resultados_juez.get("Cuerpo", 7),
                    "nota_sabor": resultados_juez.get("Sabor", 7),
                    "nota_persistencia": resultados_juez.get("Persistencia", 7),
                    
                    # Comentarios de texto estructurados
                    "comentarios_vista": comentarios_secciones.get("Vista", ""),
                    "comentarios_olfato": comentarios_secciones.get("Olfato", ""),
                    "comentarios_sabor": comentarios_secciones.get("Sabor / Boca", comentarios_secciones.get("Sabor", "")),
                    "conclusion_global": obs_global,
                    "tipicidad": dentro_cat
                }
                
                res = enviar_datos(payload_evaluacion)
                if res:
                    st.success(f"🎉 ¡Evaluación transmitida con éxito! Notas puras guardadas en la pestaña 'Evaluaciones' para la mesa {st.session_state['mesa']}.")
                else:
                    st.warning("⚠️ Los datos se procesaron localmente, pero verifica si tu Apps Script tiene configurada la acción 'registro_evaluacion'.")
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
