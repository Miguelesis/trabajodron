import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import folium
from streamlit_folium import st_folium
import math

# --- Configuración de la Página ---
st.set_page_config(page_title="Optimización de Red Wi-Fi - UAVs", layout="wide")

st.title("Optimizador de red Wi-Fi para UAV 🛰️📶")
st.markdown("""
Esta aplicación optimiza el despliegue de drones (UAVs) para dar cobertura Wi-Fi de emergencia 
utilizando Programación Lineal Entera Mixta (MILP). Ahora puedes simular el impacto geográfico real.
""")

st.markdown("---")
st.header("⚙️ Configuración del Modelo")

# --- ORGANIZACIÓN EN PESTAÑAS EN EL CUERPO PRINCIPAL ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Límites de la Operación", 
    "⚡ Consumo de Energía", 
    "🗺️ Rendimiento de Cobertura", 
    "📊 Rendimiento de Tráfico"
])

# --- BLOQUE 1: Límites Generales ---
with tab1:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        energia_max = st.slider("Presupuesto de Energía Máxima (Wh)", 10, 1000, 500, step=10)
        trafico_min = st.slider("Capacidad de Tráfico Mínima (Mbps)", 1, 800, 50, step=5)
    with col_l2:
        espectro_5ghz = st.slider("Límite de Tiempo de drones 5 GHz (min)", 1, 300, 120, step=5)
        reserva_min = st.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=1)

# --- BLOQUE 2: Coeficientes de Energía ---
with tab2:
    st.markdown("##### Consumo por minuto (Wh por min) y mantenimiento fijo")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        w_p5 = st.number_input("Tipo P (5 GHz) [Wh/min]", min_value=1, value=5)
        w_p2 = st.number_input("Tipo P (2.4 GHz) [Wh/min]", min_value=1, value=3)
    with col_e2:
        w_l5 = st.number_input("Tipo L (5 GHz) [Wh/min]", min_value=1, value=6)
        w_l2 = st.number_input("Tipo L (2.4 GHz) [Wh/min]", min_value=1, value=4)
    with col_e3:
        w_res = st.number_input("Mantenimiento Reserva [Wh fijo]", min_value=1, value=10)

# --- BLOQUE 3: Coeficientes de Cobertura ---
with tab3:
    st.markdown("##### Rendimiento de Cobertura (km² por min)")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        c_p5_coef = st.number_input("Tipo P (5 GHz) [km²/min]", min_value=1, value=2)
        c_p2_coef = st.number_input("Tipo P (2.4 GHz) [km²/min]", min_value=1, value=4)
    with col_c2:
        c_l5_coef = st.number_input("Tipo L (5 GHz) [km²/min]", min_value=1, value=3)
        c_l2_coef = st.number_input("Tipo L (2.4 GHz) [km²/min]", min_value=1, value=5)

# --- BLOQUE 4: Coeficientes de Tráfico ---
with tab4:
    st.markdown("##### Rendimiento de Tráfico (Mbps por min)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t_p5_coef = st.number_input("Tipo P (5 GHz) [Mbps/min]", min_value=1, value=15)
        t_p2_coef = st.number_input("Tipo P (2.4 GHz) [Mbps/min]", min_value=1, value=10)
    with col_t2:
        t_l5_coef = st.number_input("Tipo L (5 GHz) [Mbps/min]", min_value=1, value=20)
        t_l2_coef = st.number_input("Tipo L (2.4 GHz) [Mbps/min]", min_value=1, value=12)

st.markdown("---")

# Botón principal destacado abajo de los parámetros
calcular = st.button("🚀 ¡Optimizar Red!", use_container_width=True, type="primary")

if calcular:
    # 1. Coeficientes de la Función Objetivo
    c = np.array([-c_p5_coef, -c_p2_coef, -c_l5_coef, -c_l2_coef, 0])

    # 2. Matrices de Restricciones Dinámicas
    A = np.array([
        [w_p5, w_p2, w_l5, w_l2, w_res],       
        [t_p5_coef, t_p2_coef, t_l5_coef, t_l2_coef, 0], 
        [1, 0, 1, 0,  0],                      
        [0, 0, 0, 0,  1]                       
    ])

    constraints = LinearConstraint(
        A, 
        lb=[-np.inf, trafico_min, -np.inf, reserva_min], 
        ub=[energia_max, np.inf, espectro_5ghz, np.inf]
    )

    bounds = Bounds(lb=0, ub=np.inf)
    integrality = np.array([1, 1, 1, 1, 1])

    # Ejecución del Solver
    res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)

    st.subheader("📊 Resultados de la Optimización")

    if res.success and res.x is not None:
        st.success("¡Optimización exitosa!")
        
        area_total = -res.fun
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Área de Cobertura Maximizada", value=f"{area_total:.1f} km²")
        with col2:
            energia_consumida = np.dot(A[0], res.x)
            st.metric(label="Energía Consumida Total", value=f"{energia_consumida:.1f} Wh", delta=f"Límite: {energia_max} Wh", delta_color="inverse")
        with col3:
            trafico_generado = np.dot(A[1], res.x)
            st.metric(label="Capacidad de Tráfico Lograda", value=f"{trafico_generado:.1f} Mbps", delta=f"Mínimo: {trafico_min} Mbps")

        # --- Estado Visual de la Batería ---
        st.markdown("### 🔋 Disponibilidad y Uso de la Batería")
        porcentaje_uso = min(1.0, energia_consumida / energia_max) if energia_max > 0 else 0.0
        st.progress(porcentaje_uso)
        st.caption(f"Se está utilizando el **{porcentaje_uso * 100:.1f}%** de la batería disponible ({energia_max} Wh). Libres: **{energia_max - energia_consumida:.1f} Wh**.")
        
        # --- Configuración Óptima de la Flota ---
        st.markdown("### 🛸 Configuración Óptima de la Flota:")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tipo P (5 GHz)", f"{int(res.x[0])} min")
        c2.metric("Tipo P (2.4 GHz)", f"{int(res.x[1])} min")
        c3.metric("Tipo L (5 GHz)", f"{int(res.x[2])} min")
        c4.metric("Tipo L (2.4 GHz)", f"{int(res.x[3])} min")
        c5.metric("Drones en Reserva", f"{int(res.x[4])} u")

        # --- VISUALIZACIÓN GEOGRÁFICA AUTOMÁTICA ---
        st.markdown("---")
        st.markdown("### 🌍 Visualización Geográfica Georreferenciada")
        
        if area_total > 0:
            # Calcular el radio equivalente en metros a partir de los km² logrados
            radio_metros = math.sqrt(area_total / math.pi) * 1000

            # Coordenadas por defecto (Ej: Madrid, España)
            lat, lon = 40.416775, -3.703790 
            
            st.info(f"Visualizando un radio estimado de cobertura de **{radio_metros:.1f} metros** a la redonda.")

            # Crear el mapa base de folium
            m = folium.Map(location=[lat, lon], zoom_start=14, control_scale=True)
            
            # Dibujar el círculo de cobertura
            folium.Circle(
                location=[lat, lon],
                radius=radio_metros,
                color="#1E88E5",
                fill=True,
                fill_color="#1E88E5",
                fill_opacity=0.3,
                popup=f"Zona de Cobertura Total: {area_total:.2f} km²"
            ).add_to(m)
            
            # Añadir un marcador al centro de mando
            folium.Marker(
                [lat, lon], 
                popup="Centro de Control de UAVs",
                icon=folium.Icon(color="red", icon="plane", prefix="fa")
            ).add_to(m)

            # CRUCIAL: returned_objects=[] evita que el mapa recargue la página al procesarse
            st_folium(m, width=900, height=500, returned_objects=[])
        else:
            st.warning("El área optimizada es 0 km². Modifica los valores para generar cobertura visible.")

        # --- Desgloses Técnicos ---
        st.markdown("---")
        with st.expander("⚡ Ver desglose de energía consumida por tipo de dron"):
            st.write(f"• **Tipo P en 5 GHz:** {int(res.x[0]) * w_p5} Wh")
            st.write(f"• **Tipo P en 2.4 GHz:** {int(res.x[1]) * w_p2} Wh")
            st.write(f"• **Tipo L en 5 GHz:** {int(res.x[2]) * w_l5} Wh")
            st.write(f"• **Tipo L en 2.4 GHz:** {int(res.x[3]) * w_l2} Wh")
            st.write(f"• **Reserva en Tierra:** {int(res.x[4]) * w_res} Wh")
            st.write(f"**Suma total:** {int(res.x[0])*w_p5 + int(res.x[1])*w_p2 + int(res.x[2])*w_l5 + int(res.x[3])*w_l2 + int(res.x[4])*w_res} Wh")

        with st.expander("📊 Ver desglose de tráfico aportado"):
            st.write(f"• **Tipo P en 5 GHz:** {int(res.x[0]) * t_p5_coef} Mbps")
            st.write(f"• **Tipo P en 2.4 GHz:** {int(res.x[1]) * t_p2_coef} Mbps")
            st.write(f"• **Tipo L en 5 GHz:** {int(res.x[2]) * t_l5_coef} Mbps")
            st.write(f"• **Tipo L en 2.4 GHz:** {int(res.x[3]) * t_l2_coef} Mbps")
            st.write(f"**Tráfico Total:** {int(res.x[0])*t_p5_coef + int(res.x[1])*t_p2_coef + int(res.x[2])*t_l5_coef + int(res.x[3])*t_l2_coef} Mbps")

        with st.expander("Ver datos brutos del solver"):
            st.write("Vector de decisión final `res.x`:", res.x)

    else:
        st.error(f"No se encontró una solución factible. Estado: {res.message}")
        st.warning("Prueba a relajar las restricciones (ej. aumentar la energía, bajar los consumos o disminuir el tráfico mínimo).")

else:
    st.info("👆 Modifica los parámetros en las pestañas de arriba y haz clic en **¡Optimizar Red!** para calcular.")
