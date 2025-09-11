import streamlit as st
import CoolProp.CoolProp as CP
from datetime import datetime

# === Configuración inicial ===
fluidos = {
    "Agua": "Water",
    "Aire": "Air",
    "Dióxido de Carbono": "CO2",
    "Amoníaco": "Ammonia",
    "Metano": "Methane",
    "Etanol": "Ethanol",
}

props = {
    "T": "T", "P": "P", "h": "H", "s": "S",
    "u": "U", "rho": "D", "v": "D", "x": "Q"
}

to_return = {
    "T": "T", "P": "P", "h": "H", "s": "S",
    "u": "U", "rho": "D", "x": "Q"
}

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

# Símbolos y nombres estéticos
display_names = {
    "T": "T", "P": "P", "h": "h", "s": "s", "u": "u",
    "rho": "ρ", "v": "v", "x": "x",
    "vel_sonido": "a", "exergia": "Ex", "mu": "μ",
    "cp": "Cp", "cv": "Cv", "k": "k"
}

preset_systems = {
    "SI": {
        "T": "°C", "P": "Pa", "h": "kJ/kg", "s": "kJ/kgK",
        "u": "kJ/kg", "rho": "kg/m3", "v": "m3/kg", "x": "-",
        "vel_sonido": "m/s", "exergia": "kJ/kg", "mu": "Pa·s",
        "cp": "kJ/kgK", "cv": "kJ/kgK", "k": "-"
    },
    "Imperial": {
        "T": "°F", "P": "psi", "h": "BTU/lb", "s": "BTU/lbR",
        "u": "BTU/lb", "rho": "lb/ft3", "v": "ft3/lb", "x": "-",
        "vel_sonido": "ft/s", "exergia": "BTU/lb", "mu": "lb/(ft·s)",
        "cp": "kJ/kgK", "cv": "kJ/kgK", "k": "-"
    }
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

# === Interfaz Streamlit ===
st.title("PVT by Greec 🌡️💨")
st.subheader("Calculadora de propiedades termodinámicas")

# --- Fluido ---
fluido_seleccionado = st.selectbox("Selecciona el fluido", list(fluidos.keys()))
fluido_cp = fluidos[fluido_seleccionado]

# --- Presets ---
st.sidebar.header("Configuración rápida")
preset_choice = st.sidebar.radio("Sistema de unidades", ["Ninguno", "SI", "Imperial"])
if preset_choice != "Ninguno":
    input_units.update(preset_systems[preset_choice])
    output_units.update(preset_systems[preset_choice])

# --- Unidades ---
st.sidebar.header("Configuración de unidades")
st.sidebar.subheader("Entrada")
for p in list(props.keys()) + extra_props:
    input_units[p] = st.sidebar.selectbox(f"Unidad ingreso {display_names.get(p,p)}", unit_options[p],
                                          index=unit_options[p].index(input_units.get(p, unit_options[p][0])))

st.sidebar.subheader("Salida")
for p in list(props.keys()) + extra_props:
    output_units[p] = st.sidebar.selectbox(f"Unidad salida {display_names.get(p,p)}", unit_options[p],
                                           index=unit_options[p].index(output_units.get(p, unit_options[p][0])))

# --- Estado de referencia ---
st.sidebar.header("Estado referencia exergía")
T_ref = st.sidebar.number_input("Temperatura referencia [°C]", value=T_ref)
P_ref = st.sidebar.number_input("Presión referencia [Pa]", value=P_ref)

# --- Propiedades independientes ---
st.subheader("Propiedades independientes")
prop1 = st.selectbox("Propiedad 1", list(props.keys()), index=0)
val1 = st.number_input(f"Valor {display_names.get(prop1, prop1)} ({input_units[prop1]})", value=25.0)
prop2 = st.selectbox("Propiedad 2", list(props.keys()), index=1)
val2 = st.number_input(f"Valor {display_names.get(prop2, prop2)} ({input_units[prop2]})", value=101325.0)

# --- Inicializar historial ---
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

# --- Botón calcular ---
if st.button("Calcular"):
    res = get_state(prop1, val1, prop2, val2, fluido_cp)
    # Mostrar resultados principales
    st.subheader("Resultados")
    for k, v in res.items():
        if v is not None:
            st.write(f"**{display_names.get(k,k)}** = {v:.5g} {output_units[k]}")
        else:
            st.write(f"**{display_names.get(k,k)}**: No disponible")
    # Guardar en historial
    if len(st.session_state['historial']) >= 10:
        st.session_state['historial'].pop(0)
    st.session_state['historial'].append({
        "fecha": datetime.now().strftime("%H:%M:%S"),
        "entrada": {prop1: val1, prop2: val2},
        "resultado": res
    })

# --- Historial con slider ---
# --- Historial con slider vertical (opcional) ---
hist = st.session_state.get('historial', [])

if hist:  # Solo si hay al menos un cálculo
    with st.expander("Mostrar Historial"):
        max_index = len(hist) - 1  # índice máximo válido
        # Slider vertical (step=1, enteros)
        index = st.slider(
            "Selecciona cálculo",
            min_value=0,
            max_value=max_index,
            value=max_index,  # mostrar el último cálculo por defecto
            step=1,
            key="slider_historial"
        )

        st.write(f"**Cálculo {index+1} ({hist[index]['fecha']})**")
        st.write("**Entradas:**")
        for prop, val in hist[index]["entrada"].items():
            st.write(f"{display_names.get(prop, prop)} = {val} {input_units[prop]}")
        
        st.write("**Resultados:**")
        for k, v in hist[index]["resultado"].items():
            if v is not None:
                st.write(f"**{display_names.get(k,k)}** = {v:.5g} {output_units[k]}")
            else:
                st.write(f"**{display_names.get(k,k)}**: No disponible")





