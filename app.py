import streamlit as st
import pandas as pd
import re
import calendar
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tutorías IES Arca Real", layout="wide", page_icon="📅")

# --- ESTILOS CSS PERSONALIZADOS (Para el calendario bonito) ---
st.markdown("""
<style>
    /* Estilo para la celda del calendario */
    .day-cell {
        border: 1px solid #e0e0e0;
        height: 140px; /* Altura fija para que no se descuadre */
        padding: 5px;
        margin: 2px;
        border-radius: 5px;
        background-color: #ffffff;
        overflow-y: auto; /* Scroll si hay muchas clases */
        font-family: sans-serif;
    }
    .day-header {
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
        font-size: 1.1em;
    }
    .event-card {
        background-color: #f0f2f6;
        border-left: 3px solid #ff4b4b;
        padding: 4px;
        margin-bottom: 4px;
        border-radius: 3px;
        font-size: 0.8em;
        line-height: 1.2;
    }
    .event-time {
        font-weight: bold;
        color: #555;
        font-size: 0.9em;
    }
    .current-day {
        border: 2px solid #ff4b4b !important;
        background-color: #fff5f5 !important;
    }
    /* Ocultar barra de scroll fea en celdas */
    .day-cell::-webkit-scrollbar {
        width: 4px;
    }
    .day-cell::-webkit-scrollbar-thumb {
        background-color: #ccc;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES DE IDIOMA ---
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES DE LIMPIEZA ---

def limpiar_nombre_materia(texto):
    """
    Limpia agresivamente el nombre de la materia para los filtros.
    Elimina ' - UT...', ' UT...', ' (Grupo...)' y espacios extra.
    """
    if not isinstance(texto, str):
        return "Desconocida"
    
    # 1. Quitar patrón " - UT..." o " UT..." (con o sin guión)
    # Busca "UT" seguido de cualquier cosa hasta el final
    texto_limpio = re.sub(r'\s*[-–]?\s*UT.*', '', texto, flags=re.IGNORECASE)
    
    # 2. Quitar información de grupos entre paréntesis ej: "(Grupo A)"
    texto_limpio = re.sub(r'\s*\(Grupo.*\)', '', texto_limpio, flags=re.IGNORECASE)
    
    # 3. Quitar comillas extra si las hay
    texto_limpio = texto_limpio.replace('"', '').strip()
    
    return texto_limpio

def procesar_detalle(texto_original, texto_limpio):
    """
    Extrae lo que hemos borrado (UT, Grupo) para ponerlo en el detalle.
    """
    if texto_original == texto_limpio:
        return "General"
    # Devuelve la parte que diferencia el original del limpio
    return texto_original.replace(texto_limpio, "").strip(" -–")

def parsear_fecha(fecha_str):
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
    lista_datos = []
    # NOMBRES EXACTOS DE TUS ARCHIVOS
    archivos = [("cfgm.csv", "CFGM Gestión Admin."), ("cfgs.csv", "CFGS Admin. y Finanzas")]
    
    for archivo, ciclo in archivos:
        try:
            df = pd.read_csv(archivo)
            for _, row in df.iterrows():
                raw_nom = str(row.get('Nombre', ''))
                raw_fec = str(row.get('Fecha', ''))
                profe = str(row.get('Profesor/a', ''))
                
                # Limpieza mejorada
                nom_limpio = limpiar_nombre_materia(raw_nom)
                detalle = procesar_detalle(raw_nom, nom_limpio)
                
                fecha, ini, fin = parsear_fecha(raw_fec)
                
                if fecha:
                    lista_datos.append({
                        "Ciclo": ciclo,
                        "Materia": nom_limpio,
                        "Detalle": detalle,
                        "Profesor": profe,
                        "Fecha": fecha,
                        "Inicio": ini,
                        "Fin": fin
                    })
        except:
            continue
            
    return pd.DataFrame(lista_datos)

# --- CARGA Y FILTROS ---
df = cargar_datos()

if df.empty:
    st.error("⚠️ No hay datos. Sube 'cfgm.csv' y 'cfgs.csv' al repositorio.")
    st.stop()

st.sidebar.header("🔍 Configuración")

# 1. Filtro Ciclo
ciclos = sorted(df['Ciclo'].unique())
sel_ciclo = st.sidebar.multiselect("Ciclo", ciclos, default=ciclos)
df_f = df[df['Ciclo'].isin(sel_ciclo)]

# 2. Filtro Materia (Ahora sí, 100% únicos)
materias = sorted(df_f['Materia'].unique())
sel_materia = st.sidebar.multiselect("Asignatura", materias)
if sel_materia:
    df_f = df_f[df_f['Materia'].isin(sel_materia)]

# 3. Filtro Fecha
ver_pasadas = st.sidebar.checkbox("Ver pasadas", False)
if not ver_pasadas:
    df_f = df_f[df_f['Fecha'] >= date.today()]

df_f = df_f.sort_values(['Fecha', 'Inicio'])

# --- VISTAS ---
tab_cal, tab_lista = st.tabs(["📆 Calendario Visual", "📋 Lista / Agenda"])

# --- PESTAÑA CALENDARIO ---
with tab_cal:
    col_nav1, col_nav2 = st.columns([1, 4])
    with col_nav1:
        mes_ver = st.selectbox("Mes", list(MESES_ES.keys()), index=date.today().month-1, format_func=lambda x: MESES_ES[x])
        anio_ver = st.number_input("Año", value=date.today().year, step=1)
    
    with col_nav2:
        st.markdown(f"### {MESES_ES[mes_ver]} {anio_ver}")
    
    # Cabecera días
    cols = st.columns(7)
    for i, d in enumerate(DIAS_ES):
        cols[i].markdown(f"**{d}**", unsafe_allow_html=True)
    
    # Matriz calendario
    cal = calendar.monthcalendar(anio_ver, mes_ver)
    
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            with cols[i]:
                if dia == 0:
                    st.markdown('<div class="day-cell" style="background: #f9f9f9;"></div>', unsafe_allow_html=True)
                else:
                    fecha_celda = date(anio_ver, mes_ver, dia)
                    es_hoy = fecha_celda == date.today()
                    clase_extra = "current-day" if es_hoy else ""
                    
                    # Buscar eventos
                    eventos = df_f[df_f['Fecha'] == fecha_celda]
                    
                    # Construir HTML interno de la celda
                    html_eventos = ""
                    for _, ev in eventos.iterrows():
                        html_eventos += f"""
                        <div class="event-card">
                            <div class="event-time">{ev['Inicio']}</div>
                            <div>{ev['Materia']}</div>
                            <div style="font-size:0.7em; color:#666;">{ev['Detalle']}</div>
                        </div>
                        """
                    
                    st.markdown(f"""
                    <div class="day-cell {clase_extra}">
                        <div class="day-header">{dia}</div>
                        {html_eventos}
                    </div>
                    """, unsafe_allow_html=True)

# --- PESTAÑA LISTA ---
with tab_lista:
    for fecha, grupo in df_f.groupby('Fecha'):
        st.markdown(f"##### 📅 {fecha.strftime('%d-%m-%Y')}")
        for _, row in grupo.iterrows():
            st.info(f"⏰ **{row['Inicio']}** | {row['Materia']} ({row['Detalle']}) - {row['Profesor']}")
