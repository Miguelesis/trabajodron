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
espectro_5ghz = st.sidebar.slider("Límite de Tiempo de drones 5 GHz (min)", 10, 300, 100, step=10)
reserva_min = st.sidebar.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

st.sidebar.markdown("---")
# --- BOTÓN PARA EJECUTAR LA OPTIMIZACIÓN ---
calcular = st.sidebar.button("🚀 ¡Optimizar Red!", use_container_width=True)

# El proceso se activa ÚNICAMENTE al presionar el botón
if calcular:
    # --- Definición del Modelo Matemático ---

    # 1. Coeficientes de la Función Objetivo (Maximizar Área)
    c = np.array([-2, -4, -1, -2, 0])

    # 2. Matrices de Restricciones (A_ub * x <= b_ub)
    A = np.array([
        [2, 2, 1, 1, 10],  # Energía
        [3, 1, 3, 1,  0],  # Tráfico
        [1, 0, 1, 0,  0],  # Espectro 5 GHz
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

    # --- Renderizado de Resultados en Streamlit ---
    st.subheader("📊 Resultados de la Optimización")

    if res.success:
        st.success("¡Optimización exitosa!")
        
        # Muestra las métricas principales destacadas
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Área Total de Cobertura Maximizada", value=f"{-res.fun:.1f} km²")
        with col2:
            # Calcular energía real consumida con el vector solución res.x
            energia_consumida = np.dot(A[0], res.x)
            st.metric(label="Energía Consumida Total", value=f"{energia_consumida:.1f} Wh", delta=f"Límite: {energia_max} Wh", delta_color="inverse")

        # --- SECCIÓN NUEVA: Estado Visual de la Batería ---
        st.markdown("### 🔋 Disponibilidad y Uso de la Batería")
        porcentaje_uso = min(1.0, energia_consumida / energia_max)
        st.progress(porcentaje_uso)
        st.caption(f"Se está utilizando el **{porcentaje_uso * 100:.1f}%** de la batería total disponible ({energia_max} Wh). Quedan libres **{energia_max - energia_consumida:.1f} Wh**.")

        st.markdown("### 🛸 Configuración Óptima de la Flota:")
        
        # Crear columnas para mostrar de forma visual las variables
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tipo P (5 GHz)", f"{int(res.x[0])} min")
        c2.metric("Tipo P (2.4 GHz)", f"{int(res.x[1])} min")
        c3.metric("Tipo L (5 GHz)", f"{int(res.x[2])} min")
        c4.metric("Tipo L (2.4 GHz)", f"{int(res.x[3])} min")
        c5.metric("Drones en Reserva", f"{int(res.x[4])} u")
        
        # --- SECCIÓN NUEVA: Desglose innecesario de energía por dron ---
        st.markdown("---")
        with st.expander("⚡ Ver desglose de energía consumida por tipo de dron"):
            e_p5 = int(res.x[0]) * 2
            e_p2 = int(res.x[1]) * 2
            e_l5 = int(res.x[2]) * 1
            e_l2 = int(res.x[3]) * 1
            e_res = int(res.x[4]) * 10
            
            st.write(f"• **Drones Tipo P en 5 GHz:** {e_p5} Wh (2 Wh/min)")
            st.write(f"• **Drones Tipo P en 2.4 GHz:** {e_p2} Wh (2 Wh/min)")
            st.write(f"• **Drones Tipo L en 5 GHz:** {e_l5} Wh (1 Wh/min)")
            st.write(f"• **Drones Tipo L en 2.4 GHz:** {e_l2} Wh (1 Wh/min)")
            st.write(f"• **Drones en Reserva (Tierra):** {e_res} Wh (10 Wh fijo)")
            st.write(f"**Suma total:** {e_p5 + e_p2 + e_l5 + e_l2 + e_res} Wh")
