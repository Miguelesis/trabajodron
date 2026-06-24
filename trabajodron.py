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
    st.markdown("##### Umbrales y capacidades operativas del sistema")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        energia_max = st.number_input("Presupuesto de Energía Máxima (Wh)", min_value=1, value=600)
        trafico_min = st.number_input("Capacidad de Tráfico Mínima (Mbps)", min_value=1, value=400)
    with col_l2:
        espectro_5ghz = st.number_input("Límite de Tiempo de drones 5 GHz (min)", min_value=1, value=100)
        # Cambio aquí: El valor inicial ahora es 5
        reserva_min = st.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

# --- BLOQUE 2: Coeficientes de Energía ---
with tab2:
    st.markdown("##### Consumo por minuto (Wh por min) y mantenimiento fijo")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        w_p5 = st.number_input("Tipo P (5 GHz) [Wh/min]", min_value=1, value=2)
        w_p2 = st.number_input("Tipo P (2.4 GHz) [Wh/min]", min_value=1, value=2)
    with col_e2:
        w_l5 = st.number_input("Tipo L (5 GHz) [Wh/min]", min_value=1, value=1)
        w_l2 = st.number_input("Tipo L (2.4 GHz) [Wh/min]", min_value=1, value=1)
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
        c_l5_coef = st.number_input("Tipo L (5 GHz) [km²/min]", min_value=1, value=1)
        c_l2_coef = st.number_input("Tipo L (2.4 GHz) [km²/min]", min_value=1, value=2)

# --- BLOQUE 4: Coeficientes de Tráfico ---
with tab4:
    st.markdown("##### Rendimiento de Tráfico (Mbps por min)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t_p5_coef = st.number_input("Tipo P (5 GHz) [Mbps/min]", min_value=1, value=3)
        t_p2_coef = st.number_input("Tipo P (2.4 GHz) [Mbps/min]", min_value=1, value=1)
    with col_t2:
        t_l5_coef = st.number_input("Tipo L (5 GHz) [Mbps/min]", min_value=1, value=3)
        t_l2_coef = st.number_input("Tipo L (2.4 GHz) [Mbps/min]", min_value=1, value=1)

st.markdown("---")

calcular = st.button("🚀 ¡Optimizar Red!", use_container_width=True, type="primary")

if calcular:
    c = np.array([-c_p5_coef, -c_p2_coef, -c_l5_coef, -c_l2_coef, 0])

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
            st
