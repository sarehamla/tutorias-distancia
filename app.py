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
                    # Celda vacía (sin sangría en el HTML para evitar error)
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
                        # Ocultamos el texto "General" si no aporta nada
                        texto_detalle = ev['Detalle'] if ev['Detalle'] != "General" else ""
                        
                        html_eventos += f"""
                        <div class="event-card">
                            <div class="event-time">{ev['Inicio']}</div>
                            <div>{ev['Materia']}</div>
                            <div style="font-size:0.7em; color:#666;">{texto_detalle}</div>
                        </div>
                        """
                    
                    # --- IMPORTANTE: EL TEXTO HTML DEBE ESTAR PEGADO A LA IZQUIERDA ---
                    # Al usar st.markdown, si el HTML tiene espacios delante, se cree que es código.
                    # Aquí lo arreglamos forzando el inicio de línea.
                    st.markdown(f"""
<div class="day-cell {clase_extra}">
<div class="day-header">{dia}</div>
{html_eventos}
</div>
""", unsafe_allow_html=True)
