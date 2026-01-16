import streamlit as st
import pandas as pd
import re
import calendar
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tutorías IES Arca Real", layout="wide", page_icon="📅")

# --- ESTILOS CSS (Para que el calendario se vea bien y tenga scroll) ---
st.markdown("""
<style>
    .day-cell {
        border: 1px solid #e0e0e0;
        height: 140px; 
        padding: 5px;
        margin: 2px;
        border-radius: 5px;
        background-color: #ffffff;
        overflow-y: auto; 
        font-family: sans-serif;
    }
    .day-header {
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
        font-size: 1.1em;
        text-align: right;
    }
    .event-card {
        background-color: #f0f2f6;
        border-left: 3px solid #ff4b4b;
        padding: 4px;
        margin-bottom: 4px;
        border-radius: 3px;
        font-size: 0.85em;
        line-height: 1.2;
        color: #000;
    }
    .event-time {
        font-weight: bold;
        color: #333;
        font-size: 0.9em;
        margin-bottom: 2px;
    }
    .current-day {
        border: 2px solid #ff4b4b !important;
        background-color: #fff5f5 !important;
    }
    /* Estilizar scrollbar para que sea finita */
    .day-cell::-webkit-scrollbar { width: 4px; }
    .day-cell::-webkit-scrollbar-thumb { background-color: #ccc; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES ---

def limpiar_nombre_materia(texto):
    """Deja el nombre de la materia limpio para el filtro (quita UTs y Grupos)."""
    if not isinstance(texto, str): return "Desconocida"
    # Quitar guiones y UTs
    texto_limpio = re.sub(r'\s*[-–]?\s*UT.*', '', texto, flags=re.IGNORECASE)
    # Quitar Grupos entre paréntesis
    texto_limpio = re.sub(r'\s*\(Grupo.*\)', '', texto_limpio, flags=re.IGNORECASE)
    return texto_limpio.strip()

def procesar_detalle(texto_original, texto_limpio):
    """Detecta qué información hemos borrado (UT, Grupo) para mostrarla luego."""
    if texto_original == texto_limpio:
        return "General"
    return texto_original.replace(texto_limpio, "").strip(" -–")

def parsear_fecha(fecha_str):
    """Convierte fechas complejas de Notion a objetos Python."""
    meses_map = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    try:
        match = re.search(r"(\d{1,2}) de ([a-zA-Z]+) de (\d{4})", str(fecha_str).lower())
        if not match: return None, None, None
        
        d, m_txt, a = match.groups()
        m_num = meses_map.get(m_txt)
        if not m_num: return None, None, None
        
        fecha = datetime.strptime(f"{a}-{m_num}-{d}", "%Y-%m-%d").date()
        horas = re.findall(r"(\d{1,2}:\d{2})", str(fecha_str))
        h_ini = horas[0] if horas else ""
        h_fin = horas[1] if len(horas) > 1 else ""
        
        return fecha, h_ini, h_fin
    except:
        return None, None, None

@st.cache_data
def cargar_datos():
    lista = []
    # Asegúrate de que estos archivos existen en tu GitHub/Carpeta
    archivos = [("cfgm.csv", "CFGM Gestión Admin."), ("cfgs.csv", "CFGS Admin. y Finanzas")]
    
    for archivo, ciclo in archivos:
        try:
            df = pd.read_csv(archivo)
            for _, row in df.iterrows():
                raw_nom = str(row.get('Nombre', ''))
                raw_fec = str(row.get('Fecha', ''))
                profe = str(row.get('Profesor/a', ''))
                
                nom_limpio = limpiar_nombre_materia(raw_nom)
                detalle = procesar_detalle(raw_nom, nom_limpio)
                fecha, ini, fin = parsear_fecha(raw_fec)
                
                if fecha:
                    lista.append({
                        "Ciclo": ciclo, "Materia": nom_limpio, "Detalle": detalle,
                        "Profesor": profe, "Fecha": fecha, "Inicio": ini, "Fin": fin
                    })
        except: continue
    return pd.DataFrame(lista)

# --- EJECUCIÓN PRINCIPAL ---
df = cargar_datos()

if df.empty:
    st.error("⚠️ No se han cargado datos. Verifica los archivos CSV.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🔍 Filtros")
ciclos = sorted(df['Ciclo'].unique())
sel_ciclo = st.sidebar.multiselect("Ciclo", ciclos, default=ciclos)
df_f = df[df['Ciclo'].isin(sel_ciclo)]

materias = sorted(df_f['Materia'].unique())
sel_mat = st.sidebar.multiselect("Materia", materias)
if sel_mat: df_f = df_f[df_f['Materia'].isin(sel_mat)]

ver_pasadas = st.sidebar.checkbox("Ver pasadas", False)
if not ver_pasadas: df_f = df_f[df_f['Fecha'] >= date.today()]

df_f = df_f.sort_values(['Fecha', 'Inicio'])

# --- DEFINICIÓN DE PESTAÑAS (Aquí estaba el error antes, ahora está incluido) ---
tab_cal, tab_lista = st.tabs(["📆 Calendario Visual", "📋 Agenda Lista"])

# --- PESTAÑA CALENDARIO ---
with tab_cal:
    c1, c2 = st.columns([1, 4])
    with c1:
        # Selectores de fecha
        hoy = date.today()
        mes_ver = st.selectbox("Mes", list(MESES_ES.keys()), index=hoy.month-1, format_func=lambda x: MESES_ES[x])
        anio_ver = st.number_input("Año", value=hoy.year)
    with c2:
        st.markdown(f"### {MESES_ES[mes_ver]} {anio_ver}")

    # Cabecera (Lunes - Domingo)
    cols = st.columns(7)
    for i, d in enumerate(DIAS_ES):
        cols[i].markdown(f"<div style='text-align:center; font-weight:bold;'>{d}</div>", unsafe_allow_html=True)

    # Dibujar días
    cal = calendar.monthcalendar(anio_ver, mes_ver)
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia == 0:
                    st.markdown('<div class="day-cell" style="background:#f9f9f9; border:none;"></div>', unsafe_allow_html=True)
                else:
                    fecha_actual = date(anio_ver, mes_ver, dia)
                    es_hoy = fecha_actual == date.today()
                    clase_hoy = "current-day" if es_hoy else ""
                    
                    eventos = df_f[df_f['Fecha'] == fecha_actual]
                    
                    # Crear HTML de tarjetas
                    html_tarjetas = ""
                    for _, ev in eventos.iterrows():
                        # Si es "General", no mostramos texto extra
                        txt_det = f"<br><span style='color:#666; font-weight:normal;'>{ev['Detalle']}</span>" if ev['Detalle'] != "General" else ""
                        
                        html_tarjetas += f"""
                        <div class="event-card">
                            <div class="event-time">{ev['Inicio']}</div>
                            <div>{ev['Materia']}{txt_det}</div>
                        </div>
                        """
                    
                    # HTML Final de la celda (SIN ESPACIOS AL INICIO para evitar errores)
                    st.markdown(f"""
<div class="day-cell {clase_hoy}">
<div class="day-header">{dia}</div>
{html_tarjetas}
</div>
""", unsafe_allow_html=True)

# --- PESTAÑA LISTA ---
with tab_lista:
    if df_f.empty: st.info("No hay clases con estos filtros.")
    for fecha, grupo in df_f.groupby('Fecha'):
        st.markdown(f"##### {DIAS_ES[fecha.weekday()]} {fecha.day} de {MESES_ES[fecha.month]}")
        for _, row in grupo.iterrows():
            st.success(f"⏰ **{row['Inicio']}** | {row['Materia']} ({row['Detalle']}) - {row['Profesor']}")
