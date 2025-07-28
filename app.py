import streamlit as st
import pandas as pd
from collections import defaultdict

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Horarios Unisucre",
    page_icon="😺",
    layout="wide"
)

# --- Funciones Auxiliares ---

@st.cache_data
def cargar_datos_csv(ruta_archivo='horarios.csv'):
    """Carga los datos desde un archivo CSV."""
    try:
        df = pd.read_csv(ruta_archivo, dtype={'inicio': str, 'fin': str})
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo '{ruta_archivo}'.")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error al leer el archivo CSV: {e}")
        return None

def transformar_df_a_cursos(df_filtrado):
    """Convierte un DataFrame plano a la estructura de cursos anidada."""
    cursos = []
    for _, group in df_filtrado.groupby(['nombre_curso', 'profesor']):
        curso_info = group.iloc[0]
        horarios = []
        for _, clase in group.iterrows():
            horarios.append({
                'dia': clase['dia'],
                'inicio': clase['inicio'],
                'fin': clase['fin'],
                'salon': clase['salon']
            })
        
        cursos.append({
            'nombre': curso_info['nombre_curso'],
            'profesor': curso_info['profesor'],
            'horario': horarios
        })
    return cursos

def mostrar_horario_interactivo(cursos):
    """Crea una vista semanal donde cada clase es un expander interactivo."""
    clases_por_dia = defaultdict(list)
    for curso in cursos:
        for clase in curso['horario']:
            clases_por_dia[clase['dia']].append({
                'nombre': curso['nombre'],
                'profesor': curso['profesor'],
                'inicio': clase['inicio'],
                'fin': clase['fin'],
                'salon': clase['salon']
            })

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    columnas = st.columns(len(dias_semana))

    for i, dia in enumerate(dias_semana):
        with columnas[i]:
            st.markdown(f"### {dia}")
            clases_del_dia = sorted(clases_por_dia.get(dia, []), key=lambda x: x['inicio'])
            if clases_del_dia:
                for clase in clases_del_dia:
                    label = f"**{clase['nombre']}**\n\n_{clase['inicio']} - {clase['fin']}_"
                    with st.expander(label):
                        st.markdown(f"**👨‍🏫 Profesor:** {clase['profesor']}")
                        st.markdown(f"**📍 Salón:** {clase['salon']}")
            else:
                st.info("Sin clases")

# --- Cuerpo Principal de la App ---
st.title("Registro de Horarios")
st.markdown("Consulta horarios de forma sencilla seleccionando el período y semestre.")

st.markdown("Agrega materias con el siguiente link: [Registrar](https://docs.google.com/spreadsheets/d/1vgU3AXSIdbsLtaMr13AWC4WaxDN6Hp6pZF0qY2oWARo/edit?gid=0#gid=0)")


df_horarios = cargar_datos_csv()

if df_horarios is not None and not df_horarios.empty:
    # --- Barra Lateral (Sidebar) ---
    st.sidebar.header("Selección de Horario")

    periodos_unicos = sorted(df_horarios['periodo_id'].unique(), reverse=True)
    periodo_defecto = periodos_unicos[0] if periodos_unicos else None
    
    mapa_periodos = df_horarios[['periodo_id', 'nombre_periodo']].drop_duplicates()
    lista_periodos_id = mapa_periodos['periodo_id'].tolist()
    indice_periodo = lista_periodos_id.index(periodo_defecto) if periodo_defecto in lista_periodos_id else 0
    
    periodo_seleccionado_id = st.sidebar.selectbox(
        "Elige un período:",
        options=lista_periodos_id,
        index=indice_periodo,
        format_func=lambda id: mapa_periodos.loc[mapa_periodos['periodo_id'] == id, 'nombre_periodo'].iloc[0]
    )

    df_periodo = df_horarios[df_horarios['periodo_id'] == periodo_seleccionado_id]
    lista_sub_semestres = sorted(df_periodo['sub_semestre'].unique())
    
    sub_semestre_seleccionado = st.sidebar.selectbox(
        "Elige un semestre:",
        options=lista_sub_semestres,
    )

    # DataFrame con los datos solo del período y semestre seleccionados
    df_semestre_actual = df_periodo[df_periodo['sub_semestre'] == sub_semestre_seleccionado]

    # AÑADIDO: Lógica para el filtro de materias
    st.sidebar.header("Filtros")
    if not df_semestre_actual.empty:
        # Obtenemos la lista de materias únicas para el semestre seleccionado
        lista_materias = sorted(df_semestre_actual['nombre_curso'].unique())
        
        # Creamos el widget multiselect
        materias_filtradas = st.sidebar.multiselect(
            "Filtrar por Materia:",
            options=lista_materias,
            placeholder="Selecciona una o más materias"
        )
        
        # Si el usuario ha seleccionado materias, filtramos el DataFrame
        if materias_filtradas:
            df_final_filtrado = df_semestre_actual[df_semestre_actual['nombre_curso'].isin(materias_filtradas)]
        else:
            # Si no hay selección, usamos el DataFrame completo del semestre
            df_final_filtrado = df_semestre_actual
    else:
        # Si el semestre no tiene cursos, creamos un DataFrame vacío para evitar errores
        df_final_filtrado = pd.DataFrame(columns=df_horarios.columns)

    # Transformamos el DataFrame (ya sea completo o filtrado) a la estructura de cursos
    cursos = transformar_df_a_cursos(df_final_filtrado)

    # --- Área Principal ---
    nombre_periodo_display = mapa_periodos.loc[mapa_periodos['periodo_id'] == periodo_seleccionado_id, 'nombre_periodo'].iloc[0]
    st.header(f"Horario para: {nombre_periodo_display} - {sub_semestre_seleccionado}")

    vista_semanal, vista_lista = st.tabs(["🗓️ Vista Semanal Interactiva", "📄 Lista Detallada"])

    with vista_semanal:
        if not cursos:
            st.warning("No hay cursos para mostrar con la selección actual.")
        else:
            mostrar_horario_interactivo(cursos)
    
    with vista_lista:
        if not cursos:
            st.warning("No hay cursos para mostrar con la selección actual.")
        else:
            st.info("Expande cada curso para ver los detalles.")
            for curso in cursos:
                with st.expander(f"**{curso['nombre']}**"):
                    st.markdown(f"**Profesor/a:** {curso['profesor']}")
                    st.table(pd.DataFrame(curso['horario']))
else:
    st.info("Esperando el archivo `horarios.csv` para cargar los datos.")
