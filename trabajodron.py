import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# --- Configuración de la Página ---
st.set_page_config(page_title="Optimización de Red Wi-Fi - UAVs", layout="wide")

st.title("UAV Wi-Fi Network Optimizer 🛰️📶")
st.markdown("""
Esta aplicación optimiza el despliegue de drones (UAVs) para dar cobertura Wi-Fi de emergencia 
utilizando Programación Lineal Entera Mixta (MILP). Ahora puedes modificar tanto las restricciones como los coeficientes técnicos.
""")

st.sidebar.header("⚙️ Configuración del Modelo")

# --- BLOQUE 1: Límites Generales ---
st.sidebar.subheader("📋 Límites de la Operación")
energia_max = st.sidebar.slider("Presupuesto de Energía Máxima (Wh)", 100, 2000, 600, step=50)
trafico_min = st.sidebar.slider("Capacidad de Tráfico Mínima (Mbps)", 50, 1000, 200, step=50)
espectro_5ghz = st.sidebar.slider("Límite de Tiempo de drones 5 GHz (min)", 10, 300, 100, step=10)
reserva_min = st.sidebar.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

# --- BLOQUE 2: Coeficientes de Energía ---
st.sidebar.subheader("⚡ Consumo de Energía (Wh por min)")
w_p5 = st.sidebar.number_input("Tipo P (5 GHz) [Wh/min]", min_value=1, value=4)
w_p2 = st.sidebar.number_input("Tipo P (2.4 GHz) [Wh/min]", min_value=1, value=3)
w_l5 = st.sidebar.number_input("Tipo L (5 GHz) [Wh/min]", min_value=1, value=2)
w_l2 = st.sidebar.number_input("Tipo L (2.4 GHz) [Wh/min]", min_value=1, value=1)
w_res = st.sidebar.number_input("Mantenimiento Reserva [Wh fijo]", min_value=1, value=10)

# --- BLOQUE 3: Coeficientes de Cobertura ---
st.sidebar.subheader("🗺️ Rendimiento de Cobertura (km² por min)")
c_p5_coef = st.sidebar.number_input("Tipo P (5 GHz) [km²/min]", min_value=1, value=3)
c_p2_coef = st.sidebar.number_input("Tipo P (2.4 GHz) [km²/min]", min_value=1, value=5)
c_l5_coef = st.sidebar.number_input("Tipo L (5 GHz) [km²/min]", min_value=1, value=2)
c_l2_coef = st.sidebar.number_input("Tipo L (2.4 GHz) [km²/min]", min_value=1, value=3)

# --- BLOQUE 4: Coeficientes de Tráfico (¡NUEVO!) ---
st.sidebar.subheader("📊 Rendimiento de Tráfico (Mbps por min)")
t_p5_coef = st.sidebar.number_input("Tipo P (5 GHz) [Mbps/min]", min_value=1, value=8)
t_p2_coef = st.sidebar.number_input("Tipo P (2.4 GHz) [Mbps/min]", min_value=1, value=3)
t_l5_coef = st.sidebar.number_input("Tipo L (5 GHz) [Mbps/min]", min_value=1, value=5)
t_l2_coef = st.sidebar.number_input("Tipo L (2.4 GHz) [Mbps/min]", min_value=1, value=2)

st.sidebar.markdown("---")
calcular = st.sidebar.button("🚀 ¡Optimizar Red!", use_container_width=True)

if calcular:
    # 1. Coeficientes de la Función Objetivo (Minimizar el negativo para Maximizar Área)
    c = np.array([-c_p5_coef, -c_p2_coef, -c_l5_coef, -c_l2_coef, 0])

    # 2. Matrices de Restricciones Dinámicas Actualizada con los coeficientes de tráfico
    A = np.array([
        [w_p5, w_p2, w_l5, w_l2, w_res],       # Energía
        [t_p5_coef, t_p2_coef, t_l5_coef, t_l2_coef, 0], # Tráfico (Dinámico)
        [1, 0, 1, 0,  0],                      # Espectro 5 GHz
        [0, 0, 0, 0,  1]                       # Reserva
    ])

    # Límites para cada restricción [Mínimo, Máximo]
    constraints = LinearConstraint(
        A, 
        lb=[-np.inf, trafico_min, -np.inf, reserva_min], 
        ub=[energia_max, np.inf, espectro_5ghz, np.inf]
    )

    # 3. Límites de las variables (todas >= 0)
    bounds = Bounds(lb=0, ub=np.inf)

    # 4. Integridad (Todas las variables deben ser enteras)
    integrality = np.array([1, 1, 1, 1, 1])

    # Ejecución de la Optimización
    res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)

    # --- Renderizado de Resultados ---
    st.subheader("📊 Resultados de la Optimización")

    if res.success:
        st.success("¡Optimización exitosa!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Área de Cobertura Maximizada", value=f"{-res.fun:.1f} km²")
        with col2:
            energia_consumida = np.dot(A[0], res.x)
            st.metric(label="Energía Consumida Total", value=f"{energia_consumida:.1f} Wh", delta=f"Límite: {energia_max} Wh", delta_color="inverse")
        with col3:
            trafico_generado = np.dot(A[1], res.x)
            st.metric(label="Capacidad de Tráfico Lograda", value=f"{trafico_generado:.1f} Mbps", delta=f"Mínimo: {trafico_min} Mbps")

        # --- Estado Visual de la Batería ---
        st.markdown("### 🔋 Disponibilidad y Uso de la Batería")
        porcentaje_uso = min(1.0, energia_consumida / energia_max)
        st.progress(porcentaje_uso)
        st.caption(f"Se está utilizando el **{porcentaje_uso * 100:.1f}%** de la batería disponible ({energia_max} Wh). Libres: **{energia_max - energia_consumida:.1f} Wh**.")

        st.markdown("### 🛸 Configuración Óptima de la Flota:")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tipo P (5 GHz)", f"{int(res.x[0])} min")
        c2.metric("Tipo P (2.4 GHz)", f"{int(res.x[1])} min")
        c3.metric("Tipo L (5 GHz)", f"{int(res.x[2])} min")
        c4.metric("Tipo L (2.4 GHz)", f"{int(res.x[3])} min")
        c5.metric("Drones en Reserva", f"{int(res.x[4])} u")
        
        # --- Desgloses en Expanders ---
        st.markdown("---")
        with st.expander("⚡ Ver desglose de energía consumida por tipo de dron"):
            e_p5 = int(res.x[0]) * w_p5
            e_p2 = int(res.x[1]) * w_p2
            e_l5 = int(res.x[2]) * w_l5
            e_l2 = int(res.x[3]) * w_l2
            e_res = int(res.x[4]) * w_res
            st.write(f"• **Tipo P en 5 GHz:** {e_p5} Wh")
            st.write(f"• **Tipo P en 2.4 GHz:** {e_p2} Wh")
            st.write(f"• **Tipo L en 5 GHz:** {e_l5} Wh")
            st.write(f"• **Tipo L en 2.4 GHz:** {e_l2} Wh")
            st.write(f"• **Reserva en Tierra:** {e_res} Wh")
            st.write(f"**Suma total:** {e_p5 + e_p2 + e_l5 + e_l2 + e_res} Wh")

        with st.expander("📊 Ver desglose de tráfico aportado"):
            t_p5 = int(res.x[0]) * t_p5_coef
            t_p2 = int(res.x[1]) * t_p2_coef
            t_l5 = int(res.x[2]) * t_l5_coef
            t_l2 = int(res.x[3]) * t_l2_coef
            st.write(f"• **Tipo P en 5 GHz:** {t_p5} Mbps")
            st.write(f"• **Tipo P en 2.4 GHz:** {t_p2} Mbps")
            st.write(f"• **Tipo L en 5 GHz:** {t_l5} Mbps")
            st.write(f"• **Tipo L en 2.4 GHz:** {t_l2} Mbps")
            st.write(f"**Tráfico Total:** {t_p5 + t_p2 + t_l5 + t_l2} Mbps")

        with st.expander("Ver datos brutos del solver"):
            st.write("Vector de decisión final `res.x`:", res.x)

    else:
        st.error(f"No se encontró una solución factible. Estado: {res.message}")
        st.warning("Prueba a relajar las restricciones (ej. aumentar la energía, bajar los consumos o disminuir el tráfico mínimo).")

else:
    st.info("👈 Modifica los parámetros y restricciones que necesites en la barra lateral izquierda y haz clic en **¡Optimizar Red!** para calcular.")
