import streamlit as st
import pandas as pd
import requests
import io
import urllib.parse
import random
from datetime import datetime

# ==============================================================================
# 🔌 CONFIGURACIÓN DE CONEXIONES CON GOOGLE SHEETS
# ==============================================================================
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxUj67JHjqpIjtbV3mxtz4QBRSH9Mu31Bcls9OuH2nllncpIq-6mvvH4sxEO_3ao2faIw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="
NUMERO_WHATSAPP = "5492914737608"

def enviar_datos(datos):
    try:
        response = requests.post(URL_SCRIPT, data=datos, timeout=25)
        if "OK" in response.text:
            return True
        return False
    except Exception as e:
        st.error(f"Error de red: {str(e)}")
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
# 🥃 CONFIGURACIÓN DE INTERFAZ Y CONTROL DE ESTADOS
# ==============================================================================
st.set_page_config(page_title="Inscripciones - Concurso Destilados", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False
if "mostrar_confirmacion_muestra" not in st.session_state:
    st.session_state["mostrar_confirmacion_muestra"] = False
if "info_muestra_creada" not in st.session_state:
    st.session_state["info_muestra_creada"] = {}

# 🎨 CSS AJUSTADO: Espacio superior garantizado para evitar superposición de banners
st.markdown("""
<style>
    .stApp { margin-top: 50px !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #1E3A8A; color: white; font-weight: bold; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 26px; text-align: center; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
    .success-box { background-color: #D1FAE5; padding: 20px; border-radius: 8px; border: 2px solid #10B981; color: #065F46; text-align: center; margin-bottom: 20px; }
    .whatsapp-btn { background-color: #25D366; color: white !important; font-weight: bold; padding: 12px; border-radius: 6px; text-align: center; text-decoration: none; display: inline-block; margin-top: 10px; width: 100%; border: none; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# Carga inicial de datos desde el Sheet
usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
destiladores_db = leer_hoja("Datos_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

# 📈 LEER COTIZACIÓN REAL DE LA PESTAÑA CONFIGURACION (Celda B2 / Fila 1)
cotizacion_hoy = 1000.0  # Respaldo por las dudas
if not df_config.empty and "Cotizacion" in df_config.columns:
    try:
        cotizacion_hoy = float(df_config["Cotizacion"].dropna().iloc[0])
    except:
        pass

categorias_disponibles = [str(x).strip() for x in df_config["Categorias"].dropna().unique() if str(x).strip() != ""] if not df_config.empty and "Categorias" in df_config.columns else ["Gin", "Whisky", "Vodka", "Ron"]

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Portal Oficial de Inscripciones</h1>", unsafe_allow_html=True)
    
    if st.session_state["mostrar_confirmacion_registro"]:
        st.markdown("""
        <div class='success-box'>
            <h3>🎉 ¡Cuenta Creada de Forma Exitosa!</h3>
            <p>El registro se completó en el servidor. Procede a ingresar tus datos en la pestaña de inicio de sesión.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👍 Entendido"):
            st.session_state["mostrar_confirmacion_registro"] = False
            st.rerun()

    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse como Nuevo Destilador"])
    
    with tab_login:
        usr = st.text_input("Nombre de Usuario", key="login_user").strip()
        pwd = st.text_input("Contraseña", type="password", key="login_pass").strip()
        
        if st.button("🚀 Ingresar al Portal", key="btn_login"):
            if usuarios_db:
                usr_input = str(usr).strip().lower()
                for row in usuarios_db:
                    row_clean = {str(k).strip().lower(): str(v).strip() for k, v in row.items()}
                    if row_clean.get("usuario", "").strip().lower() == usr_input:
                        if row_clean.get("contrasena", "").split('.')[0] == str(pwd).strip():
                            st.session_state["rol"] = "Destilador"
                            st.session_state["usuario"] = row_clean.get("usuario", usr).strip()
                            st.rerun()
            st.error("❌ Credenciales inválidas.")
            
    with tab_registro:
        nuevo_usr = st.text_input("Elige tu Nombre de Usuario", key="reg_user").strip().lower()
        nueva_pwd = st.text_input("Elige tu Contraseña", type="password", key="reg_pass").strip()
        
        if st.button("✨ Confirmar y Crear Cuenta", key="btn_registro"):
            if not nuevo_usr or not nueva_pwd:
                st.error("❌ Todos los campos son obligatorios.")
            elif " " in nuevo_usr:
                st.error("❌ El nombre de usuario no puede contener espacios.")
            elif usuarios_db and any(str(r.get("usuario", "")).strip().lower() == nuevo_usr for r in usuarios_db):
                st.error("❌ Nombre de usuario no disponible. Ya se encuentra registrado.")
            else:
                if enviar_datos({"action_real": "registro_usuario", "usuario": nuevo_usr, "contrasena": nueva_pwd, "rol": "Destilador"}):
                    st.session_state["mostrar_confirmacion_registro"] = True
                    st.rerun()

# ==============================================================================
# 🚀 ENTORNO INTERNO DEL USUARIO AUTENTICADO
# ==============================================================================
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['usuario']}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state["rol"] = None
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

    # 💥 PANTALLA DE CONFIRMACIÓN CORREGIDA (HTML Totalmente Renderizado)
    if st.session_state["mostrar_confirmacion_muestra"] and st.session_state["info_muestra_creada"]:
        info = st.session_state["info_muestra_creada"]
        
        if "producto" in info and "categoria" in info and "id_muestra" in info:
            monto_pesos = info['valor_usd'] * cotizacion_hoy
            
            # Formateamos el texto del mensaje para WhatsApp
            texto_wa = (
                f"🏆 *COPA ESPÍRITU DEL SUR*\n"
                f"Hola! Envío el comprobante de pago de mi inscripción:\n\n"
                f"🆔 *Código:* {info['id_muestra']}\n"
                f"🏬 *Destilería:* {nombre_destileria_global}\n"
                f"🥃 *Muestra:* {info['producto']} ({info['categoria']})\n"
                f"📊 *Muestra N°:* {info['nro_muestra']} (Lote {info['lote_nro']})\n"
                f"💰 *Arancel:* USD {info['valor_usd']} (${monto_pesos:,.0f} ARS)\n\n"
                f"⚠️ *Nota:* Adjunto el comprobante correspondiente a este código identificador."
            )
            texto_encoded = urllib.parse.quote(texto_wa)
            url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={texto_encoded}"
            
            # Procesamos todo el bloque visual completo con safe_allow_html activo
            st.markdown(f"""
            <div class='success-box'>
                <h2>🏆 ¡Muestra Registrada Exitosamente!</h2>
                <p style='font-size: 16px; color: #1E3A8A; font-weight: bold;'>Concurso: Copa Espíritu del Sur</p>
                <p style='font-size: 18px;'>Código asignado: <b style='color: #D97706;'>{info['id_muestra']}</b></p>
                
                <div style='background-color: #ffffff; padding: 15px; border-radius: 5px; margin: 10px 0; border: 1px solid #10B981; text-align: left; color: #333333;'>
                    📌 <b>Instrucciones de Pago y Aranceles:</b><br>
                    • Arancel de Inscripción: <span style='font-size: 18px; color: #1E3A8A; font-weight:bold;'>USD {info['valor_usd']} (${monto_pesos:,.0f} ARS)</span><br>
                    • 📊 <i>Calculado con el cambio cargado en el sistema: $ {cotizacion_hoy:,.2f} ARS por Dólar</i><br><br>
                    • 🏦 <b>Alias Cuenta Pesos:</b> <span style='font-family: monospace; background:#f4f4f4; padding:2px 5px; font-weight: bold;'>festivaldestiladores</span><br>
                    • 🏦 <b>Alias Cuenta Dólares:</b> <span style='font-family: monospace; background:#f4f4f4; padding:2px 5px; font-weight: bold;'>festivaldestiladores.usd</span><br><br>
                    ⚠️ <b>PAGOS MÚLTIPLES:</b> Si decides abonar varias muestras juntas en una misma transferencia, <b>debes ingresar el flujo de WhatsApp de cada muestra individualmente</b> y adjuntar el mismo comprobante en cada una. Esto es indispensable para asociar el pago al código <b>{info['id_muestra']}</b>.
                </div>
                <hr style='border: 1px solid #10B981;'>
                <p style='font-weight: bold; color: #065F46;'>⚠️ PASO FINAL OBLIGATORIO:</p>
                <p style='color: #065F46;'>Haz clic abajo para abrir WhatsApp y reportar el pago de esta muestra:</p>
                <a href='{url_wa}' target='_blank' class='whatsapp-btn'>📱 Enviar Comprobante por WhatsApp</a>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Hubo un problema al procesar los datos de la muestra de forma local.")
        
        if st.button("✅ Procesado / Cerrar Ventana"):
            st.session_state["mostrar_confirmacion_muestra"] = False
            st.session_state["info_muestra_creada"] = {}
            st.rerun()

    tab_perfil, tab_muestra, tab_estado = st.tabs(["📋 1. Perfil Destilería", "🥃 2. Inscribir Muestra", "📄 3. Estado de Mis Muestras"])

    with tab_perfil:
        st.subheader("📋 Información de Contacto")
        n_resp = st.text_input("Responsable Técnico", value=str(perfil_existente.get("responsable", ""))).strip()
        c_resp = st.text_input("Correo Oficial", value=str(perfil_existente.get("correo", ""))).strip()
        n_dest = st.text_input("Destilería / Razón Social", value=str(perfil_existente.get("destileria", ""))).strip()
        m_com = st.text_input("Marca Comercial", value=str(perfil_existente.get("marca", ""))).strip()
        n_rne = st.text_input("Número RNE", value=str(perfil_existente.get("rne", ""))).strip()
        u_loc = st.text_input("📍 Ubicación", value=str(perfil_existente.get("ubicacion", ""))).strip()
        t_tel = st.text_input("📞 WhatsApp", value=str(perfil_existente.get("telefono", ""))).strip()
        
        if st.button("💾 Guardar Datos del Perfil"):
            if not n_dest or not n_rne or not n_resp or not c_resp:
                st.error("❌ Los campos clave son obligatorios.")
            else:
                payload = {"action_real": "guardar_perfil", "usuario": st.session_state["usuario"], "responsable": n_resp, "correo": c_resp, "destileria": n_dest, "marca": m_com, "rne": n_rne, "ubicacion": u_loc, "telefono": t_tel}
                if enviar_datos(payload):
                    st.success("🎉 Perfil actualizado.")
                    st.rerun()
                    
        st.markdown("---")
        st.subheader("🔐 Modificar Contraseña")
        nueva_pass_input = st.text_input("Nueva contraseña de acceso", type="password").strip()
        
        if st.button("🔄 Actualizar Mi Contraseña"):
            if not nueva_pass_input:
                st.error("❌ Campo vacío.")
            else:
                payload_pwd = {"action_real": "actualizar_contrasena", "usuario": st.session_state["usuario"], "contrasena": nueva_pass_input}
                if enviar_datos(payload_pwd):
                    st.success("🎉 Contraseña modificada de manera exitosa en el servidor.")
                else:
                    st.error("❌ Error al actualizar en el servidor.")
                
    with tab_muestra:
        st.markdown(f"""
        <div class='card-warning'>
            <h4>⚠️ BASES LOGÍSTICAS - COPA ESPÍRITU DEL SUR</h4>
            Recuerda enviar físicamente las muestras requeridas por el reglamento. El costo unitario se calcula automáticamente según la fecha actual y la cantidad de muestras acumuladas.
            <br><b>Cotización de referencia actual (según tu Excel): $ {cotizacion_hoy:,.2f} ARS</b>
        </div>
        """, unsafe_allow_html=True)
        
        p_nom = st.text_input("Nombre Comercial del Producto", key="m_prod").strip()
        p_cat = st.selectbox("Categoría", categorias_disponibles, key="m_cat")
        p_rnpa = st.text_input("Registro RNPA", key="m_rnpa").strip()
        p_vol = st.number_input("Volumen (ml)", min_value=50, max_value=5000, value=750, step=50)
        
        if st.button("🔒 Confirmar e Inscribir Producto"):
            if not p_nom or not p_rnpa:
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
                    hoy = datetime.now().date()
                    
                    lote = 1
                    if datetime(2026, 8, 1).date() <= hoy <= datetime(2026, 8, 31).date():
                        lote = 2
                    elif hoy >= datetime(2026, 9, 1).date():
                        lote = 3
                        
                    if total_muestras <= 3:
                        precios = {1: 60, 2: 70, 3: 80}
                    elif 4 <= total_muestras <= 7:
                        precios = {1: 50, 2: 60, 3: 70}
                    else:
                        precios = {1: 45, 2: 55, 3: 65}
                        
                    valor_usd = precios[lote]
                    id_generado = f"DST-{random.randint(1000, 9999)}"
                    
                    payload_muestra = {
                        "action_real": "guardar_muestra", 
                        "id_muestra": id_generado,
                        "usuario": st.session_state["usuario"], 
                        "producto": p_nom, 
                        "categoria": p_cat, 
                        "rnpa": p_rnpa, 
                        "volumen": str(p_vol)
                    }
                    
                    if enviar_datos(payload_muestra):
                        st.session_state["info_muestra_creada"] = {
                            "id_muestra": id_generado, 
                            "producto": p_nom, 
                            "categoria": p_cat,
                            "valor_usd": valor_usd,
                            "lote_nro": lote,
                            "nro_muestra": total_muestras
                        }
                        st.session_state["mostrar_confirmacion_muestra"] = True
                        st.rerun()

    with tab_estado:
        st.subheader("📄 Historial Realizado")
        df_m = pd.DataFrame(muestras_db) if muestras_db else pd.DataFrame()
        
        if not df_m.empty:
            df_m.columns = [c.lower() for c in df_m.columns]
            mis_m = df_m[df_m["usuario"].astype(str).str.lower() == st.session_state["usuario"].lower()]
            
            if mis_m.empty:
                st.info("No hay registros vinculados.")
            else:
                cols_seguras = ["id_muestra", "producto", "categoría", "estado", "fecha"]
                cols_presentes = [c for c in cols_seguras if c in mis_m.columns]
                st.dataframe(mis_m[cols_presentes], use_container_width=True)
        else:
            st.info("Aún no has registrado ninguna muestra.")
