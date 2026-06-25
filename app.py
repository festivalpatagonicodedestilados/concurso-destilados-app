import streamlit as st
import pandas as pd
import requests
import random

# --- CONFIGURACIÓN DE CONEXIÓN A GOOGLE APP SCRIPT ---
try:
    URL_SCRIPT = st.secrets["url_google_script"]
except Exception:
    st.error("Falta configurar la URL del script en los Secrets de Streamlit.")
    st.stop()

# --- FUNCIONES AUXILIARES DE CONEXIÓN (Cerebro del sistema) ---
def leer_hoja(nombre_pestana):
    """Lee todos los datos de una pestaña específica en Google Sheets"""
    try:
        response = requests.post(URL_SCRIPT, json={"action": "read", "sheet": nombre_pestana}, timeout=10)
        if response.status_code == 200:
            datos = response.json()
            if isinstance(datos, dict) and datos.get("status") == "error":
                return []
            return datos
        return []
    except Exception:
        return []

def escribir_hoja(nombre_pestana, fila_datos):
    """Añade una nueva fila de datos a una pestaña específica en Google Sheets"""
    try:
        response = requests.post(URL_SCRIPT, json={"action": "append", "sheet": nombre_pestana, "row": fila_datos}, timeout=10)
        if response.status_code == 200:
            return True
        return False
    except Exception:
        return False

def cambiar_password_hoja(usuario, nueva_clave):
    """Envía la solicitud a Google Sheets para actualizar la contraseña (Guardado para el futuro)"""
    try:
        payload = {
            "action": "update_password", 
            "sheet": "Usuarios", 
            "usuario": usuario, 
            "nueva_contrasena": nueva_clave
        }
        response = requests.post(URL_SCRIPT, json=payload, timeout=10)
        if response.status_code == 200:
            datos = response.json()
            if datos.get("status") == "success":
                return True
        return False
    except Exception:
        return False

# --- CARGA DINÁMICA DE CATEGORÍAS ---
records_config = leer_hoja("Configuracion")
if records_config:
    df_config = pd.DataFrame(records_config)
    if not df_config.empty and "Categorias" in df_config.columns:
        CATEGORIAS_CONCURSO = df_config["Categorias"].dropna().astype(str).tolist()
    else:
        CATEGORIAS_CONCURSO = ["Gin", "Whisky", "Vodka", "Ron"]
else:
    CATEGORIAS_CONCURSO = ["Gin", "Whisky", "Vodka", "Ron"]

# --- CONFIGURACIÓN DE LA PÁGINA MÓVIL ---
st.set_page_config(page_title="Concurso Destilados", layout="centered")

# Muestra el logo guardado en GitHub en la parte superior de la App
st.image("logo.png", use_container_width=True)

# Inicializar estados de la sesión para el sistema de Login
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

# --- PANTALLA 1: INICIO DE SESIÓN ---
if not st.session_state["autenticado"]:
    st.title("🏆 Concurso de Destilados")
    st.subheader("Control de Acceso")
    
    usuario_input = st.text_input("Usuario:")
    clave_input = st.text_input("Contraseña:", type="password")
    
    if st.button("Ingresar"):
        records_usuarios = leer_hoja("Usuarios")
        if records_usuarios:
            df_users = pd.DataFrame(records_usuarios)
            
            user_row = df_users[(df_users["Usuario"].astype(str) == usuario_input) & (df_users["Contraseña"].astype(str) == str(clave_input))]
            
            if not user_row.empty:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario_input
                st.session_state["rol"] = user_row.iloc[0]["Rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        else:
            st.error("No se pudo conectar con la base de datos de usuarios. Verifica las pestañas de tu Sheet.")

# --- PANTALLAS CON SESIÓN ACTIVA ---
else:
    # Barra lateral móvil para cerrar sesión
    st.sidebar.write(f"👤 Usuario: **{st.session_state['usuario']}**")
    st.sidebar.write(f"🎖️ Rol: **{st.session_state['rol']}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["rol"] = ""
        st.rerun()

    # -------------------------------------------------------------
    # ROL: DESTILADOR (Perfil obligatorio + Inscripción Oculta)
    # -------------------------------------------------------------
    if st.session_state["rol"] == "Destilador":
        st.title("🧪 Panel del Destilador")
        
        records_datos = leer_hoja("Datos_Destiladores")
        perfil_completado = False
        
        if records_datos:
            df_datos = pd.DataFrame(records_datos)
            if st.session_state["usuario"] in df_datos["Usuario"].values:
                perfil_completado = True

        if not perfil_completado:
            st.warning("⚠️ Para continuar, debes completar el registro de tu destilería obligatoriamente.")
            with st.form("form_datos_personales"):
                st.subheader("📝 Datos de la Destilería")
                nombre_resp = st.text_input("Nombre completo del Responsable:")
                nombre_dest = st.text_input("Nombre de la Destilería / Marca:")
                ciudad_pais = st.text_input("Ciudad y País:")
                telefono = st.text_input("Teléfono de contacto:")
                email = st.text_input("Correo electrónico:")
                
                guardar_perfil = st.form_submit_button("Guardar y Activar Cuenta")
                
                if guardar_perfil:
                    if nombre_resp and nombre_dest and ciudad_pais and telefono and email:
                        exito = escribir_hoja("Datos_Destiladores", [
                            st.session_state["usuario"], nombre_resp, nombre_dest, ciudad_pais, telefono, email
                        ])
                        if exito:
                            st.success("¡Datos guardados! Tu cuenta ha sido activada.")
                            st.rerun()
                        else:
                            st.error("Error al escribir en la base de datos.")
                    else:
                        st.error("Todos los campos son obligatorios.")

        else:
            tab_registro, tab_mis_muestras = st.tabs(["📝 Inscribir Producto", "📋 Mis Inscripciones"])
            
            with tab_registro:
                with st.form("form_registro_muestra", clear_on_submit=True):
                    nombre_destilado = st.text_input("Nombre comercial del destilado:")
                    categoria = st.selectbox("Categoría del Producto:", CATEGORIAS_CONCURSO)
                    
                    enviar_muestra = st.form_submit_button("Confirmar Inscripción")
                    
                    if enviar_muestra:
                        if nombre_destilado:
                            codigo_incognito = f"DST-{random.randint(1000, 9999)}"
                            exito = escribir_hoja("Muestras_Destiladores", [
                                st.session_state["usuario"], nombre_destilado, categoria, codigo_incognito
                            ])
                            if exito:
                                st.success(f"¡Tu producto '{nombre_destilado}' ha sido inscrito exitosamente!")
                                st.info("La organización se encargará del etiquetado oficial anónimo.")
                            else:
                                st.error("Error al registrar el producto.")
                        else:
                            st.error("Debes ingresar el nombre de tu destilado.")
                            
            with tab_mis_muestras:
                st.write("### Tus productos inscritos:")
                records_muestras = leer_hoja("Muestras_Destiladores")
                if records_muestras:
                    df_m = pd.DataFrame(records_muestras)
                    df_mis_m = df_m[df_m["Destilador"] == st.session_state["usuario"]]
                    st.dataframe(df_mis_m[["Nombre_Destilado", "Categoría"]], use_container_width=True)
                else:
                    st.info("Aún no tienes productos inscritos.")

    # -------------------------------------------------------------
    # ROL: JUEZ (Evaluación ciega con Filtros de No Repetición + Observaciones)
    # -------------------------------------------------------------
    elif st.session_state["rol"] == "Juez":
        st.title("✍️ Evaluación de Muestras")
        juez_actual = st.session_state["usuario"]
        
        # 1. Leer todas las muestras y las evaluaciones ya asentadas
        records_muestras = leer_hoja("Muestras_Destiladores")
        records_evaluaciones = leer_hoja("Evaluaciones")
        
        df_m = pd.DataFrame(records_muestras) if records_muestras else pd.DataFrame()
        df_e = pd.DataFrame(records_evaluaciones) if records_evaluaciones else pd.DataFrame()
        
        # Obtener lista de muestras que este juez ya evaluó
        muestras_ya_evaluadas = []
        if not df_e.empty and "Juez" in df_e.columns and "Muestra" in df_e.columns:
            muestras_ya_evaluadas = df_e[df_e["Juez"] == juez_actual]["Muestra"].astype(str).tolist()
        
        # Filtrar muestras disponibles (que no haya evaluado este juez)
        if not df_m.empty and "Código_Muestra" in df_m.columns:
            df_disponibles = df_m[~df_m["Código_Muestra"].astype(str).isin(muestras_ya_evaluadas)]
        else:
            df_disponibles = pd.DataFrame()
            
        # Filtrar categorías que tienen muestras pendientes para este juez
        if not df_disponibles.empty and "Categoría" in df_disponibles.columns:
            categorias_pendientes = df_disponibles["Categoría"].unique().tolist()
            categorias_filtradas = [cat for cat in CATEGORIAS_CONCURSO if cat in categorias_pendientes]
        else:
            categorias_filtradas = []
            
        # Interfaz visual del Juez dependiente de muestras pendientes
        if categorias_filtradas:
            categoria_seleccionada = st.selectbox("Selecciona la Categoría a evaluar:", categorias_filtradas)
            
            muestras_categoria = df_disponibles[df_disponibles["Categoría"] == categoria_seleccionada]["Código_Muestra"].astype(str).tolist()
            
            if muestras_categoria:
                with st.form("form_evaluacion", clear_on_submit=True):
                    id_muestra = st.selectbox("Selecciona el Código de la Muestra:", muestras_categoria)
                    
                    st.divider()
                    st.write("### Criterios de Evaluación (1 al 10)")
                    aroma = st.slider("Aroma:", 1, 10, 5)
                    sabor = st.slider("Sabor:", 1, 10, 5)
                    apariencia = st.slider("Apariencia:", 1, 10, 5)
                    final = st.slider("Final / Postgusto:", 1, 10, 5)
                    
                    st.divider()
                    observaciones = st.text_area("📝 Observaciones / Notas de cata (Opcional):", max_chars=300)
                    
                    enviar_eval = st.form_submit_button("Guardar Evaluación")
                    
                    if enviar_eval:
                        puntaje_total = aroma + sabor + apariencia + final
                        exito = escribir_hoja("Evaluaciones", [
                            juez_actual, id_muestra, categoria_seleccionada, 
                            aroma, sabor, apariencia, final, puntaje_total, observaciones
                        ])
                        if exito:
                            st.success(f"🎉 ¡Evaluación de la muestra {id_muestra} guardada con éxito!")
                            st.rerun()
                        else:
                            st.error("Error al guardar la evaluación en la base de datos.")
            else:
                st.info(f"¡Al día! No tienes muestras pendientes en {categoria_seleccionada}.")
        else:
            st.balloons()
            st.success("🏆 ¡Felicitaciones! Has evaluado todas las muestras disponibles en el concurso.")

    # -------------------------------------------------------------
    # ROL: DIRECTOR (Resultados calculados, Podio y Descarga)
    # -------------------------------------------------------------
    elif st.session_state["rol"] == "Director":
        st.title("📊 Panel de Control General")
        
        tab1, tab2 = st.tabs(["🥇 Podios por Categoría", "📄 Planilla Completa"])
        
        records_eval = leer_hoja("Evaluaciones")
        if records_eval:
            df_res = pd.DataFrame(records_eval)
            
            with tab1:
                st.header("Ranking en Tiempo Real")
                df_res["Puntaje Total"] = pd.to_numeric(df_res["Puntaje Total"])
                
                df_ranking = df_res.groupby(["Categoría", "Muestra"])["Puntaje Total"].mean().reset_index()
                df_ranking = df_ranking.sort_values(by=["Categoría", "Puntaje Total"], ascending=[True, False])
                
                for cat in df_ranking["Categoría"].unique():
                    st.write(f"#### 🥃 Categoría: {cat}")
                    df_cat = df_ranking[df_ranking["Categoría"] == cat].head(3).reset_index(drop=True)
                    df_cat.index = df_cat.index + 1
                    st.dataframe(df_cat.rename(columns={"Puntaje Total": "Promedio"}), use_container_width=True)
            
            with tab2:
                st.header("Todas las Evaluaciones Registradas")
                st.dataframe(df_res, use_container_width=True)
                
                csv = df_res.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Planilla Completa (CSV)", csv, "resultados_concurso.csv", "text/csv")
        else:
            st.info("Esperando que los jueces suban las primeras evaluaciones.")
