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
        h_ini = horas[0]
