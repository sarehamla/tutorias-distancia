import streamlit as st
import pandas as pd
import re
import calendar
import hashlib
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda IES Arca Real", layout="centered", page_icon="📓")

# --- PALETA DE COLORES ESTILO MOLESKINE (Tonos sobrios y elegantes) ---
COLORES_MOLESKINE = [
    "#E74C3C", "#8E44AD", "#3498DB", "#16A085", "#F39C12", "#D35400", 
    "#2C3E50", "#27AE60", "#7F8C8D", "#C0392B", "#2980B9", "#884EA0"
]

def get_color_materia(texto):
    """Genera un color único y consistente para cada asignatura basado en su nombre."""
    if not isinstance(texto, str): return "#333"
    # Usamos un hash para que 'Inglés' siempre de el mismo color, por ejemplo.
    hash_obj = hashlib.md5(texto.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return COLORES_MOLESKINE[hash_int % len(COLORES_MOLESKINE)]

# --- ESTILOS CSS (MOLESKINE VIBES) ---
st.markdown("""
<style>
    /* Fuente elegante con serifa para títulos (Playfair Display) y limpia para texto (Lato) */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400;700&display=swap');

    /* Fondo general sutilmente crema (simulado en bloques) */
    .stApp {
        background-color: #fdfbf7; 
    }

    h1, h2, h3, h4 { font-family: 'Playfair Display', serif; color: #2c3e50; }
    
    /* --- AGENDA TIMELINE --- */
    
    .day-separator {
        font-family: 'Playfair Display', serif;
        font-size: 1.5em;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 35px;
        margin-bottom: 20px;
        border-bottom: 1px solid #d0d0d0;
        padding-bottom: 5px;
        letter-spacing: 0.5px;
    }

    .timeline-row {
        display: flex;
        margin-bottom: 15px;
        align-items: stretch;
    }

    /* Columna Hora */
    .time-col {
        width: 65px;
        text-align: right;
        padding-right: 15px;
        padding-top: 15px;
        font-family: 'Lato', sans-serif;
        color: #7f8c8d;
        font-size: 0.9em;
    }

    /* Línea Vertical */
    .line-col {
        width: 20px;
        position: relative;
        display: flex;
        justify-content: center;
    }
    .line-vertical {
        width: 1px;
        background-color: #bdc3c7;
        height: 100%;
        position: absolute;
        top: 0;
    }
    .line-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        position: relative;
        top: 20px;
        z-index: 2;
        border: 2px solid #fdfbf7; /* Mismo color que el fondo para efecto recorte */
    }

    /* Tarjeta Moleskine */
    .card-col {
        flex-grow: 1;
        background-color: #faf9f6; /* Blanco roto / Hueso */
        padding: 15px 20px;
        border-radius: 4px; /* Bordes menos redondeados, más libreta */
        border: 1px solid #e0e0e0;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.03); /* Sombra muy sutil */
        margin-bottom: 5px;
        border-left-width: 4px;
        border-left-style: solid;
        transition: transform 0.2s;
    }
    .card-col:hover {
        transform: translateX(3px);
        box-shadow: 3px 3px 8px rgba(0,0,0,0.06);
    }

    .materia-title {
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 1.1em;
        color: #2c3e50;
        margin-bottom: 2px;
    }
    .materia-detail {
        font-family: 'Lato', sans-serif;
        font-weight: 300;
        font-size: 0.95em;
        color: #555;
        font-style: italic;
    }
    .meta-info {
        margin-top: 10px;
        font-size: 0.75em;
        color: #95a5a6;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* --- CALENDARIO --- */
    .day-cell {
        background-color: #faf9f6;
        border: 1px solid #e0e0e0;
        border-radius: 3px;
        height: 100px;
        padding: 4px;
        overflow-y: auto;
        font-family: 'Lato', sans-serif;
    }
    .day-header {
        font-family: 'Playfair Display', serif;
        text-align: right;
        font-weight: bold;
        color: #7f8c8d;
    }
    .cal-event {
        font-size: 0.75em;
        padding: 2px 4px;
        margin-bottom: 2px;
        border-radius: 2px;
        color: white; /* Texto blanco para resaltar sobre color fondo */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .current-day-cell {
        background-color: #fff !important;
        border: 2px solid #2c3e50 !important;
    }
    
    /* Scrollbars elegantes */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 2px; }

</style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
MESES = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES DE PARSEO ---
def limpiar_materia(txt):
    if not isinstance(txt, str): return "Desconocida"
    txt = re.sub(r'\s*[-–]?\s*UT.*', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s*\(Grupo.*\)', '', txt, flags=re.IGNORECASE)
    return txt.strip()

def extraer_detalle(original, limpio):
    if original == limpio: return "General"
    det = original.replace(limpio, "").strip(" -–")
    return det if det else "General"

def parsear_fecha(txt):
    if not isinstance(txt, str): return None, None, None
    try:
        match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)\s+de\s+(\d{4})", txt.lower())
        if not match: return None, None, None
        d, m_txt, a = match.groups()
        mes_map = {v.lower(): k for k, v in MESES.items()}
        m_num = mes_map.get(m_txt)
        if not m_num: return None, None, None
        return date(int(a), m_num, int(d)), re.findall(r"(\d{1,2}:\d{2})", txt)[0], re.findall(r"(\d{1,2}:\d{2})", txt)[1] if len(re.findall(r"(\d{1,2}:\d{2})", txt))>1 else ""
    except: return None, None, None

@st.cache_data
def cargar_datos():
    lista = []
    archivos = [("cfgm.csv", "CFGM Gestión"), ("cfgs.csv", "CFGS Finanzas")]
    for f_name, c_name in archivos:
        try:
            df = pd.read_csv(f_name)
            for _, row in df.iterrows():
                r_n, r_f, prof = str(row.get('Nombre','')), str(row.get('Fecha','')), str(row.get('Profesor/a',''))
                limpio = limpiar_materia(r_n)
                f, i, end = parsear_fecha(r_f)
                if f: lista.append({"Ciclo":c_name, "Materia":limpio, "Detalle":extraer_detalle(r_n, limpio), "Profesor":prof, "Fecha":f, "Inicio":i, "Fin":end})
        except: continue
    return pd.DataFrame(lista)

# --- MAIN ---
df = cargar_datos()
if df.empty:
    st.error("No se encontraron los archivos CSV.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2965/2965358.png", width=50)
    st.markdown("### Filtros")
    ciclos = sorted(df['Ciclo'].unique())
    sel_ciclo = st.multiselect("Ciclo", ciclos, default=ciclos)
    df_f = df[df['Ciclo'].isin(sel_ciclo)]
    
    materias = sorted(df_f['Materia'].unique())
    sel_mat = st.multiselect("Asignatura", materias)
    if sel_mat: df_f = df_f[df_f['Materia'].isin(sel_mat)]

# --- VISTAS ---
st.title("Agenda de Tutorías")
st.markdown(f"**IES Arca Real** | {date.today().year}")

tab_agenda, tab_cal = st.tabs(["📓 Agenda Diaria", "🗓️ Calendario Mensual"])

# --- VISTA AGENDA ---
with tab_agenda:
    hoy = date.today()
    df_view = df_f[df_f['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_view.empty: st.info("No hay tutorías pendientes.")
    
    # Iterar por días
    for fecha, grupo in df_view.groupby('Fecha'):
        dia_str = DIAS[fecha.weekday()]
        fecha_fmt = f"{dia_str}, {fecha.day} de {MESES[fecha.month]}"
        
        st.markdown(f'<div class="day-separator">{fecha_fmt}</div>', unsafe_allow_html=True)
        
        for _, row in grupo.iterrows():
            # Obtener color único para esta materia
            color_tema = get_color_materia(row['Materia'])
            
            st.markdown(f"""
<div class="timeline-row">
<div class="time-col">
    <div>{row['Inicio']}</div>
    <div style="font-size:0.8em; opacity:0.6;">{row['Fin']}</div>
</div>
<div class="line-col">
    <div class="line-vertical"></div>
    <div class="line-dot" style="background-color: {color_tema};"></div>
</div>
<div class="card-col" style="border-left-color: {color_tema};">
    <div class="materia-title" style="color:{color_tema}">{row['Materia']}</div>
    <div class="materia-detail">{row['Detalle']}</div>
    <div class="meta-info">
        👨‍🏫 {row['Profesor']} &nbsp; | &nbsp; 🎓 {row['Ciclo']}
    </div>
</div>
</div>
""", unsafe_allow_html=True)

# --- VISTA CALENDARIO ---
with tab_cal:
    c1, c2 = st.columns([1,3])
    with c1:
        mes_v = st.selectbox("Mes", list(MESES.keys()), index=hoy.month-1, format_func=lambda x: MESES[x])
        anio_v = st.number_input("Año", value=hoy.year)
    
    cal = calendar.monthcalendar(anio_v, mes_v)
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
                        c_ev = get_color_materia(e['Materia'])
                        html_evs += f'<div class="cal-event" style="background-color:{c_ev};" title="{e["Materia"]}">{e["Inicio"]} {e["Materia"][:9]}..</div>'
                    
                    st.markdown(f"""<div class="day-cell {clase}"><div class="day-header">{d}</div>{html_evs}</div>""", unsafe_allow_html=True)
