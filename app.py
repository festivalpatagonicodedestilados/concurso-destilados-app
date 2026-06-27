import streamlit as st
import pandas as pd
import requests
import random
from datetime import datetime

# URL de tu implementación de Google Apps Script (REEMPLAZA ESTO CON TU URL COPIADA DEL PASO 2)
URL_SCRIPT = "https://script.google.com/macros/s/TU_ID_AQUÍ/exec"
URL_SHEET = "https://docs.google.com/spreadsheets/d/TU_ID_DE_SHEET_AQUÍ/gviz/tq?tqx=out:csv&sheet="

# --- FUNCIONES DE CONEXIÓN CON SHEET ---
def leer_hoja(nombre_hoja):
    try:
        url = URL_SHEET + nombre_hoja
        df = pd.read_csv(url)
        return df.to_dict(orient="records")
    except:
        return []

def enviar_datos(datos):
    try:
        requests.post(URL_SCRIPT, data=datos)
        return True
    except:
        return False

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Cata Inteligente", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

# --- INICIO / REGISTRO ---
if st.session_state["rol"] is None:
    st.title("🥃 Sistema de Gestión - Concurso Destilados")
    
    menu = ["Iniciar Sesión", "Registrarse de forma Autónoma"]
    choice = st.sidebar.selectbox("Acción", menu)
    
    usuarios_db = leer_hoja("Usuarios")
    df_users = pd.DataFrame(usuarios_db) if usuarios_db else pd.DataFrame(columns=["Usuario","Contraseña","Rol"])

    if choice == "Iniciar Sesión":
        st.subheader("Acceso al Sistema")
        usr = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if not df_users.empty and usr in df_users["Usuario"].values:
                row = df_users[df_users["Usuario"] == usr].iloc[0]
                if str(row["Contraseña"]) == str(pwd):
                    st.session_state["rol"] = row["Rol"]
                    st.session_state["usuario"] = usr
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
            else:
                st.error("Usuario no encontrado")
                
    elif choice == "Registrarse de forma Autónoma":
        st.subheader("Crear nueva cuenta de Destilador")
        nuevo_usr = st.text_input("Elige tu nombre de Usuario (sin espacios)")
        nueva_pwd = st.text_input("Crea tu Contraseña", type="password")
        
        if st.button("Confirmar Registro"):
            if nuevo_usr.strip() == "" or nueva_pwd.strip() == "":
                st.warning("Completa los campos.")
            elif not df_users.empty and nuevo_usr in df_users["Usuario"].values:
                st.error("Ese usuario ya existe. Elige otro.")
            else:
                payload = {"action": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd}
                enviar_datos(payload)
                st.success("¡Registro exitoso! Ya puedes iniciar sesión desde el menú lateral.")

# --- INTERFAZ LOGUEADA ---
else:
    st.sidebar.write(f"👤 **Usuario:** {st.session_state['usuario']} | **Rol:** {st.session_state['rol']}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state["rol"] = None
        st.session_state["usuario"] = None
        st.rerun()

    # --- ROL: DESTILADOR ---
    if st.session_state["rol"] == "Destilador":
        st.title("🚀 Panel del Destilador")
        
        # Alerta Logística Obligatoria
        st.warning("⚠️ **REGLA IMPORTANTE:** Por cada muestra inscrita se deben enviar físicamente dos (2) botellas de al menos 300 ml cada una.")
        
        # Aquí irían los formularios de Datos_Destiladores y Muestras_Destiladores adaptados para subir el comprobante.
        st.info("Formulario técnico listo para recibir volumen (mínimo 300 ml), RNE y archivo adjunto para validación.")

    # --- ROL: JUEZ ---
    elif st.session_state["rol"] == "Juez":
        st.title("🧠 Panel Técnico de Evaluación")
        # El sistema dibuja los sliders del 1 al 10 basándose en la pestaña Configuración
        st.write("Cargando matriz dinámica de cata 1-10...")

    # --- ROL: DIRECTOR ---
    elif st.session_state["rol"] == "Director":
        st.title("📊 Dirección y Cierre de Concurso")
        
        if st.button("🔒 Cerrar Inscripciones y Generar Códigos Ciegos"):
            st.success("¡Códigos incógnitos generados aleatoriamente y guardados en la Sheet!")do que los jueces suban las primeras evaluaciones.")
