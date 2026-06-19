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

# --- Inputs en la Barra Lateral (Modificables por el usuario) ---
energia_max = st.sidebar.slider("Presupuesto de Energía Máxima (Wh)", 100, 1000, 600, step=50)
trafico_min = st.sidebar.slider("Capacidad de Tráfico Mínima (Mbps)", 100, 800, 400, step=50)
espectro_5ghz = st.sidebar.slider("Límite de Tiempo en Espectro 5 GHz (min)", 10, 300, 100, step=10)
reserva_min = st.sidebar.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

# --- Definición del Modelo Matemático ---

# 1. Coeficientes de la Función Objetivo (Maximizar Área)
# Como milp() minimiza por defecto, invertimos los signos de la cobertura:
# Z = 2x1 + 4x2 + 1x3 + 2x4 + 0x5 -> Pasamos a negativo
c = np.array([-2, -4, -1, -2, 0])

# 2. Matrices de Restricciones (A_ub * x <= b_ub)
# Para usar LinearConstraint, definimos los límites inferiores (lb) y superiores (ub)
# Fila 1: Energía -> 2x1 + 2x2 + 1x3 + 1x4 + 10x5 <= energia_max
# Fila 2: Tráfico -> 3x1 + 1x2 + 3x3 + 1x4 + 0x5 >= trafico_min
# Fila 3: Espectro -> 1x1 + 0x2 + 1x3 + 0x4 + 0x5 <= espectro_5ghz
# Fila 4: Reserva  -> 0x1 + 0x2 + 0x3 + 0x4 + 1x5 >= reserva_min

A = np.array([
    [2, 2, 1, 1, 10],  # Energía
    [3, 1, 3, 1,  0],  # Tráfico
    [1, 0, 1, 0,  0],  # Espectro 5 GHz
    [0, 0, 0, 0,  1]   # Reserva
])

# Límites para cada restricción [Mínimo, Máximo]
# -np.inf significa que no tiene límite inferior/superior según corresponda
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

# --- Renderizado de Resultados en Streamlit ---
st.subheader("📊 Resultados de la Optimización")

if res.success:
    st.success(f"¡Optimización exitosa! Estado: {res.message}")
    
    # Muestra las métricas principales destacadas
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Área Total de Cobertura Maximizada", value=f"{-res.fun:.1f} km²")
    with col2:
        # Calcular energía real consumida con el vector solución res.x
        energia_consumida = np.dot(A[0], res.x)
        st.metric(label="Energía Consumida", value=f"{energia_consumida:.1f} Wh", delta=f"Límite: {energia_max} Wh", delta_color="inverse")

    st.markdown("### 🛸 Configuración Óptima de la Flota:")
    
    # Crear columnas para mostrar de forma visual las variables
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tipo P (5 GHz)", f"{int(res.x[0])} min")
    c2.metric("Tipo P (2.4 GHz)", f"{int(res.x[1])} min")
    c3.metric("Tipo L (5 GHz)", f"{int(res.x[2])} min")
    c4.metric("Tipo L (2.4 GHz)", f"{int(res.x[3])} min")
    c5.metric("Drones en Reserva", f"{int(res.x[4])} u")
    
    # Opcional: Mostrar el array crudo como pedías en tu print(res.x)
    with st.expander("Ver datos brutos del solver"):
        st.write("Vector de decisión final `res.x`:", res.x)

else:
    st.error(f"No se encontró una solución factible. Estado: {res.message}")
    st.warning("Prueba a relajar las restricciones (ej. aumentar la energía o disminuir el tráfico mínimo).")
