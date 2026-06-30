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
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbxUj67JHjqpIjtbV3mxtz4QBRSH9Mu31Bcls9OuH2nllncpIq-6mvvH4sxEO_3ao2faIw/exec"
BASE_URL_SHEET = "https://docs.google.com/spreadsheets/d/13Mtvg8celufTjtt6uF0lyPYC9Al4JsXqZQQQvGcPobw/export?format=csv&gid="
NUMERO_WHATSAPP = "5492914737608"
CBU_DOLARES = "3220001888027640440018"
ALIAS_PESOS = "festivaldestiladores"
EMAIL_ORGANIZACION = "festivalpatagonicodedestilados@gmail.com"

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
# 🥃 CONFIGURACIÓN DE INTERFAZ Y ESTILOS
# ==============================================================================
st.set_page_config(page_title="Inscripciones - Festival Patagónico de Destilados", page_icon="🥃", layout="wide")

if "rol" not in st.session_state:
    st.session_state["rol"] = None
    st.session_state["usuario"] = None

if "mostrar_confirmacion_registro" not in st.session_state:
    st.session_state["mostrar_confirmacion_registro"] = False
if "mostrar_confirmacion_muestra" not in st.session_state:
    st.session_state["mostrar_confirmacion_muestra"] = False
if "info_muestra_creada" not in st.session_state:
    st.session_state["info_muestra_creada"] = {}

# Diccionario global en memoria para recordar qué muestras ya fueron notificadas por WhatsApp
if "muestras_notificadas" not in st.session_state:
    st.session_state["muestras_notificadas"] = set()

# CSS inyectado para corregir el corte de scroll abajo del todo
st.markdown("""
<style>
    .stApp { margin-top: 50px !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 14rem !important; }
    .main-header { color: #1E3A8A; font-weight: bold; font-size: 26px; text-align: center; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 15px; border-radius: 6px; border-left: 4px solid #D97706; margin-bottom: 15px; color: #92400E; }
    .box-pago { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
    .badge-info-delay { background-color: #eff6ff; padding: 10px; border-radius: 6px; border-left: 4px solid #3b82f6; color: #1e40af; font-size: 14px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# Carga inicial de datos desde el Sheet
usuarios_db = leer_hoja("Usuarios")["datos"]
muestras_db = leer_hoja("Muestras_Destiladores")["datos"]
destiladores_db = leer_hoja("Datos_Destiladores")["datos"]
df_config = pd.DataFrame(leer_hoja("Configuracion")["datos"]) if leer_hoja("Configuracion")["datos"] else pd.DataFrame()

# 📈 CONTROL DE COTIZACIÓN
cotizacion_hoy = 1000.0
categorias_disponibles = ["Gin", "Whisky", "Vodka", "Ron"]

if not df_config.empty:
    columnas_originales = {c.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').strip(): c for c in df_config.columns}
    if "cotizacion" in columnas_originales:
        col_real = columnas_originales["cotizacion"]
        try:
            cotizacion_hoy = float(df_config[col_real].dropna().iloc[0])
        except:
            pass
    if "categorias" in columnas_originales:
        col_cat_real = columnas_originales["categorias"]
        categorias_disponibles = [str(x).strip() for x in df_config[col_cat_real].dropna().unique() if str(x).strip() != ""]

# Helper para calcular precio unitario según el total histórico
def calcular_arancel_muestra(nro_muestra):
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
# 🛟 BLOQUE DE SOPORTE PERMANENTE EN SIDEBAR (A PRUEBA DE FALLOS)
# ==============================================================================
st.sidebar.markdown("---")
with st.sidebar.expander("🚨 ¿Reportar Error o Consultas?", expanded=True):
    # Enlace mailto directo en el texto estático por si la lógica interactiva se congela
    st.sidebar.markdown(f"""
    <div style="background-color: #fee2e2; padding: 12px; border-radius: 6px; border-left: 4px solid #ef4444; color: #991b1b; font-size: 13px; margin-bottom: 10px;">
        ⚠️ <b>¿La app no responde o detectaste un error?</b><br>
        Haz clic abajo o escríbenos a nuestro correo oficial de soporte:
        <br><a href="mailto:{EMAIL_ORGANIZACION}" style="color:#b91c1c; font-weight:bold; font-family:monospace; text-decoration:underline;">{EMAIL_ORGANIZACION}</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 13px; margin-bottom: 5px;'>O utiliza el asistente pre-redactado:</p>", unsafe_allow_html=True)
    
    tipo_reporte = st.selectbox("Motivo del contacto:", ["Falla Técnica / Error en App", "Duda sobre Aranceles", "Consulta de Inscripción", "Otro"], key="sop_tipo")
    detalle_reporte = st.text_area("Describe el problema detalladamente:", height=70, key="sop_desc")
    
    if detalle_reporte.strip() != "":
        usuario_actual_tag = st.session_state["usuario"] if st.session_state["usuario"] else "Usuario no autenticado"
        asunto_mail = f"Soporte App - {tipo_reporte} ({usuario_actual_tag})"
        cuerpo_mail = f"Hola Organización,\n\nSe ha enviado una solicitud de soporte desde el portal web/móvil:\n\n• Usuario del portal: {usuario_actual_tag}\n• Motivo: {tipo_reporte}\n• Descripción del incidente:\n{detalle_reporte}\n\n---\nPortal de Gestión Copa Espíritu del Sur"
        
        asunto_enc = urllib.parse.quote(asunto_mail)
        cuerpo_enc = urllib.parse.quote(cuerpo_mail)
        url_mailto = f"mailto:{EMAIL_ORGANIZACION}?subject={asunto_enc}&body={cuerpo_enc}"
        
        st.link_button("📧 Redactar Correo Automático", url_mailto, use_container_width=True)
    else:
        st.info("Escribe el mensaje para habilitar el botón interactivo.")

# ==============================================================================
# 🔐 MÓDULO DE AUTENTICACIÓN
# ==============================================================================
if st.session_state["rol"] is None:
    st.markdown("<h1 class='main-header'>🥃 Festival Patagónico de Destilados<br><span style='font-size:22px;color:#D97706;font-weight:bold;'>Copa Espíritu del Sur</span></h1>", unsafe_allow_html=True)
    
    if st.session_state["mostrar_confirmacion_registro"]:
        st.success("🎉 ¡Cuenta Creada de Forma Exitosa! El registro se completó en el servidor. Procede a ingresar tus datos en la pestaña de inicio de sesión.")
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

    # Ventana emergente temporal al crear una muestra justo en el momento
    if st.session_state["mostrar_confirmacion_muestra"] and st.session_state["info_muestra_creada"]:
        info = st.session_state["info_muestra_creada"]
        st.success("🏆 ¡Muestra Registrada Exitosamente!")
        st.markdown(f"""
        <div style="background-color:#f0fdf4; padding:12px; border-radius:6px; margin-bottom:15px; border:1px solid #bbf7d0;">
            <p style="margin:0; font-size:15px; color:#374151;"><b>Concurso:</b> Festival Patagónico de Destilados</p>
            <p style="margin:5px 0 0 0; font-size:28px; color:#D97706; font-weight:bold;">🏆 Copa Espíritu del Sur</p>
            <p style="margin:8px 0 0 0; font-size:16px; color:#1e3a8a;"><b>Código asignado:</b> {info['id_muestra']}</p>
        </div>
        """, unsafe_allow_html=True)
        st.info("💡 Tu muestra ya figura en tu listado. Dirígete a la pestaña **'3. Estado de Mis Muestras'** en cualquier momento para reportar su pago o revisar la información.")
        if st.button("👍 Entendido / Continuar", type="primary"):
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

    with tab_muestra:
        txt_cotizacion_banner = f"$ {cotizacion_hoy:,.2f} ARS"
        st.markdown(f"""
        <div class="card-warning">
            <h4>⚠️ BASES LOGÍSTICAS - FESTIVAL PATAGÓNICO DE DESTILADOS</h4>
            Recuerda enviar físicamente las muestras requeridas por el reglamento. El costo unitario se calcula automáticamente según la cantidad de muestras acumuladas por tu destilería.
            <br><b>Cotización actual: {txt_cotizacion_banner}</b>
        </div>
        """, unsafe_allow_html=True)
        
        p_nom = st.text_input("Nombre Comercial del Producto (Ej: Gin London Dry, Vermut Rojo...)", key="m_prod").strip()
        p_cat = st.selectbox("Categoría del Espíritu", categorias_disponibles, key="m_cat")
        p_rnpa = st.text_input("Registro RNPA o Trámite", key="m_rnpa").strip()
        p_vol = st.number_input("Volumen de la Botella (ml)", min_value=50, max_value=5000, value=750, step=50)
        
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
                    valor_usd, lote = calcular_arancel_muestra(total_muestras)
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
        if os.path.exists("valores muestras.jpeg"):
            st.image("valores muestras.jpeg", caption="Folleto Oficial de Inscripciones", use_container_width=True)

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
            opciones_muestra = {f"{m.get('id_muestra', 'S/D')} — {m.get('producto', 'S/P')} ({m.get('categoria', 'S/C')})": m for m in mis_muestras_lista}
            seleccion_label = st.selectbox("👉 Selecciona la muestra específica que deseas abonar:", list(opciones_muestra.keys()))
            
            muestra_elegida = opciones_muestra[seleccion_label]
            idx_muestra = mis_muestras_lista.index(muestra_elegida) + 1
            valor_usd, lote_nro = calcular_arancel_muestra(idx_muestra)
            monto_pesos = valor_usd * cotizacion_hoy
            id_actual = str(muestra_elegida.get('id_muestra', ''))
            
            # Contenedor con las instrucciones de pago + Aclaración de 24/48 hs
            st.markdown(f"""
            <div class="box-pago">
                <p style="margin:0 0 8px 0; font-size:18px; color:#1E3A8A; font-weight:bold;">📋 Liquidación para el Código: {id_actual}</p>
                • <b>Arancel de Inscripción:</b> <span style="font-size: 16px; color: #065F46; font-weight:bold;">USD {valor_usd} (${monto_pesos:,.0f} ARS)</span><br>
                • 📊 <i>Calculado a la cotización actual: $ {cotizacion_hoy:,.2f} ARS por Dólar</i><br><br>
                • 🇺🇸 <b>CBU de Cuenta Dólares:</b> <span style="font-family: monospace; background:#e2e8f0; padding:3px 6px; font-weight: bold; font-size:14px; color:#1e3a8a;">{CBU_DOLARES}</span><br>
                • 🇦🇷 <b>Alias de Cuenta Pesos:</b> <span style="font-family: monospace; background:#f4f4f4; padding:3px 6px; font-weight: bold; font-size:14px; color:#065f46;">{ALIAS_PESOS}</span><br>
                • 👤 <b>Titular:</b> Festival Patagónico de Destilados<br><br>
                <div class="badge-info-delay">
                    ⏳ <b>Nota importante sobre los tiempos de acreditación:</b> La comprobación manual de las muestras y transferencias se realiza en un plazo de <b>24 a 48 horas</b> desde el envío del comprobante por WhatsApp. El estado definitivo impactará en tu historial una vez aprobado administrativamente.
                </div>
                <br>
                ⚠️ <b>PAGOS MÚLTIPLES:</b> Si abonas varias muestras en una misma transferencia, selecciona cada una en este menú desplegable individualmente y envíale el flujo de WhatsApp correspondiente adjuntando el mismo comprobante. Esto es vital para asociar el pago a cada código único.
            </div>
            """, unsafe_allow_html=True)
            
            # Mensaje de WhatsApp
            texto_wa = (
                f"🏆 *FESTIVAL PATAGÓNICO DE DESTILADOS - COPA ESPÍRITU DEL SUR*\n"
                f"Hola! Envío el comprobante de pago de mi inscripción:\n\n"
                f"🆔 *Código:* {id_actual}\n"
                f"🏬 *Destilería:* {nombre_destileria_global}\n"
                f"🥃 *Muestra:* {muestra_elegida.get('producto')} ({muestra_elegida.get('categoria')})\n"
                f"📊 *Muestra N°:* {idx_muestra} (Lote {lote_nro})\n"
                f"💰 *Arancel:* USD {valor_usd} (${monto_pesos:,.0f} ARS)\n\n"
                f"⚠️ *Nota:* Adjunto el comprobante correspondiente a este código identificador."
            )
            texto_encoded = urllib.parse.quote(texto_wa)
            url_wa = f"https://wa.me/{NUMERO_WHATSAPP}?text={texto_encoded}"
            
            st.warning(f"⚠️ **PASO FINAL OBLIGATORIO:** Haz clic abajo para reportar el pago de la muestra **{id_actual}** por WhatsApp:")
            
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
                
                cols_seguras = ["id_muestra", "producto", "categoria", "estado", "fecha"]
                cols_presentes = [c for c in cols_seguras if c in mis_m_filtradas.columns]
                
                st.dataframe(mis_m_filtradas[cols_presentes], use_container_width=True)
                st.caption("💡 *Nota: Si enviaste el comprobante de pago, el estado figurará como '⏳ Por comprobar' en tu pantalla de manera provisional. Aguarda de 24 a 48 hs hábiles a que la administración valide la transferencia.*")
            else:
                st.info("No hay registros vinculados.")
        else:
            st.info("Aún no has registrado ninguna muestra.")
