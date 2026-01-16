import streamlit as st
import pandas as pd
import re
import calendar
import hashlib
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Actions Arca Real", layout="centered", page_icon="⚫")

# --- PALETA "ACTIONS" (Colores Neón/Vibrantes sobre Negro) ---
COLORES_ACTIONS = [
    "#FF296D", # Rosa Neón
    "#00FFF5", # Cian Eléctrico
    "#7FFF00", # Verde Lima
    "#FF9F1C", # Naranja Vivo
    "#D65DB1", # Púrpura
    "#FFEE00", # Amarillo
    "#00A8E8", # Azul Vivo
    "#FF4D4D", # Rojo Brillante
    "#B967FF", # Violeta
    "#32FF7E"  # Menta
]

def get_color_materia(texto):
    """Asigna un color neón consistente a cada módulo."""
    if not isinstance(texto, str): return "#888"
    hash_obj = hashlib.md5(texto.encode())
    hash_int = int(hash_obj.hexdigest(), 16)
    return COLORES_ACTIONS[hash_int % len(COLORES_ACTIONS)]

# --- ESTILOS CSS (ACTIONS DARK MODE) ---
st.markdown("""
<style>
    /* Fuente moderna sans-serif (estilo Inter/Roboto) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* --- FONDO NEGRO PROFUNDO (Global) --- */
    .stApp {
        background-color: #101010;
        color: #ffffff;
    }
    
    /* Forzar texto blanco en general */
    h1, h2, h3, p, div, span {
        font-family: 'Inter', sans-serif;
        color: #eeeeee;
    }

    /* Ocultar elementos decorativos de Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* --- CABECERAS --- */
    h1 {
        font-weight: 800;
        letter-spacing: -1px;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* --- SEPARADOR DE DÍA (Minimalista) --- */
    .day-header-actions {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #666; /* Gris oscuro para el día, sutil */
        margin-top: 40px;
        margin-bottom: 15px;
        border-bottom: 1px solid #222;
        padding-bottom: 5px;
        font-weight: 600;
    }

    /* --- FILAS DE EVENTOS (Estilo Lista Actions) --- */
    .action-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #1a1a1a; /* Línea separadora muy sutil */
        transition: background 0.2s;
    }
    .action-row:hover {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding-left: 10px; /* Pequeño movimiento al pasar mouse */
        margin-left: -10px;
    }

    /* Columna de Color (El punto o barra) */
    .color-indicator {
        width: 6px;
        height: 40px;
        border-radius: 4px;
        margin-right: 15px;
        flex-shrink: 0;
        box-shadow: 0 0 8px rgba(0,0,0,0.5); /* Resplandor neón */
    }

    /* Columna de Texto Principal */
    .content-col {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }

    .module-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 2px;
        /* El color se inyecta por línea */
    }

    .task-detail {
        font-size: 0.9rem;
        color: #888 !important;
        font-weight: 300;
    }

    /* Columna de Hora (Derecha, discreta) */
    .time-col {
        text-align: right;
        font-size: 0.85rem;
        color: #555 !important;
        font-weight: 600;
        min-width: 80px;
    }

    /* Etiquetas sutiles */
    .meta-tag {
        font-size: 0.7rem;
        background-color: #222;
        padding: 2px 6px;
        border-radius: 4px;
        color: #aaa !important;
        margin-top: 4px;
        display: inline-block;
        width: fit-content;
    }

    /* --- CALENDARIO DARK --- */
    .day-cell {
        background-color: #161616;
        border: 1px solid #222;
        border-radius: 6px;
        height: 100px;
        padding: 5px;
        overflow-y: auto;
    }
    .current-day-cell {
        border: 1px solid #fff !important;
        background-color: #000 !important;
    }
    .cal-event {
        font-size: 0.75rem;
        background-color: #222;
        margin-bottom: 2px;
        padding: 2px 5px;
        border-radius: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Scrollbars invisibles o muy oscuras */
    ::-webkit-scrollbar { width: 6px; background: #101010; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
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
    # ARCHIVOS
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
    st.error("No se encontraron los datos.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Preferencias")
    ciclos = sorted(df['Ciclo'].unique())
    sel_ciclo = st.multiselect("Ciclo", ciclos, default=ciclos)
    df_f = df[df['Ciclo'].isin(sel_ciclo)]
    
    materias = sorted(df_f['Módulo'].unique())
    sel_mat = st.multiselect("Módulo formativo", materias)
    if sel_mat: df_f = df_f[df_f['Módulo'].isin(sel_mat)]
    
    st.markdown("---")
    st.caption("Modo Actions Dark")

# --- VISTAS ---
st.title("Tutorías")

tab_agenda, tab_cal = st.tabs(["Listado", "Calendario"])

# --- VISTA 1: LISTADO ACTIONS (Minimalista) ---
with tab_agenda:
    hoy = date.today()
    df_view = df_f[df_f['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_view.empty: st.info("No hay tareas pendientes.")
    
    for fecha, grupo in df_view.groupby('Fecha'):
        dia_str = DIAS[fecha.weekday()]
        fecha_fmt = f"{dia_str}, {fecha.day} {MESES[fecha.month]}"
        
        # Cabecera de día minimalista (Gris oscuro, mayúsculas)
        st.markdown(f'<div class="day-header-actions">{fecha_fmt}</div>', unsafe_allow_html=True)
        
        for _, row in grupo.iterrows():
            c_neon = get_color_materia(row['Módulo'])
            
            # HTML ESTRUCTURADO TIPO ACTIONS
            st.markdown(f"""
<div class="action-row">
    <div class="color-indicator" style="background-color: {c_neon}; box-shadow: 0 0 10px {c_neon}40;"></div>
    
    <div class="content-col">
        <div class="module-title" style="color: {c_neon};">{row['Módulo']}</div>
        <div class="task-detail">{row['Detalle']}</div>
        <div class="meta-tag">👨‍🏫 {row['Profesor']}</div>
    </div>
    
    <div class="time-col">
        {row['Inicio']}
    </div>
</div>
""", unsafe_allow_html=True)

# --- VISTA 2: CALENDARIO ACTIONS ---
with tab_cal:
    c1, c2 = st.columns([1,3])
    with c1:
        mes_v = st.selectbox("Mes", list(MESES.keys()), index=hoy.month-1, format_func=lambda x: MESES[x])
        anio_v = st.number_input("Año", value=hoy.year)
    
    cal = calendar.monthcalendar(anio_v, mes_v)
    cols = st.columns(7)
    for i, d in enumerate(DIAS): cols[i].markdown(f"<div style='color:#666; font-size:0.8rem; text-align:center'>{d[:3]}</div>", unsafe_allow_html=True)
    
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
                        # Eventos en calendario: texto de color sobre fondo negro
                        html_evs += f'<div class="cal-event" style="color:{c_ev}; border-left: 2px solid {c_ev};">{e["Inicio"]}</div>'
                    
                    st.markdown(f"""<div class="day-cell {clase}"><div style="text-align:right; color:#444; font-weight:bold;">{d}</div>{html_evs}</div>""", unsafe_allow_html=True)
