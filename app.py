import streamlit as st
import pandas as pd
import re
import calendar
from datetime import datetime, date

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Tutorías IES Arca Real", layout="wide", page_icon="📅")

# --- ESTILOS CSS AVANZADOS (AGENDA ELEGANTE + CALENDARIO) ---
st.markdown("""
<style>
    /* --- CALENDARIO --- */
    .day-cell {
        border: 1px solid #eee;
        height: 120px;
        background-color: #ffffff;
        padding: 4px;
        border-radius: 8px;
        overflow-y: auto;
        transition: all 0.2s ease;
    }
    .day-cell:hover {
        border-color: #ccc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .day-header {
        text-align: right;
        font-size: 0.9em;
        font-weight: bold;
        color: #888;
        margin-bottom: 4px;
        padding-right: 5px;
    }
    .cal-event {
        background-color: #e3f2fd;
        border-left: 3px solid #2196f3;
        color: #0d47a1;
        padding: 3px 5px;
        margin-bottom: 3px;
        border-radius: 4px;
        font-size: 0.75em;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        cursor: help;
    }
    .current-day-cell {
        border: 2px solid #ff4b4b !important;
        background-color: #fffbfc !important;
    }

    /* --- AGENDA (TIMELINE) --- */
    .agenda-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        transition: transform 0.2s;
    }
    .agenda-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .agenda-date {
        color: #ff4b4b;
        font-weight: 800;
        text-transform: uppercase;
        font-size: 0.85em;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .agenda-title {
        font-size: 1.3em;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }
    .agenda-meta {
        display: flex;
        gap: 15px;
        margin-top: 10px;
        color: #6b7280;
        font-size: 0.95em;
    }
    .tag {
        background-color: #f3f4f6;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        font-weight: 600;
        color: #374151;
    }
</style>
""", unsafe_allow_html=True)

# --- MAPEOS DE IDIOMA ---
MESES = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_materia(txt):
    if not isinstance(txt, str): return "Desconocida"
    # Eliminar patrones de UT y Grupo
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
        # Regex para "17 de octubre de 2025"
        match = re.search(r"(\d{1,2})\s+de\s+([a-zA-Z]+)\s+de\s+(\d{4})", txt.lower())
        if not match: return None, None, None
        
        d, m_txt, a = match.groups()
        # Mapa inverso de meses
        mes_map = {v.lower(): k for k, v in MESES.items()}
        m_num = mes_map.get(m_txt)
        
        if not m_num: return None, None, None
        
        fecha_obj = date(int(a), m_num, int(d))
        
        # Extraer horas
        horas = re.findall(r"(\d{1,2}:\d{2})", txt)
        ini = horas[0] if horas else "??:??"
        fin = horas[1] if len(horas) > 1 else ""
        
        return fecha_obj, ini, fin
    except Exception as e:
        return None, None, None

@st.cache_data
def cargar_datos():
    lista = []
    # AJUSTA LOS NOMBRES DE TUS ARCHIVOS AQUÍ
    archivos = [("cfgm.csv", "CFGM Gestión Admin."), ("cfgs.csv", "CFGS Admin. y Finanzas")]
    
    for f_name, ciclo_name in archivos:
        try:
            df = pd.read_csv(f_name)
            for _, row in df.iterrows():
                raw_nom = str(row.get('Nombre', ''))
                raw_fec = str(row.get('Fecha', ''))
                profe = str(row.get('Profesor/a', ''))
                
                nom_clean = limpiar_materia(raw_nom)
                detalle = extraer_detalle(raw_nom, nom_clean)
                fecha, ini, fin = parsear_fecha(raw_fec)
                
                if fecha:
                    lista.append({
                        "Ciclo": ciclo_name,
                        "Materia": nom_clean,
                        "Detalle": detalle,
                        "Profesor": profe,
                        "Fecha": fecha,
                        "Inicio": ini,
                        "Fin": fin
                    })
        except FileNotFoundError:
            continue
            
    return pd.DataFrame(lista)

# --- LÓGICA PRINCIPAL ---
df = cargar_datos()

if df.empty:
    st.error("⚠️ No se cargaron datos. Verifica que los archivos .csv están en la carpeta.")
    st.stop()

# --- SIDEBAR (FILTROS) ---
st.sidebar.title("🔍 Filtros")
ciclos_dispo = sorted(df['Ciclo'].unique())
sel_ciclo = st.sidebar.multiselect("Ciclo", ciclos_dispo, default=ciclos_dispo)

# Filtrado preliminar
df_filtered = df[df['Ciclo'].isin(sel_ciclo)]

materias_dispo = sorted(df_filtered['Materia'].unique())
sel_materia = st.sidebar.multiselect("Asignatura", materias_dispo)

if sel_materia:
    df_filtered = df_filtered[df_filtered['Materia'].isin(sel_materia)]

# --- INTERFAZ ---
st.title("📚 Agenda de Tutorías")

tab_cal, tab_agenda = st.tabs(["📆 Calendario Mensual", "🎫 Agenda Próxima"])

# ==========================================
# PESTAÑA 1: CALENDARIO (Visualmente corregido)
# ==========================================
with tab_cal:
    c1, c2 = st.columns([1, 4])
    with c1:
        hoy = date.today()
        # Navegación
        mes_view = st.selectbox("Mes", list(MESES.keys()), index=hoy.month-1, format_func=lambda x: MESES[x])
        anio_view = st.number_input("Año", value=hoy.year, step=1)
    with c2:
        st.markdown(f"### {MESES[mes_view]} {anio_view}")

    # Cabecera
    cols = st.columns(7)
    for i, d in enumerate(DIAS):
        cols[i].markdown(f"<div style='text-align:center; font-weight:bold; color:#555;'>{d[:3]}</div>", unsafe_allow_html=True)
    
    # Matriz del mes
    cal_matrix = calendar.monthcalendar(anio_view, mes_view)
    
    # IMPORTANTE: Aquí NO usamos filtros de "pasadas", usamos todo el DF filtrado por materia
    df_cal = df_filtered.copy()
    
    for semana in cal_matrix:
        cols = st.columns(7)
        for i, dia_num in enumerate(semana):
            with cols[i]:
                if dia_num == 0:
                    st.markdown('<div class="day-cell" style="background:#f9f9f9; border:none;"></div>', unsafe_allow_html=True)
                else:
                    fecha_celda = date(anio_view, mes_view, dia_num)
                    es_hoy = fecha_celda == hoy
                    clase_hoy = "current-day-cell" if es_hoy else ""
                    
                    # Buscar eventos de este día
                    eventos_dia = df_cal[df_cal['Fecha'] == fecha_celda]
                    
                    html_evs = ""
                    for _, ev in eventos_dia.iterrows():
                        tooltip = f"{ev['Materia']} ({ev['Detalle']})&#10;Prof: {ev['Profesor']}"
                        html_evs += f"""
                        <div class="cal-event" title="{tooltip}">
                            <b>{ev['Inicio']}</b> {ev['Materia']}
                        </div>
                        """
                    
                    # Renderizado HTML limpio (todo en una línea o pegado a la izquierda)
                    st.markdown(f"""<div class="day-cell {clase_hoy}"><div class="day-header">{dia_num}</div>{html_evs}</div>""", unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: AGENDA (Diseño Elegante)
# ==========================================
with tab_agenda:
    # Filtro solo futuras para la agenda
    df_agenda = df_filtered[df_filtered['Fecha'] >= hoy].sort_values(['Fecha', 'Inicio'])
    
    if df_agenda.empty:
        st.info("✅ No tienes tutorías próximas con los filtros seleccionados.")
    else:
        # Agrupar por mes para separar secciones
        meses_agenda = df_agenda['Fecha'].apply(lambda x: (x.year, x.month)).unique()
        
        for (anio, mes) in meses_agenda:
            st.markdown(f"#### 🗓️ {MESES[mes]} {anio}")
            
            # Filtrar eventos de ese mes
            df_mes = df_agenda[(df_agenda['Fecha'].apply(lambda x: x.month) == mes) & (df_agenda['Fecha'].apply(lambda x: x.year) == anio)]
            
            for _, row in df_mes.iterrows():
                # Formato de fecha legible
                dia_semana = DIAS[row['Fecha'].weekday()]
                fecha_str = f"{dia_semana}, {row['Fecha'].day} de {MESES[row['Fecha'].month]}"
                
                # Diseño de Tarjeta HTML
                st.markdown(f"""
                <div class="agenda-card">
                    <div class="agenda-date">{fecha_str}</div>
                    <div class="agenda-title">{row['Materia']}</div>
                    <div style="color: #4b5563; margin-top: 4px;">{row['Detalle']}</div>
                    
                    <div class="agenda-meta">
                        <span class="tag">⏰ {row['Inicio']} {f"- {row['Fin']}" if row['Fin'] else ""}</span>
                        <span class="tag">👨‍🏫 {row['Profesor']}</span>
                        <span class="tag">🎓 {row['Ciclo']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
