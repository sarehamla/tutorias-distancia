import streamlit as st
import pandas as pd
import re
import calendar
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda IES Arca Real", layout="centered", page_icon="📅")

# --- ESTILOS CSS (DISEÑO AGENDA PREMIUM) ---
st.markdown("""
<style>
    /* Importar fuentes bonitas: 'Patrick Hand' (manuscrita) y 'Roboto' (limpia) */
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Roboto:wght@300;400;700&display=swap');

    /* --- ESTILOS GENERALES --- */
    h1, h2, h3 { font-family: 'Roboto', sans-serif; }
    
    /* --- CALENDARIO (Vista Mensual) --- */
    .day-cell {
        border: 1px solid #f0f0f0;
        height: 100px;
        background-color: #ffffff;
        padding: 5px;
        border-radius: 8px;
        overflow-y: auto;
        font-family: 'Roboto', sans-serif;
    }
    .current-day-cell {
        border: 2px solid #ff6b6b !important;
        background-color: #fff0f0 !important;
    }
    .cal-event {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 2px 4px;
        margin-bottom: 2px;
        border-radius: 4px;
        font-size: 0.7em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border-left: 2px solid #1565c0;
    }

    /* --- AGENDA (VISTA TIMELINE) --- */
    
    /* Contenedor del día */
    .day-separator {
        font-family: 'Patrick Hand', cursive;
        font-size: 1.8em;
        color: #2c3e50;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 2px dashed #bdc3c7;
        padding-bottom: 5px;
    }

    /* Estructura del evento (Flexbox) */
    .timeline-row {
        display: flex;
        margin-bottom: 20px;
        position: relative;
    }

    /* Columna de Hora (Izquierda) */
    .time-col {
        width: 70px;
        text-align: right;
        padding-right: 15px;
        flex-shrink: 0;
    }
    .time-start {
        font-weight: 800;
        font-size: 1.1em;
        color: #333;
    }
    .time-end {
        font-size: 0.8em;
        color: #888;
    }

    /* Línea Vertical y Punto */
    .line-col {
        width: 20px;
        position: relative;
        display: flex;
        justify-content: center;
    }
    .line-vertical {
        width: 2px;
        background-color: #e0e0e0;
        height: 100%;
        position: absolute;
        top: 0;
    }
    .line-dot {
        width: 14px;
        height: 14px;
        background-color: #ff6b6b; /* Color del punto */
        border: 2px solid white;
        border-radius: 50%;
        position: relative;
        top: 5px;
        z-index: 2;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }

    /* Tarjeta de Contenido (Derecha) */
    .card-col {
        flex-grow: 1;
        background: white;
        padding: 15px 20px;
        border-radius: 0 12px 12px 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-left: 5px solid #ff6b6b; /* Borde de color */
        transition: transform 0.2s ease;
    }
    .card-col:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }
    
    .materia-title {
        font-family: 'Roboto', sans-serif;
        font-weight: 700;
        font-size: 1.1em;
        color: #2c3e50;
        margin-bottom: 4px;
    }
    .materia-detail {
        font-family: 'Patrick Hand', cursive; /* Detalle manuscrito */
        color: #666;
        font-size: 1.1em;
    }
    .prof-tag {
        display: inline-block;
        background-color: #f8f9fa;
        color: #555;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        margin-top: 8px;
        border: 1px solid #eee;
    }
    .ciclo-tag {
        font-size: 0.7em;
        color: #aaa;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
        display: block;
    }

    /* Scrollbar fina */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
MESES = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES ---
def limpiar_materia(txt):
    if not isinstance(txt, str): return "Desconocida"
    txt = re.sub(r'\s*[-–]?\s*UT.*', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s*\(Grupo.*\)', '', txt, flags=re.IGNORECASE)
    return txt.strip()

def extraer_detalle(original, limpio):
    if original == limpio: return "Clase General"
    det = original.replace(limpio, "").strip(" -–")
    return det if det else "Clase General"

def parsear_fecha(txt):
    if not isinstance(txt, str): return None, None, None
    try:
        match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)\s+de\s+(\d{4})", txt.lower())
        if not match: return None, None, None
        d, m_txt, a = match.groups()
        mes_map = {v.lower(): k for k, v in MESES.items()}
        m_num = mes_map.get(m_txt)
        if not m_num: return None, None, None
        fecha = date(int(a), m_num, int(d))
        horas = re.findall(r"(\d{1,2}:\d{2})", txt)
        ini = horas[0] if horas else "??"
        fin = horas[1] if len(horas) > 1 else ""
        return fecha, ini, fin
    except: return None, None, None

@st.cache_data
def cargar_datos():
    lista = []
    # NOMBRES DE TUS ARCHIVOS
    archivos = [("cfgm.csv", "CFGM Gestión"), ("cfgs.csv", "CFGS Finanzas")]
    for f_name, c_name in archivos:
        try:
            df = pd.read_csv(f_name)
            for _, row in df.iterrows():
                raw_n, raw_f, prof = str(row.get('Nombre','')), str(row.get('Fecha','')), str(row.get('Profesor/a',''))
                limpio = limpiar_materia(raw_n)
                det = extraer_detalle(raw_n, limpio)
                f, i, end = parsear_fecha(raw_f)
                if f: lista.append({"Ciclo":c_name, "Materia":limpio, "Detalle":det, "Profesor":prof, "Fecha":f, "Inicio":i, "Fin":end})
        except: continue
    return pd.DataFrame(lista)

# --- MAIN ---
df = cargar_datos()
if df.empty:
    st.error("Faltan los archivos CSV.")
    st.stop()

# --- FILTROS SIDEBAR ---
with st.sidebar:
    st.header("🗂️ Tu Planificador")
    ciclos = sorted(df['Ciclo'].unique())
    sel_ciclo = st.multiselect("Ciclo", ciclos, default=ciclos)
    df_f = df[df['Ciclo'].isin(sel_ciclo)]
    
    materias = sorted(df_f['Materia'].unique())
    sel_mat = st.multiselect("Asignatura", materias)
    if sel_mat: df_f = df_f[df_f['Materia'].isin(sel_mat)]

# --- VISTAS ---
st.title("📓 Agenda Escolar")
st.markdown("IES Arca Real - Modalidad Virtual")

tab_agenda, tab_cal = st.tabs(["✨ Agenda Visual", "📅 Calendario Mensual"])

# --- VISTA 1: AGENDA TIPO TIMELINE ---
with tab_agenda:
    hoy = date.today()
    # Filtro solo futuras
    df_view = df_f[df_f['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_view.empty:
        st.info("🎉 ¡Todo despejado! No tienes clases próximas.")
    
    # Iterar por días
    for fecha, grupo in df_view.groupby('Fecha'):
        dia_str = DIAS[fecha.weekday()]
        fecha_bonita = f"{dia_str}, {fecha.day} de {MESES[fecha.month]}"
        
        # Separador de día (Estilo manuscrito)
        st.markdown(f'<div class="day-separator">📌 {fecha_bonita}</div>', unsafe_allow_html=True)
        
        for _, row in grupo.iterrows():
            # Color del borde según ciclo (truco visual)
            color_borde = "#ff6b6b" if "CFGM" in row['Ciclo'] else "#4ecdc4"
            
            # HTML ESTRUCTURADO (Pegado a la izquierda para evitar error)
            st.markdown(f"""
<div class="timeline-row">
<div class="time-col">
<div class="time-start">{row['Inicio']}</div>
<div class="time-end">{row['Fin']}</div>
</div>
<div class="line-col">
<div class="line-vertical"></div>
<div class="line-dot" style="background-color: {color_borde};"></div>
</div>
<div class="card-col" style="border-left-color: {color_borde};">
<div class="materia-title">{row['Materia']}</div>
<div class="materia-detail">{row['Detalle']}</div>
<span class="prof-tag">👨‍🏫 {row['Profesor']}</span>
<span class="ciclo-tag">{row['Ciclo']}</span>
</div>
</div>
""", unsafe_allow_html=True)

# --- VISTA 2: CALENDARIO COMPACTO ---
with tab_cal:
    c1, c2 = st.columns([1,3])
    with c1:
        mes_v = st.selectbox("Mes", list(MESES.keys()), index=hoy.month-1, format_func=lambda x: MESES[x])
        anio_v = st.number_input("Año", value=hoy.year)
    
    # Matriz
    cal = calendar.monthcalendar(anio_v, mes_v)
    
    # Cabecera
    cols = st.columns(7)
    for i, d in enumerate(DIAS): cols[i].markdown(f"**{d[:3]}**")
    
    for sem in cal:
        cols = st.columns(7)
        for i, d in enumerate(sem):
            with cols[i]:
                if d != 0:
                    f_celda = date(anio_v, mes_v, d)
                    clase = "current-day-cell" if f_celda == hoy else ""
                    evs = df_f[df_f['Fecha'] == f_celda]
                    
                    html_evs = ""
                    for _, e in evs.iterrows():
                        html_evs += f'<div class="cal-event" title="{e["Materia"]}">{e["Inicio"]} {e["Materia"][:10]}..</div>'
                    
                    st.markdown(f"""<div class="day-cell {clase}"><div style="text-align:right; font-weight:bold; color:#aaa;">{d}</div>{html_evs}</div>""", unsafe_allow_html=True)
