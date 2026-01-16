import streamlit as st
import pandas as pd
import re
import calendar
import hashlib
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tutorías Arca Real", layout="centered", page_icon="🎓")

# --- PALETA NEÓN "ACTIONS" ---
COLORES_NEON = [
    "#FF296D", "#00FFF5", "#7FFF00", "#FF9F1C", "#D65DB1", 
    "#FFEE00", "#00A8E8", "#FF4D4D", "#B967FF", "#32FF7E"
]

def get_color_materia(texto):
    if not isinstance(texto, str): return "#888"
    hash_obj = hashlib.md5(texto.encode())
    return COLORES_NEON[int(hash_obj.hexdigest(), 16) % len(COLORES_NEON)]

# --- ESTILOS CSS (DARK MODE TOTAL + INPUTS CORREGIDOS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    /* --- 1. FONDO GLOBAL NEGRO --- */
    .stApp {
        background-color: #050505 !important;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }

    /* --- 2. BARRA SUPERIOR Y SIDEBAR OSCUROS --- */
    header[data-testid="stHeader"] {
        background-color: #050505 !important;
        border-bottom: 1px solid #1a1a1a;
    }
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #222;
    }
    
    /* Textos del sidebar */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] p {
        color: #e0e0e0 !important;
    }

    /* --- 3. INPUTS, FILTROS Y CAJA DEL AÑO --- */
    /* Selectores */
    div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        border-color: #333 !important;
        color: white !important;
    }
    div[data-baseweb="select"] span { color: #e0e0e0 !important; }
    div[data-baseweb="select"] svg { fill: #888 !important; }

    /* Inputs Numéricos */
    div[data-baseweb="input"] > div {
        background-color: #1a1a1a !important;
        border-color: #333 !important;
        color: white !important;
    }
    input { color: white !important; caret-color: white; }
    button[tabindex="-1"] { background-color: #222 !important; color: white !important; }

    /* Menús desplegables */
    div[role="listbox"] ul { background-color: #1a1a1a !important; }
    div[role="option"] { color: #e0e0e0 !important; }
    div[data-baseweb="tag"] { background-color: #333 !important; }

    /* --- 4. TARJETAS OSCURAS (AGENDA) --- */
    .action-card {
        background-color: #161616;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        transition: transform 0.2s, background-color 0.2s;
        position: relative;
        overflow: hidden;
    }
    .action-card:hover {
        background-color: #1f1f1f;
        transform: translateX(4px);
        border-color: #444;
    }

    /* --- 5. TIPOGRAFÍA Y ELEMENTOS --- */
    h1, h2, h3, p { color: #ffffff !important; }
    
    .day-header {
        color: #666;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 30px;
        margin-bottom: 10px;
        border-bottom: 1px solid #222;
        padding-bottom: 5px;
        font-weight: 700;
    }

    .module-title {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .module-detail {
        font-size: 0.9rem;
        color: #aaa;
        font-weight: 300;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .time-badge {
        background-color: #000;
        color: #fff;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #333;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .prof-badge {
        font-size: 0.75rem;
        color: #666;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .cycle-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        font-size: 0.65rem;
        color: #444;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: 1px solid #222;
        padding: 2px 5px;
        border-radius: 4px;
    }
    .color-bar {
        width: 4px;
        height: 50px;
        border-radius: 2px;
        margin-right: 15px;
        box-shadow: 0 0 8px rgba(0,0,0,0.3);
    }

    /* --- 6. CALENDARIO DARK --- */
    .day-cell {
        background-color: #111;
        border: 1px solid #222;
        border-radius: 6px;
        height: 100px;
        padding: 5px;
        overflow-y: auto;
    }
    .current-day-cell {
        background-color: #000 !important;
        border: 1px solid #fff !important;
    }
    .cal-event {
        font-size: 0.7rem;
        background-color: #222;
        color: #ddd;
        padding: 2px 4px;
        margin-bottom: 2px;
        border-radius: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border-left-width: 2px; 
        border-left-style: solid;
    }
    .day-num { text-align: right; color: #555; font-weight: bold; font-size: 0.9rem; }

    ::-webkit-scrollbar { width: 6px; background: #050505; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
MESES = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

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

# --- CARGA DATOS ---
df = cargar_datos()

# --- SIDEBAR OSCURO ---
with st.sidebar:
    # 1. LOGO
    st.image("https://cdn-icons-png.flaticon.com/512/3771/3771343.png", width=80) 
    
    st.markdown("### ⚙️ Preferencias")
    
    if not df.empty:
        ciclos = sorted(df['Ciclo'].unique())
        sel_ciclo = st.multiselect("Ciclo", ciclos, default=ciclos, placeholder="Elige el ciclo")
        df_f = df[df['Ciclo'].isin(sel_ciclo)]
        
        materias = sorted(df_f['Módulo'].unique())
        sel_mat = st.multiselect("Módulo formativo", materias, placeholder="Elige el módulo")
        if sel_mat: df_f = df_f[df_f['Módulo'].isin(sel_mat)]
        
        # --- AQUÍ ESTÁ EL NUEVO INTERRUPTOR DE PASADAS ---
        st.markdown("---")
        ver_pasadas = st.toggle("Mostrar tutorías pasadas", value=False)
        
    else:
        st.error("No hay datos cargados.")
        df_f = pd.DataFrame()
        ver_pasadas = False

    st.caption("Modo Oscuro | IES Arca Real")

# --- INTERFAZ PRINCIPAL ---
st.title("Tutorías colectivas CCFF modalidad virtual")
st.markdown("#### IES Arca Real")

if df_f.empty:
    st.info("No hay datos para mostrar.")
    st.stop()

tab_agenda, tab_cal = st.tabs(["LISTA", "CALENDARIO"])

# --- VISTA 1: AGENDA OSCURA ---
with tab_agenda:
    hoy = date.today()
    
    # LÓGICA DE FILTRADO DE FECHAS
    if ver_pasadas:
        # Si el usuario quiere ver todo, mostramos todo ordenado
        df_view = df_f.sort_values(['Fecha', 'Inicio'])
    else:
        # Si no, solo desde hoy en adelante
        df_view = df_f[df_f['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_view.empty: st.markdown("✅ *No hay tutorías pendientes.*")
    
    for fecha, grupo in df_view.groupby('Fecha'):
        dia_str = DIAS[fecha.weekday()]
        fecha_fmt = f"{dia_str}, {fecha.day} {MESES[fecha.month]}"
        
        st.markdown(f'<div class="day-header">{fecha_fmt}</div>', unsafe_allow_html=True)
        
        for _, row in grupo.iterrows():
            c_neon = get_color_materia(row['Módulo'])
            
            # Cálculo de opacidad: si es fecha pasada, se ve semitransparente (0.5), si es futura se ve normal (1)
            opacidad = "0.5" if row['Fecha'] < hoy else "1"
            
            st.markdown(f"""
            <div class="action-card" style="opacity: {opacidad};">
                <div class="color-bar" style="background-color: {c_neon}; box-shadow: 0 0 8px {c_neon}60;"></div>
                <div style="flex-grow:1;">
                    <div class="cycle-badge">📂 {row['Ciclo']}</div>
                    <div class="module-title" style="color: {c_neon};">{row['Módulo']}</div>
                    <div class="module-detail">📌 {row['Detalle']}</div>
                    <div class="prof-badge">👨‍🏫 {row['Profesor']}</div>
                </div>
                <div style="text-align:right;">
                    <div class="time-badge">🕒 {row['Inicio']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- VISTA 2: CALENDARIO OSCURO ---
with tab_cal:
    c1, c2 = st.columns([1,3])
    with c1:
        mes_v = st.selectbox("Mes", list(MESES.keys()), index=date.today().month-1, format_func=lambda x: MESES[x])
        anio_v = st.number_input("Año", value=date.today().year)
    
    cal = calendar.monthcalendar(anio_v, mes_v)
    
    cols = st.columns(7)
    for i, d in enumerate(DIAS): 
        cols[i].markdown(f"<div style='text-align:center; color:#666; font-size:0.8rem'>{d[:3]}</div>", unsafe_allow_html=True)
    
    for sem in cal:
        cols = st.columns(7)
        for i, d in enumerate(sem):
            with cols[i]:
                if d != 0:
                    f_celda = date(anio_v, mes_v, d)
                    clase = "current-day-cell" if f_celda == date.today() else ""
                    evs = df_f[df_f['Fecha'] == f_celda]
                    
                    html_evs = ""
                    for _, e in evs.iterrows():
                        c_ev = get_color_materia(e['Módulo'])
                        html_evs += f'<div class="cal-event" style="border-left-color:{c_ev};">{e["Inicio"]} {e["Módulo"][:8]}..</div>'
                    
                    st.markdown(f"""
                    <div class="day-cell {clase}">
                        <div class="day-num">{d}</div>
                        {html_evs}
                    </div>
                    """, unsafe_allow_html=True)
