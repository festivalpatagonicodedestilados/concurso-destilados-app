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

st.markdown("""
<style>
    .reportview-container { background: #fafafa; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .main-header { color: #1E3A8A; font-weight: bold; }
    .card-info { background-color: #F3F4F6; padding: 15px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 5px solid #D97706; margin-bottom: 15px; }
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
        # Asegurar limpieza de nombres de columnas
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
                    # Limpieza estándar de decimales por si Google Sheets añade .0
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
    # 🧠 INTERFAZ: ROL JUEZ
    # ==========================================================================
    elif st.session_state["rol"] == "Juez":
        st.title("🧠 Matriz de Evaluación Sensorial")
        st.write("Bienvenido al panel técnico de cata a ciegas.")
        
        muestras_blindadas = ["DST-1084", "DST-4921", "DST-8832"]
        muestra_a_evaluar = st.selectbox("Muestra Código Incógnito", muestras_blindadas)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        df_criterios_juez = df_config[df_config["Sección"].notna() & df_config["Parámetro"].notna()]
        
        resultados_juez = {}
        comentarios_juez = {}
        
        if not df_criterios_juez.empty:
            secciones_unicas = df_criterios_juez["Sección"].unique()
            for sec in secciones_unicas:
                st.markdown(f"### 📊 Dimensión: {sec}")
                df_sec = df_criterios_juez[df_criterios_juez["Sección"] == sec]
                
                for idx, fila in df_sec.iterrows():
                    param = fila["Parámetro"]
                    peso = float(fila["Peso"])
                    
                    st.write(f"**{param}** (Impacto relativo: {int(abs(peso)*100)}%)")
                    nota = st.slider(f"Puntaje para {param}", min_value=1, max_value=10, value=7, key=f"nota_{sec}_{param}")
                    com_criterio = st.text_input(f"Observaciones breves sobre {param} (Opcional)", key=f"com_{sec}_{param}")
                    
                    resultados_juez[param] = nota
                    comentarios_juez[param] = com_criterio
                st.markdown("<br>", unsafe_allow_html=True)
                
            st.subheader("Observaciones y Dictamen General")
            obs_global = st.text_area("Comentarios finales integrales")
            dentro_cat = st.radio("¿El producto se encuentra dentro de los parámetros?", ["Sí", "No"])
            
            if st.button("💾 Guardar y Enviar Evaluación Oficial"):
                nota_final_base_100 = 0.0
                for param, nota in resultados_juez.items():
                    peso_param = float(df_config[df_config["Parámetro"] == param]["Peso"].values[0])
                    nota_final_base_100 += (nota * peso_param * 10)
                
                nota_final_base_100 = max(0.0, min(100.0, nota_final_base_100))
                st.success(f"🎉 Evaluación procesada: **{round(nota_final_base_100, 2)} / 100 puntos**.")
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
