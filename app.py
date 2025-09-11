import streamlit as st
import CoolProp.CoolProp as CP
from datetime import datetime
import pytz
import plotly.graph_objects as go
import numpy as np

# === Configuración inicial ===
fluidos = {
    "Agua": "Water",
    "Aire": "Air",
    "Dióxido de Carbono": "CO2",
    "Amoníaco": "Ammonia",
    "Metano": "Methane",
    "Etanol": "Ethanol",
}

fluido_lista_organizada = [
    "--- Muy usados ---",
    "Agua", "Aire", "Dióxido de Carbono", "Amoníaco", "Metano", "Oxígeno", "Nitrógeno", "Helio",
    "--- REFRIGERANTES ---",
    "R134a", "R22", "R404A", "R407C", "R410A", "R1234yf", "R1234ze(E)", "R600a", "R290",
    "--- Química / Industria ---",
    "Acetone", "Ethanol", "Benzene", "Toluene", "o-Xylene", "m-Xylene", "p-Xylene", "SulfurDioxide",
    "--- Gas ideal / Laboratorio ---",
    "Hydrogen", "Deuterium", "OrthoHydrogen", "ParaHydrogen", "OrthoDeuterium", "ParaDeuterium",
    "Neon", "Argon", "Xenon", "Krypton"
]

for f in fluido_lista_organizada:
    if not f.startswith("---") and f not in fluidos:
        fluidos[f] = f

props = {"T": "T", "P": "P", "h": "H", "s": "S", "u": "U", "rho": "D", "v": "D", "x": "Q"}
to_return = {"T": "T", "P": "P", "h": "H", "s": "S", "u": "U", "rho": "D", "x": "Q"}
extra_props = ["vel_sonido", "exergia", "mu", "cp", "cv", "k"]

unit_options = {
    "T": ["°C", "K", "°F"],
    "P": ["Pa", "kPa", "bar", "atm", "psi"],
    "h": ["kJ/kg", "J/kg", "BTU/lb"],
    "s": ["kJ/kgK", "J/kgK", "BTU/lbR"],
    "u": ["kJ/kg", "J/kg", "BTU/lb"],
    "rho": ["kg/m3", "lb/ft3"],
    "v": ["m3/kg", "ft3/lb"],
    "x": ["-"],
    "vel_sonido": ["m/s", "ft/s"],
    "exergia": ["kJ/kg", "BTU/lb"],
    "mu": ["Pa·s", "cP", "lb/(ft·s)"],
    "cp": ["kJ/kgK", "J/kgK", "cal/gK", "kcal/kgK"],
    "cv": ["kJ/kgK", "J/kgK", "cal/gK", "kcal/kgK"],
    "k": ["-"]
}

display_names = {
    "T": "T", "P": "P", "h": "h", "s": "s", "u": "u",
    "rho": "ρ", "v": "v", "x": "x",
    "vel_sonido": "a", "exergia": "Ex", "mu": "μ",
    "cp": "Cp", "cv": "Cv", "k": "k"
}

preset_systems = {
    "SI": {"T": "°C", "P": "Pa", "h": "kJ/kg", "s": "kJ/kgK",
           "u": "kJ/kg", "rho": "kg/m3", "v": "m3/kg", "x": "-",
           "vel_sonido": "m/s", "exergia": "kJ/kg", "mu": "Pa·s",
           "cp": "kJ/kgK", "cv": "kJ/kgK", "k": "-"},
    "Imperial": {"T": "°F", "P": "psi", "h": "BTU/lb", "s": "BTU/lbR",
                 "u": "BTU/lb", "rho": "lb/ft3", "v": "ft3/lb", "x": "-",
                 "vel_sonido": "ft/s", "exergia": "BTU/lb", "mu": "lb/(ft·s)",
                 "cp": "kJ/kgK", "cv": "kJ/kgK", "k": "-"}
}

input_units = {k: v[0] for k, v in unit_options.items()}
output_units = {k: v[0] for k, v in unit_options.items()}

T_ref = 15.0
P_ref = 101325.0

# === Funciones de conversión ===
def to_SI(prop, val, unit):
    try:
        if prop == "T":
            if unit == "°C": return val + 273.15
            if unit == "K": return val
            if unit == "°F": return (val - 32) * 5/9 + 273.15
        if prop == "P":
            if unit == "Pa": return val
            if unit == "kPa": return val * 1000
            if unit == "bar": return val * 1e5
            if unit == "atm": return val * 101325
            if unit == "psi": return val * 6894.757
        if prop in ["h", "u"]:
            if unit == "kJ/kg": return val * 1000
            if unit == "J/kg": return val
            if unit == "BTU/lb": return val * 2326
        if prop == "s":
            if unit == "kJ/kgK": return val * 1000
            if unit == "J/kgK": return val
            if unit == "BTU/lbR": return val * 4186.8
        if prop == "rho":
            if unit == "kg/m3": return val
            if unit == "lb/ft3": return val * 16.0185
        if prop == "v":
            if unit == "m3/kg": return val
            if unit == "ft3/lb": return val / 16.0185
        if prop == "vel_sonido":
            if unit == "m/s": return val
            if unit == "ft/s": return val / 0.3048
        if prop == "exergia":
            if unit == "kJ/kg": return val * 1000
            if unit == "BTU/lb": return val * 2326
        if prop == "mu":
            if unit == "Pa·s": return val
            if unit == "cP": return val / 1000
            if unit == "lb/(ft·s)": return val / 47.8803
        if prop in ["cp", "cv"]:
            if unit == "J/kgK": return val
            if unit == "kJ/kgK": return val * 1000
            if unit == "cal/gK": return val * 4186.8
            if unit == "kcal/kgK": return val * 4186.8
        return val
    except:
        return val

def from_SI(prop, val, unit):
    try:
        if prop == "T":
            if unit == "°C": return val - 273.15
            if unit == "K": return val
            if unit == "°F": return val * 9/5 - 459.67
        if prop == "P":
            if unit == "Pa": return val
            if unit == "kPa": return val / 1000
            if unit == "bar": return val / 1e5
            if unit == "atm": return val / 101325
            if unit == "psi": return val / 6894.757
        if prop in ["h", "u"]:
            if unit == "kJ/kg": return val / 1000
            if unit == "J/kg": return val
            if unit == "BTU/lb": return val / 2326
        if prop == "s":
            if unit == "kJ/kgK": return val / 1000
            if unit == "J/kgK": return val
            if unit == "BTU/lbR": return val / 4186.8
        if prop == "rho":
            if unit == "kg/m3": return val
            if unit == "lb/ft3": return val / 16.0185
        if prop == "v":
            if unit == "m3/kg": return val
            if unit == "ft3/lb": return val * 16.0185
        if prop == "vel_sonido":
            if unit == "m/s": return val
            if unit == "ft/s": return val * 0.3048
        if prop == "exergia":
            if unit == "kJ/kg": return val / 1000
            if unit == "BTU/lb": return val / 2326
        if prop == "mu":
            if unit == "Pa·s": return val
            if unit == "cP": return val * 1000
            if unit == "lb/(ft·s)": return val * 47.8803
        if prop in ["cp", "cv"]:
            if unit == "J/kgK": return val
            if unit == "kJ/kgK": return val / 1000
            if unit == "cal/gK": return val / 4186.8
            if unit == "kcal/kgK": return val / 4186.8
        return val
    except:
        return val

# === Función principal ===
def get_state(prop1, val1, prop2, val2, fluid):
    val1_SI = to_SI(prop1, val1, input_units[prop1])
    val2_SI = to_SI(prop2, val2, input_units[prop2])
    results = {}

    for k, v in to_return.items():
        try:
            val = CP.PropsSI(v, props[prop1], val1_SI, props[prop2], val2_SI, fluid)
            results[k] = from_SI(k, val, output_units[k])
        except:
            results[k] = None

    # Velocidad del sonido
    try:
        val = CP.PropsSI("A", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        results["vel_sonido"] = from_SI("vel_sonido", val, output_units["vel_sonido"])
    except:
        results["vel_sonido"] = None

    # Exergía
    try:
        h = CP.PropsSI("H", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        s = CP.PropsSI("S", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        h0 = CP.PropsSI("H", "T", T_ref + 273.15, "P", P_ref, fluid)
        s0 = CP.PropsSI("S", "T", T_ref + 273.15, "P", P_ref, fluid)
        ex = (h - h0) - (T_ref + 273.15) * (s - s0)
        results["exergia"] = from_SI("exergia", ex, output_units["exergia"])
    except:
        results["exergia"] = None

    # Viscosidad
    try:
        val = CP.PropsSI("V", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        results["mu"] = from_SI("mu", val, output_units["mu"])
    except:
        results["mu"] = None

    # cp, cv, k
    try:
        cp = CP.PropsSI("Cpmass", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        cv = CP.PropsSI("Cvmass", props[prop1], val1_SI, props[prop2], val2_SI, fluid)
        k = cp / cv if cv != 0 else None
        results["cp"] = from_SI("cp", cp, output_units["cp"])
        results["cv"] = from_SI("cv", cv, output_units["cv"])
        results["k"] = k
    except:
        results["cp"], results["cv"], results["k"] = None, None, None

    return results

# === Streamlit Interface ===
st.title("PVT by Greec 🌡️💨")
st.subheader("Calculadora de propiedades termodinámicas")

# Fluido
fluido_seleccionado = st.selectbox("Selecciona el fluido", fluido_lista_organizada,
                                   index=fluido_lista_organizada.index("Agua"))
if fluido_seleccionado.startswith("---"):
    fluido_seleccionado = "Agua"
fluido_cp = fluidos[fluido_seleccionado]

# Presets
st.sidebar.header("Configuración rápida")
preset_choice = st.sidebar.radio("Sistema de unidades", ["Ninguno", "SI", "Imperial"])
if preset_choice != "Ninguno":
    input_units.update(preset_systems[preset_choice])
    output_units.update(preset_systems[preset_choice])

# Unidades
st.sidebar.header("Configuración de unidades")
st.sidebar.subheader("Entrada")
for p in list(props.keys()) + extra_props:
    input_units[p] = st.sidebar.selectbox(f"Unidad ingreso {display_names.get(p,p)}",
                                          unit_options[p], index=unit_options[p].index(input_units.get(p, unit_options[p][0])))
st.sidebar.subheader("Salida")
for p in list(props.keys()) + extra_props:
    output_units[p] = st.sidebar.selectbox(f"Unidad salida {display_names.get(p,p)}",
                                           unit_options[p], index=unit_options[p].index(output_units.get(p, unit_options[p][0])))

# Estado de referencia
st.sidebar.header("Estado referencia exergía")
T_ref = st.sidebar.number_input("Temperatura referencia [°C]", value=T_ref)
P_ref = st.sidebar.number_input("Presión referencia [Pa]", value=P_ref)

# Propiedades independientes
st.subheader("Propiedades independientes")
prop1 = st.selectbox("Propiedad 1", list(props.keys()), index=0)
val1 = st.number_input(f"Valor {display_names.get(prop1, prop1)} ({input_units[prop1]})", value=25.0)
prop2 = st.selectbox("Propiedad 2", list(props.keys()), index=1)
val2 = st.number_input(f"Valor {display_names.get(prop2, prop2)} ({input_units[prop2]})", value=101325.0)

# Inicializar historial
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

tz = pytz.timezone("America/Argentina/Buenos_Aires")

# Calcular
if st.button("Calcular"):
    res = get_state(prop1, val1, prop2, val2, fluido_cp)
    st.subheader("Resultados")
    for k, v in res.items():
        if v is not None:
            st.write(f"**{display_names.get(k,k)}** = {v:.5g} {output_units[k]}")
        else:
            st.write(f"**{display_names.get(k,k)}**: No disponible")
    if len(st.session_state['historial']) >= 10:
        st.session_state['historial'].pop(0)
    st.session_state['historial'].append({"fecha": datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S"),
                                          "entrada": {prop1: val1, prop2: val2}, "resultado": res})

# Historial
hist = st.session_state.get('historial', [])
if hist:
    with st.expander("Mostrar Historial"):
        max_index = len(hist) - 1
        index = st.slider("Selecciona cálculo", 0, max_index, max_index, key="slider_historial") if len(hist) > 1 else 0
        st.write(f"**Cálculo {index+1} ({hist[index]['fecha']})**")
        st.write("**Entradas:**")
        for prop, val in hist[index]["entrada"].items():
            st.write(f"{display_names.get(prop, prop)} = {val} {input_units[prop]}")
        st.write("**Resultados:**")
        for k, v in hist[index]["resultado"].items():
            if v is not None:
                st.write(f"{display_names.get(k,k)} = {v:.5g} {output_units[k]}")
            else:
                st.write(f"{display_names.get(k,k)}: No disponible")

# === Gráfico interactivo plegable ===
import numpy as np  # <--- asegurate de importar numpy

with st.expander("Mostrar Gráfico"):
    # Limitamos las opciones
    grafico_tipo = st.selectbox("Selecciona diagrama", ["T vs S", "P vs v"])

    fig = go.Figure()

    try:
        fluid = fluido_cp
        T_triple = CP.PropsSI('Ttriple', fluid)
        T_crit = CP.PropsSI('Tcrit', fluid)
        T_vals = np.linspace(T_triple + 0.01, T_crit - 0.01, 100)  # rango de temperatura

        if grafico_tipo == "T vs S":
            # Curva de saturación
            S_liq = [CP.PropsSI('S', 'T', T, 'Q', 0, fluid) for T in T_vals]
            S_vap = [CP.PropsSI('S', 'T', T, 'Q', 1, fluid) for T in T_vals]

            # Convertir solo la curva de saturación a unidades de salida
            T_plot = [from_SI("T", T, output_units["T"]) for T in T_vals]
            S_liq_plot = [from_SI("s", s, output_units["s"]) for s in S_liq]
            S_vap_plot = [from_SI("s", s, output_units["s"]) for s in S_vap]

            fig.add_trace(go.Scatter(x=S_liq_plot, y=T_plot, mode='lines', name="Líquido saturado"))
            fig.add_trace(go.Scatter(x=S_vap_plot, y=T_plot, mode='lines', name="Vapor saturado"))
            fig.update_layout(xaxis_title=f"S ({output_units['s']})", yaxis_title=f"T ({output_units['T']})")

            # Puntos del historial (ya están en unidades de salida)
            x_vals = [h["resultado"].get("s") for h in hist if h["resultado"].get("s") is not None]
            y_vals = [h["resultado"].get("T") for h in hist if h["resultado"].get("T") is not None]

        elif grafico_tipo == "P vs v":
            # Curva de saturación
            P_liq = [CP.PropsSI('P', 'T', T, 'Q', 0, fluid) for T in T_vals]
            P_vap = [CP.PropsSI('P', 'T', T, 'Q', 1, fluid) for T in T_vals]
            v_liq = [1/CP.PropsSI('D', 'T', T, 'Q', 0, fluid) for T in T_vals]  # v = 1/ρ
            v_vap = [1/CP.PropsSI('D', 'T', T, 'Q', 1, fluid) for T in T_vals]

            # Convertir solo la curva de saturación a unidades de salida
            P_liq_plot = [from_SI("P", P, output_units["P"]) for P in P_liq]
            P_vap_plot = [from_SI("P", P, output_units["P"]) for P in P_vap]
            v_liq_plot = [from_SI("v", v, output_units["v"]) for v in v_liq]
            v_vap_plot = [from_SI("v", v, output_units["v"]) for v in v_vap]

            fig.add_trace(go.Scatter(x=v_liq_plot, y=P_liq_plot, mode='lines', name="Líquido saturado"))
            fig.add_trace(go.Scatter(x=v_vap_plot, y=P_vap_plot, mode='lines', name="Vapor saturado"))
            fig.update_layout(xaxis_title=f"v ({output_units['v']})", yaxis_title=f"P ({output_units['P']})")

            # Puntos del historial (ya están en unidades de salida)
            x_vals = [h["resultado"].get("v") for h in hist if h["resultado"].get("v") is not None]
            y_vals = [h["resultado"].get("P") for h in hist if h["resultado"].get("P") is not None]

        # Puntos del historial con numeritos
        if x_vals and y_vals:
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                text=[str(i) for i in range(len(x_vals))],
                textposition="top right",
                marker=dict(size=8, color='red'),
                name="Historial"
            ))

            # Flechas que unen puntos consecutivos
            for i in range(len(x_vals)-1):
                fig.add_annotation(
                    x=x_vals[i+1],
                    y=y_vals[i+1],
                    ax=x_vals[i],
                    ay=y_vals[i],
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1,
                    arrowwidth=1.5,
                    arrowcolor="green"
                )

            # Agregar "trace" invisible solo para la leyenda del sentido
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='lines+markers',
                marker=dict(size=6, color='green'),
                line=dict(color='green', width=2),
                name="Sentido"
            ))

    except Exception as e:
        st.write("No se pudo generar la curva de saturación:", e)

    st.plotly_chart(fig)
