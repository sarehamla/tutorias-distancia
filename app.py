import streamlit as st
import pandas as pd
import re
import calendar
import hashlib
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Agenda IES Arca Real", layout="centered", page_icon="🌑")

# --- PALETA DE COLORES VIBRANTES (Para que resalten sobre fondo oscuro) ---
COLORES_MODULOS = [
    "#FF6B6B", "#4ECDC4", "#FFE66D", "#1A535C", "#F7FFF7", 
    "#FF9F1C", "#CBF3F0", "#2EC4B6", "#E71D36", "#A786DF"
]

def get_color_materia(texto):
    """Genera un color único para cada módulo."""
    if not isinstance(texto, str): return "#333"
    hash_obj = hashlib.md5(texto.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return COLORES_MODULOS[hash_int % len(COLORES_MODULOS)]

# --- ESTILOS CSS (DARK MODE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400;700&display=swap');

    /* --- AJUSTES GENERALES PARA MODO OSCURO --- */
    /* Forzamos colores claros en textos principales por si acaso */
    h1, h2, h3, h4, p, div { color: #e0e0e0; }
    
    .day-separator {
        font-family: 'Playfair Display', serif;
        font-size: 1.6em;
        font-weight: bold;
        color: #f0f0f0; /* Blanco casi puro */
        margin-top: 35px;
        margin-bottom: 20px;
        border-bottom: 1px solid #444; /* Línea gris oscura */
        padding-bottom: 5px;
        letter-spacing: 1px;
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
        color: #aaa; /* Gris claro */
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
        background-color: #555; /* Gris medio */
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
        border: 2px solid #262730; /* Mismo color que el fondo de la tarjeta oscura */
    }

    /* Tarjeta Dark Mode */
    .card-col {
        flex-grow: 1;
        background-color: #262730; /* Gris oscuro Streamlit */
        padding: 15px 20px;
        border-radius: 8px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 5px;
        border-left-width: 4px;
        border-left-style: solid;
        transition: transform 0.2s;
    }
    .card-col:hover {
        transform: translateX(3px);
        background-color: #30323d; /* Un pelín más claro al pasar ratón */
        border-color: #555;
    }

    .materia-title {
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        font-size: 1.1em;
        color: #ffffff !important; /* Blanco fuerza */
        margin-bottom: 2px;
    }
    .materia-detail {
        font-family: 'Lato', sans-serif;
        font-weight: 300;
        font-size: 0.95em;
        color: #bbb !important; /* Gris claro */
        font-style: italic;
    }
    .meta-info {
        margin-top: 10px;
        font-size: 0.75em;
        color: #888 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* --- CALENDARIO DARK --- */
    .day-cell {
        background-color: #262730;
        border: 1px solid #444;
        border-radius: 4px;
        height: 100px;
        padding: 4px;
        overflow-y: auto;
        font-family: 'Lato', sans-serif;
    }
    .day-header {
        font-family: 'Playfair Display', serif;
        text-align: right;
        font-weight: bold;
        color: #aaa;
    }
    .cal-event {
        font-size: 0.75em;
        padding: 2px 4px;
        margin-bottom: 2px;
        border-radius: 2px;
        color: #111; /* Texto oscuro sobre etiqueta de color */
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .current-day-cell {
        background-color: #1f2029 !important;
        border: 2px solid #FF6B6B !important;
    }
    
    /* Scrollbars oscuras */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #1e1e1e; }
    ::-webkit-scrollbar-thumb { background: #555; border-radius: 2px; }

</style>
""", unsafe_allow_html=True)

# --- CONSTANTES ---
MESES = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES ---
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
        fecha = date(int(a), m_num, int(d))
        horas = re.findall(r"(\d{1,2}:\d{2})", txt)
        return fecha, horas[0] if horas else "??", horas[1] if len(horas)>1 else ""
    except: return None, None, None

@st.cache_data
def cargar_datos():
    lista = []
    # AJUSTA AQUÍ TUS ARCHIVOS
    archivos = [("cfgm.csv", "CFGM Gestión"), ("cfgs.csv", "CFGS Finanzas")]
    for f_name, c_name in archivos:
        try:
            df = pd.read_csv(f_name)
            for _, row in df.iterrows():
                r_n, r_f, prof = str(row.get('Nombre','')), str(row.get('Fecha','')), str(row.get('Profesor/a',''))
                limpio = limpiar_materia(r_n)
                f, i, end = parsear_fecha(r_f)
                if f: lista.append({"Ciclo":c_name, "Módulo":limpio, "Detalle":extraer_detalle(r_n, limpio), "Profesor":prof, "Fecha":f, "Inicio":i, "Fin":end})
        except: continue
    return pd.DataFrame(lista)

# --- MAIN ---
df = cargar_datos()
if df.empty:
    st.error("No se encontraron los archivos CSV.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Filtros")
    ciclos = sorted(df['Ciclo'].unique())
    sel_ciclo = st.multiselect("Ciclo", ciclos, default=ciclos)
    df_f = df[df['Ciclo'].isin(sel_ciclo)]
    
    # CAMBIO: Ahora usamos 'Módulo formativo' en vez de 'Asignatura'
    materias = sorted(df_f['Módulo'].unique())
    sel_mat = st.multiselect("Módulo formativo", materias)
    if sel_mat: df_f = df_f[df_f['Módulo'].isin(sel_mat)]

# --- VISTAS ---
st.title("Agenda de Tutorías")
st.caption(f"IES Arca Real | Curso {date.today().year} - Modo Oscuro")

tab_agenda, tab_cal = st.tabs(["📓 Agenda Diaria", "🗓️ Calendario Mensual"])

# --- VISTA AGENDA ---
with tab_agenda:
    hoy = date.today()
    df_view = df_f[df_f['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_view.empty: st.info("No hay tutorías pendientes.")
    
    for fecha, grupo in df_view.groupby('Fecha'):
        dia_str = DIAS[fecha.weekday()]
        fecha_fmt = f"{dia_str}, {fecha.day} de {MESES[fecha.month]}"
        
        st.markdown(f'<div class="day-separator">{fecha_fmt}</div>', unsafe_allow_html=True)
        
        for _, row in grupo.iterrows():
            # Color del módulo
            color_tema = get_color_materia(row['Módulo'])
            
            st.markdown(f"""
<div class="timeline-row">
<div class="time-col">
    <div>{row['Inicio']}</div>
    <div style="font-size:0.8em; opacity:0.6;">{row['Fin']}</div>
</div>
<div class="line-col">
    <div class="line-vertical"></div>
    <div class="line-dot" style="border-color: #262730; background-color: {color_tema};"></div>
</div>
<div class="card-col" style="border-left-color: {color_tema};">
    <div class="materia-title">{row['Módulo']}</div>
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
                        c_ev = get_color_materia(e['Módulo'])
                        html_evs += f'<div class="cal-event" style="background-color:{c_ev};" title="{e["Módulo"]}">{e["Inicio"]} {e["Módulo"][:9]}..</div>'
                    
                    st.markdown(f"""<div class="day-cell {clase}"><div class="day-header">{d}</div>{html_evs}</div>""", unsafe_allow_html=True)
