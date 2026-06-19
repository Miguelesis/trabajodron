import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# --- Configuración de la Página ---
st.set_page_config(page_title="Optimización de Red Wi-Fi - UAVs", layout="wide")

st.title("UAV Wi-Fi Network Optimizer 🛰️📶")
st.markdown("""
Esta aplicación optimiza el despliegue de drones (UAVs) para dar cobertura Wi-Fi de emergencia 
utilizando Programación Lineal Entera Mixta (MILP).
""")

st.sidebar.header("⚙️ Parámetros y Restricciones")

# --- Inputs en la Barra Lateral ---
energia_max = st.sidebar.slider("Presupuesto de Energía Máxima (Wh)", 100, 1000, 600, step=50)
trafico_min = st.sidebar.slider("Capacidad de Tráfico Mínima (Mbps)", 100, 800, 400, step=50)

# Cambio de nombre solicitado aquí:
espectro_5ghz = st.sidebar.slider("Límite de tiempo de los drones de capacidad 5 GHz (min)", 10, 300, 100, step=10)

reserva_min = st.sidebar.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

st.sidebar.markdown("---")
# --- NUEVO: Botón para ejecutar la optimización ---
calcular = st.sidebar.button("🚀 ¡Optimizar Red!", use_container_width=True)

# La optimización solo se ejecuta al presionar el botón
if calcular:
    # --- Definición del Modelo Matemático ---

    # 1. Coeficientes de la Función Objetivo (Maximizar Área)
    c = np.array([-2, -4, -1, -2, 0])

    # 2. Matrices de Restricciones (A_ub * x <= b_ub)
    A = np.array([
        [2, 2, 1, 1, 10],  # Energía
        [3, 1, 3, 1,  0],  # Tráfico
        [1, 0, 1, 0,  0],  # Tiempo en 5 GHz
        [0, 0, 0, 0,  1]   # Reserva
    ])

    # Límites para cada restricción [Mínimo, Máximo]
    constraints = LinearConstraint(
        A, 
        lb=[-np.inf, trafico_min, -np.inf, reserva_min], 
        ub=[energia_max, np.inf, espectro_5ghz, np.inf]
    )

    # 3. Límites de las variables (todas >= 0)
    bounds = Bounds(lb=0, ub=np.inf)

    # 4. Integridad: 1 significa que la variable es ENTERA
    integrality = np.array([1, 1, 1, 1, 1])

    # --- Ejecución de la Optimización ---
    res = milp(
        c=c,
        constraints=constraints,
        bounds=bounds,
        integrality=integrality
    )

    # --- Renderizado de Resultados ---
    st.subheader("📊 Resultados de la Optimización")
