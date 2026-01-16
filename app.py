import streamlit as st
import pandas as pd
import re
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Tutorías IES Arca Real", layout="wide", page_icon="📅")

st.title("📚 Visor de Tutorías - IES Arca Real")
st.markdown("Gestión Administrativa (CFGM) y Administración y Finanzas (CFGS)")

# --- FUNCIONES DE LIMPIEZA ---

def parsear_fecha_compleja(fecha_str):
    """
    Convierte cadenas como '17 de octubre de 2025 17:20 (CEST) → 19:00'
    en objetos de fecha y horas separadas.
    """
    if not isinstance(fecha_str, str):
        return None, None, None

    # Diccionario para meses en español
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }

    # Intentar limpiar la cadena básica
    try:
        # Extraer fecha base (ej: 17 de octubre de 2025)
        # Regex busca: digitos + " de " + letras + " de " + digitos
        match_fecha = re.search(r"(\d{1,2}) de ([a-zA-Z]+) de (\d{4})", fecha_str)
        
        if not match_fecha:
            return None, None, None # No es una fecha válida

        dia, mes_txt, anio = match_fecha.groups()
        mes_num = meses.get(mes_txt.lower())
        
        fecha_obj = datetime.strptime(f"{anio}-{mes_num}-{dia}", "%Y-%m-%d").date()

        # Extraer Horas
        # Busca patrones de hora HH:MM
        horas = re.findall(r"(\d{1,2}:\d{2})", fecha_str)
        hora_inicio = horas[0] if len(horas) > 0 else "Consultar"
        hora_fin = horas[1] if len(horas) > 1 else ""

        return fecha_obj, hora_inicio, hora_fin

    except Exception as e:
        return None, None, None

@st.cache_data
def cargar_datos():
    datos_totales = []

    # Archivos y etiquetas (Asegúrate de que los nombres coincidan con tus archivos)
    # Si no renombraste los archivos, cambia 'cfgm.csv' por el nombre largo original
    archivos = [
        ("cfgm.csv", "CFGM Gestión Administrativa"),
        ("cfgs.csv", "CFGS Administración y Finanzas")
    ]

    for archivo, nombre_ciclo in archivos:
        try:
            df = pd.read_csv(archivo)
            # Normalizar columnas (quitar espacios extra)
            df.columns = df.columns.str.strip()
            
            # Procesar cada fila
            for _, row in df.iterrows():
                nombre_completo = row.get('Nombre', '')
                fecha_raw = row.get('Fecha', '')
                profe = row.get('Profesor/a', '')

                # Separar Asignatura de Unidad (UT) si existe el guión "-"
                if " - " in str(nombre_completo):
                    partes = str(nombre_completo).split(" - ", 1)
                    asignatura = partes[0]
                    detalle = partes[1]
                else:
                    asignatura = nombre_completo
                    detalle = ""

                fecha_obj, h_inicio, h_fin = parsear_fecha_compleja(fecha_raw)

                if fecha_obj: # Solo añadir si la fecha es válida
                    datos_totales.append({
                        "Ciclo": nombre_ciclo,
                        "Asignatura": asignatura,
                        "Detalle": detalle,
                        "Profesor": profe,
                        "Fecha": fecha_obj,
                        "Inicio": h_inicio,
                        "Fin": h_fin,
                        "Raw": fecha_raw
                    })
        except FileNotFoundError:
            st.warning(f"No se encontró el archivo: {archivo}")
            continue

    return pd.DataFrame(datos_totales)

# --- LÓGICA PRINCIPAL ---

df = cargar_datos()

if df.empty:
    st.error("No hay datos cargados. Por favor verifica que los archivos .csv están en la carpeta.")
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros")

# 1. Filtro Ciclo
ciclos_disponibles = df['Ciclo'].unique()
ciclo_sel = st.sidebar.multiselect("Ciclo Formativo", ciclos_disponibles, default=ciclos_disponibles)

# Filtrar DF parcial
df_filtered = df[df['Ciclo'].isin(ciclo_sel)]

# 2. Filtro Asignatura (Dinámico según ciclo)
asignaturas_disponibles = sorted(df_filtered['Asignatura'].astype(str).unique())
asig_sel = st.sidebar.multiselect("Asignatura / Módulo", asignaturas_disponibles)

# 3. Checkbox pasadas
mostrar_pasadas = st.sidebar.checkbox("Mostrar tutorías ya pasadas", value=False)

# APLICAR TODOS LOS FILTROS
if asig_sel:
    df_filtered = df_filtered[df_filtered['Asignatura'].isin(asig_sel)]

if not mostrar_pasadas:
    df_filtered = df_filtered[df_filtered['Fecha'] >= datetime.now().date()]

df_filtered = df_filtered.sort_values(by=['Fecha', 'Inicio'])

# --- VISTA PRINCIPAL ---

tab1, tab2 = st.tabs(["📆 Vista Agenda", "📋 Tabla Detallada"])

with tab1:
    if df_filtered.empty:
        st.info("No hay tutorías que coincidan con los filtros.")
    
    # Agrupar por Mes para visualización limpia
    df_filtered['Mes_Str'] = pd.to_datetime(df_filtered['Fecha']).dt.strftime('%B %Y').str.capitalize()
    
    meses_unicos = df_filtered['Mes_Str'].unique()
    
    for mes in meses_unicos:
        st.subheader(f"🗓️ {mes}")
        tutorias_mes = df_filtered[df_filtered['Mes_Str'] == mes]
        
        # Crear columnas para tarjetas (diseño tipo grid)
        cols = st.columns(3) # 3 tarjetas por fila
        for i, (index, row) in enumerate(tutorias_mes.iterrows()):
            col = cols[i % 3]
            
            # Estilo condicional si es HOY
            es_hoy = row['Fecha'] == datetime.now().date()
            borde = "2px solid #ff4b4b" if es_hoy else "1px solid #ddd"
            bg = "#ffecec" if es_hoy else "#ffffff"
            
            with col:
                st.markdown(f"""
                <div style="border: {borde}; background-color: {bg}; padding: 15px; border-radius: 8px; margin-bottom:10px; height: 100%;">
                    <small style="color: #666;">{row['Ciclo']}</small>
                    <h5 style="margin: 5px 0; color: #000;">{row['Asignatura']}</h5>
                    <p style="font-size: 0.9em; margin-bottom: 5px;"><b>📝 {row['Detalle']}</b></p>
                    <hr style="margin: 5px 0;">
                    <p>📅 <b>{row['Fecha'].strftime('%d-%m-%Y')}</b><br>
                    ⏰ {row['Inicio']} {f'➝ {row["Fin"]}' if row["Fin"] else ''}</p>
                    <p style="font-size: 0.85em; color: #555;">👨‍🏫 {row['Profesor']}</p>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.dataframe(
        df_filtered[['Fecha', 'Inicio', 'Fin', 'Ciclo', 'Asignatura', 'Detalle', 'Profesor']],
        use_container_width=True,
        hide_index=True
    )