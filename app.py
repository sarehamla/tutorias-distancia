import streamlit as st
import pandas as pd
import re
import calendar
from datetime import datetime, date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tutorías IES Arca Real", layout="wide", page_icon="📅")

# --- CONSTANTES DE IDIOMA (Para asegurar español siempre) ---
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# --- FUNCIONES DE LIMPIEZA ---

def limpiar_texto_fecha(fecha_str):
    """
    Convierte cadenas complejas de Notion a objetos date y horas limpias.
    Soporta formato: "17 de octubre de 2025 17:20 (CEST) → 19:00"
    """
    if not isinstance(fecha_str, str):
        return None, None, None

    # Mapeo manual de meses para el parseo
    meses_map = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    try:
        # Extraer fecha base (ej: 17 de octubre de 2025)
        match_fecha = re.search(r"(\d{1,2}) de ([a-zA-Z]+) de (\d{4})", fecha_str.lower())
        
        if not match_fecha:
            return None, None, None

        dia, mes_txt, anio = match_fecha.groups()
        mes_num = meses_map.get(mes_txt)
        
        if not mes_num: return None, None, None
        
        fecha_obj = datetime.strptime(f"{anio}-{mes_num}-{dia}", "%Y-%m-%d").date()

        # Extraer Horas
        horas = re.findall(r"(\d{1,2}:\d{2})", fecha_str)
        hora_inicio = horas[0] if len(horas) > 0 else "Consultar"
        hora_fin = horas[1] if len(horas) > 1 else ""

        return fecha_obj, hora_inicio, hora_fin

    except Exception:
        return None, None, None

@st.cache_data
def cargar_datos():
    datos_totales = []
    # Asegúrate de que estos nombres coinciden con tus archivos en GitHub/Carpeta
    archivos = [
        ("cfgm.csv", "Gestión Administrativa (CFGM)"),
        ("cfgs.csv", "Administración y Finanzas (CFGS)")
    ]

    for archivo, nombre_ciclo in archivos:
        try:
            df = pd.read_csv(archivo)
            df.columns = df.columns.str.strip() # Limpiar espacios en nombres de columnas
            
            for _, row in df.iterrows():
                nombre_crudo = str(row.get('Nombre', ''))
                fecha_raw = str(row.get('Fecha', ''))
                profe = row.get('Profesor/a', 'Sin asignar')

                # --- LIMPIEZA DE MATERIA (Aquí quitamos lo de UT1, UT2...) ---
                # Separamos por " - " o por " UT" si el guion no existe pero la UT sí
                if " - " in nombre_crudo:
                    partes = nombre_crudo.split(" - ", 1)
                    asignatura_limpia = partes[0].strip()
                    detalle = partes[1].strip() # Aquí se queda "UT1"
                else:
                    asignatura_limpia = nombre_crudo.strip()
                    detalle = ""

                # Procesar fecha
                fecha_obj, h_inicio, h_fin = limpiar_texto_fecha(fecha_raw)

                if fecha_obj:
                    datos_totales.append({
                        "Ciclo": nombre_ciclo,
                        "Asignatura": asignatura_limpia, # Usamos la limpia para el filtro
                        "Detalle": detalle,              # Guardamos la UT para la tarjeta
                        "Profesor": profe,
                        "Fecha": fecha_obj,
                        "Año": fecha_obj.year,
                        "Mes": fecha_obj.month,
                        "Inicio": h_inicio,
                        "Fin": h_fin
                    })
        except FileNotFoundError:
            continue

    return pd.DataFrame(datos_totales)

# --- CARGA INICIAL ---
df = cargar_datos()

if df.empty:
    st.error("⚠️ No se encontraron datos. Verifica que 'cfgm.csv' y 'cfgs.csv' están subidos.")
    st.stop()

# --- SIDEBAR: FILTROS ---
st.sidebar.title("🔍 Filtros")

# 1. Filtro Ciclo
ciclos = df['Ciclo'].unique()
sel_ciclo = st.sidebar.multiselect("Ciclo Formativo", ciclos, default=ciclos)
df_f = df[df['Ciclo'].isin(sel_ciclo)]

# 2. Filtro Asignatura (AHORA LIMPIO)
# Al usar 'Asignatura' limpia, sorted y unique, no saldrán repetidas
asignaturas = sorted(df_f['Asignatura'].unique())
sel_asig = st.sidebar.multiselect("Materia / Módulo", asignaturas)

if sel_asig:
    df_f = df_f[df_f['Asignatura'].isin(sel_asig)]

# 3. Opción Pasadas
mostrar_pasadas = st.sidebar.checkbox("Ver tutorías pasadas", value=False)
if not mostrar_pasadas:
    df_f = df_f[df_f['Fecha'] >= date.today()]

df_f = df_f.sort_values(['Fecha', 'Inicio'])

# --- INTERFAZ PRINCIPAL ---
st.title("📚 Calendario de Tutorías")
st.markdown("IES Arca Real - Formación Profesional Virtual")

tab1, tab2, tab3 = st.tabs(["📆 Vista Mensual (Calendario)", "📝 Vista Agenda (Lista)", "📋 Tabla Datos"])

# --- PESTAÑA 1: CALENDARIO VISUAL ---
with tab1:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        # Selectores de mes y año
        hoy = date.today()
        sel_anio = st.number_input("Año", min_value=2024, max_value=2030, value=hoy.year)
        sel_mes_num = st.selectbox(
            "Mes", 
            list(MESES_ES.keys()), 
            format_func=lambda x: MESES_ES[x],
            index=hoy.month - 1
        )
    
    with col_b:
        st.write("") # Espacio
        st.subheader(f"📅 {MESES_ES[sel_mes_num]} {sel_anio}")

    # Filtrar datos solo para el mes seleccionado (para pintarlos en el calendario)
    df_cal = df_f[(df_f['Año'] == sel_anio) & (df_f['Mes'] == sel_mes_num)]
    
    # Dibujar Cabecera Semanal
    cols_cabecera = st.columns(7)
    for i, dia in enumerate(DIAS_ES):
        cols_cabecera[i].markdown(f"**{dia}**")
    
    # Obtener matriz del mes
    cal_matriz = calendar.monthcalendar(sel_anio, sel_mes_num)
    
    for semana in cal_matriz:
        cols_dias = st.columns(7, gap="small")
        for i, dia_num in enumerate(semana):
            if dia_num == 0:
                cols_dias[i].write("") # Día vacío de otro mes
            else:
                # Buscar eventos de este día concreto
                fecha_actual = date(sel_anio, sel_mes_num, dia_num)
                eventos_dia = df_cal[df_cal['Fecha'] == fecha_actual]
                
                # Estilo del día
                es_hoy = fecha_actual == date.today()
                bg_style = "background-color: #ffecec; border: 2px solid #ff4b4b;" if es_hoy else "background-color: #f0f2f6;"
                
                with cols_dias[i]:
                    with st.container():
                        # Caja del día
                        st.markdown(f"""
                        <div style="{bg_style} padding: 5px; border-radius: 5px; min-height: 80px; font-size: 0.8rem;">
                            <strong style="font-size:1rem;">{dia_num}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Pintar puntitos o textos si hay eventos
                        for _, evento in eventos_dia.iterrows():
                            # Tooltip nativo de Streamlit con help
                            st.markdown(f"**{evento['Inicio']}**")
                            st.caption(f"{evento['Asignatura'][:15]}...", help=f"{evento['Asignatura']} - {evento['Detalle']}\nProf: {evento['Profesor']}")
                            st.divider()

# --- PESTAÑA 2: AGENDA (LISTA) ---
with tab2:
    if df_f.empty:
        st.info("No hay tutorías pendientes con estos filtros.")
    
    # Agrupar por mes
    meses_presentes = df_f['Fecha'].apply(lambda x: f"{MESES_ES[x.month]} {x.year}").unique()
    
    for mes_str in meses_presentes:
        st.subheader(mes_str)
        # Filtrar solo este mes visual
        df_mes_visual = df_f[df_f['Fecha'].apply(lambda x: f"{MESES_ES[x.month]} {x.year}") == mes_str]
        
        for _, row in df_mes_visual.iterrows():
            es_hoy = row['Fecha'] == date.today()
            icono = "🔴 HOY" if es_hoy else "🗓️"
            color_borde = "red" if es_hoy else "lightgray"
            
            with st.expander(f"{icono} {row['Fecha'].day} - {row['Asignatura']} ({row['Inicio']})", expanded=es_hoy):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Módulo:** {row['Asignatura']}")
                    st.markdown(f"**Unidad/Detalle:** {row['Detalle']}")
                    st.markdown(f"**Profesor/a:** {row['Profesor']}")
                with c2:
                    st.markdown(f"⏰ **{row['Inicio']}**")
                    if row['Fin']:
                        st.markdown(f"➝ {row['Fin']}")
                    st.caption(row['Ciclo'])

# --- PESTAÑA 3: TABLA ---
with tab3:
    st.dataframe(
        df_f[['Fecha', 'Inicio', 'Asignatura', 'Detalle', 'Profesor', 'Ciclo']], 
        use_container_width=True, 
        hide_index=True
    )
