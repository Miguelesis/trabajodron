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
energia_max = st.sidebar.slider("Presupuesto de Energía Máxima (Wh)", 100, 1000, 600, step=50)
trafico_min = st.sidebar.slider("Capacidad de Tráfico Mínima (Mbps)", 100, 800, 400, step=50)
espectro_5ghz = st.sidebar.slider("Límite de Tiempo de drones 5 GHz (min)", 10, 300, 100, step=10)
reserva_min = st.sidebar.number_input("Drones Mínimos en Reserva (u)", min_value=0, max_value=20, value=5)

# --- BLOQUE 2: Coeficientes de Energía (Sin tope máximo) ---
st.sidebar.subheader("⚡ Consumo de Energía (Wh por min)")
w_p5 = st.sidebar.number_input("Tipo P (5 GHz) [Wh/min]", min_value=1, value=2)
w_p2 = st.sidebar.number_input("Tipo P (2.4 GHz) [Wh/min]", min_value=1, value=2)
w_l5 = st.sidebar.number_input("Tipo L (5 GHz) [Wh/min]", min_value=1, value=1)
w_l2 = st.sidebar.number_input("Tipo L (2.4 GHz) [Wh/min]", min_value=1, value=1)
w_res = st.sidebar.number_input("Mantenimiento Reserva [Wh fijo]", min_value=1, value=10)

# --- BLOQUE 3: Coeficientes de Cobertura (Sin tope máximo) ---
st.sidebar.subheader("🗺️ Capacidad de Cobertura del Dron (km² por min)")
c_p5_coef = st.sidebar.number_input("Tipo P (5 GHz) [km²/min]", min_value=1, value=2)
c_p2_coef = st.sidebar.number_input("Tipo P (2.4 GHz) [km²/min]", min_value=1, value=4)
c_l5_coef = st.sidebar.number_input("Tipo L (5 GHz) [km²/min]", min_value=1, value=1)
c_l2_coef = st.sidebar.number_input("Tipo L (2.4 GHz) [km²/min]", min_value=1, value=2)

st.sidebar.markdown("---")
# --- BOTÓN PARA EJECUTAR LA OPTIMIZACIÓN ---
calcular = st.sidebar.button("🚀 ¡Optimizar Red!", use_container_width=True)

# El proceso se activa ÚNICAMENTE al presionar el botón
if calcular:
    # --- Definición Dinámica del Modelo Matemático ---

    # 1. Coeficientes de la Función Objetivo (Maximizar Área usando los inputs del usuario)
    # Recordar pasar a negativo porque milp() minimiza
    c = np.array([-c_p5_coef, -c_p2_coef, -c_l5_coef, -c_l2_coef, 0])

    # 2. Matrices de Restricciones Dinámicas (A_ub * x <= b_ub)
    A = np.array([
        [w_p5, w_p2, w_l5, w_l2, w_res],  # Energía (Configurada por el usuario)
        [3, 1, 3, 1,  0],                 # Tráfico (Fijo según el estándar Wi-Fi del problema original)
        [1, 0, 1, 0,  0],                 # Espectro 5 GHz
        [0, 0, 0, 0,  1]                  # Reserva
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
            # Calcular energía real consumida con los coeficientes elegidos
            energia_consumida = np.dot(A[0], res.x)
            st.metric(label="Energía Consumida Total", value=f"{energia_consumida:.1f} Wh", delta=f"Límite: {energia_max} Wh", delta_color="inverse")

        # --- Estado Visual de la Batería ---
        st.markdown("### 🔋 Disponibilidad y Uso de la Batería")
        porcentaje_uso = min(1.0, energia_consumida / energia_max)
        st.progress(porcentaje_uso)
        st.caption(f"Se está utilizando el **{porcentaje_uso * 100:.1f}%** de la batería disponible ({energia_max} Wh). Libres: **{energia_max - energia_consumida:.1f} Wh**.")

        st.markdown("### 🛸 Configuración Óptima de la Flota:")
        
        # Crear columnas para mostrar de forma visual las variables
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Tipo P (5 GHz)", f"{int(res.x[0])} min")
        c2.metric("Tipo P (2.4 GHz)", f"{int(res.x[1])} min")
        c3.metric("Tipo L (5 GHz)", f"{int(res.x[2])} min")
        c4.metric("Tipo L (2.4 GHz)", f"{int(res.x[3])} min")
        c5.metric("Drones en Reserva", f"{int(res.x[4])} u")
        
        # --- Desglose de energía dinámico ---
        st.markdown("---")
        with st.expander("⚡ Ver desglose de energía consumida por tipo de dron"):
            e_p5 = int(res.x[0]) * w_p5
            e_p2 = int(res.x[1]) * w_p2
            e_l5 = int(res.x[2]) * w_l5
            e_l2 = int(res.x[3]) * w_l2
            e_res = int(res.x[4]) * w_res
            
            st.write(f"• **Tipo P en 5 GHz:** {e_p5} Wh ({w_p5} Wh/min)")
            st.write(f"• **Tipo P en 2.4 GHz:** {e_p2} Wh ({w_p2} Wh/min)")
            st.write(f"• **Tipo L en 5 GHz:** {e_l5} Wh ({w_l5} Wh/min)")
            st.write(f"• **Tipo L en 2.4 GHz:** {e_l2} Wh ({w_l2} Wh/min)")
            st.write(f"• **Reserva en Tierra:** {e_res} Wh ({w_res} Wh fijo)")
            st.write(f"**Suma total:** {e_p5 + e_p2 + e_l5 + e_l2 + e_res} Wh")

        # --- Desglose de cobertura dinámico ---
        with st.expander("🗺️ Ver desglose de cobertura alcanzada por tipo de dron"):
            c_p5 = int(res.x[0]) * c_p5_coef
            c_p2 = int(res.x[1]) * c_p2_coef
            c_l5 = int(res.x[2]) * c_l5_coef
            c_l2 = int(res.x[3]) * c_l2_coef
            c_res = int(res.x[4]) * 0
            
            st.write(f"• **Tipo P en 5 GHz:** {c_p5} km² ({c_p5_coef} km²/min)")
            st.write(f"• **Tipo P en 2.4 GHz:** {c_p2} km² ({c_p2_coef} km²/min)")
            st.write(f"• **Tipo L en 5 GHz:** {c_l5} km² ({c_l5_coef} km²/min)")
            st.write(f"• **Tipo L en 2.4 GHz:** {c_l2} km² ({c_l2_coef} km²/min)")
            st.write(f"• **Reserva en Tierra:** {c_res} km² (0 km²/min)")
            st.write(f"**Cobertura Total:** {c_p5 + c_p2 + c_l5 + c_l2 + c_res} km²")

        # Mostrar el array crudo
        with st.expander("Ver datos brutos del solver"):
            st.write("Vector de decisión final `res.x`:", res.x)

    else:
        st.error(f"No se encontró una solución factible. Estado: {res.message}")
        st.warning("Prueba a relajar las restricciones (ej. aumentar la energía, bajar los consumos o disminuir el tráfico mínimo).")

else:
    # Estado en espera antes de hacer clic en el botón
    st.info("👈 Modifica los parámetros y restricciones que necesites en la barra lateral izquierda y haz clic en **¡Optimizar Red!** para calcular.")
