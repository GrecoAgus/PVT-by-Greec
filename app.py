import streamlit as st
import CoolProp.CoolProp as CP
from datetime import datetime
import pytz
import plotly.graph_objects as go
import numpy as np
import scipy.optimize as opt
import math

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
        if prop == "k": return val
        return val
    except:
        return val

# === Función principal para obtener propiedades ===
def get_state(fluido, P=None, T=None, h=None, s=None, u=None, x=None, dentro_campana=True):
    # Ajustes según lo ingresado
    try:
        if T is not None and h is not None:
            # Encontrar P aproximada para T & h
            def fun(Pguess):
                return CP.PropsSI('H', 'T', T, 'P', Pguess, fluido) - h
            P_guess = CP.PropsSI('P', 'T', T, 'Q', 0, fluido)  # Punto saturación
            P = opt.fsolve(fun, P_guess)[0]
            # Ajuste si dentro de la campana
            if dentro_campana:
                if P < CP.PropsSI('P','T',T,'Q',0,fluido): P = CP.PropsSI('P','T',T,'Q',0,fluido)
                if P > CP.PropsSI('P','T',T,'Q',1,fluido): P = CP.PropsSI('P','T',T,'Q',1,fluido)
        elif T is not None and u is not None:
            def fun(Pguess):
                return CP.PropsSI('U', 'T', T, 'P', Pguess, fluido) - u
            P_guess = CP.PropsSI('P', 'T', T, 'Q', 0, fluido)
            P = opt.fsolve(fun, P_guess)[0]
            if dentro_campana:
                if P < CP.PropsSI('P','T',T,'Q',0,fluido): P = CP.PropsSI('P','T',T,'Q',0,fluido)
                if P > CP.PropsSI('P','T',T,'Q',1,fluido): P = CP.PropsSI('P','T',T,'Q',1,fluido)
        elif x is not None:
            # Para mezcla
            P = CP.PropsSI('P', 'T', T, 'Q', x, fluido)
    except:
        pass

    results = {}
    for p in to_return:
        try:
            if p=="x":
                results[p] = CP.PropsSI('Q','P',P,'T',T,fluido)
            elif p=="T":
                results[p] = T if T is not None else CP.PropsSI('T','P',P,'Q',0,fluido)
            elif p=="P":
                results[p] = P
            elif p=="h":
                results[p] = CP.PropsSI('H','P',P,'T',T,fluido)
            elif p=="s":
                results[p] = CP.PropsSI('S','P',P,'T',T,fluido)
            elif p=="u":
                results[p] = CP.PropsSI('U','P',P,'T',T,fluido)
            elif p=="rho":
                results[p] = CP.PropsSI('D','P',P,'T',T,fluido)
        except:
            results[p] = None

    # Propiedades extra
    try:
        results["vel_sonido"] = CP.PropsSI('A','P',P,'T',T,fluido)
        results["exergia"] = CP.PropsSI('HMASS','P',P,'T',T,fluido) - CP.PropsSI('HMASS','T',273.15,'P',101325,fluido)
        results["mu"] = CP.PropsSI('VISCOSITY','P',P,'T',T,fluido)
        results["cp"] = CP.PropsSI('C','P',P,'T',T,fluido)
        results["cv"] = CP.PropsSI('C','V','P',P,'T',T,fluido)
        results["k"] = results["cp"]/results["cv"] if results["cv"] not in [0,None] else None
    except:
        for ep in extra_props:
            results[ep] = None

    return results

# === Interfaz ===
st.title("Calculadora de propiedades termodinámicas")
fluido_seleccionado = st.selectbox("Seleccionar fluido", list(fluido_lista_organizada), index=1)
dentro_campana = st.checkbox("Dentro de la campana de vapor", value=True)

# Propiedades independientes
st.subheader("Propiedades independientes")
prop1 = st.selectbox("Propiedad 1", list(props.keys()), index=0)
val1_str = st.text_input(f"Valor {display_names.get(prop1, prop1)} ({input_units[prop1]})", value="25.0")
try:
    val1 = float(val1_str.replace(',', '.'))
except:
    val1 = 0.0

prop2 = st.selectbox("Propiedad 2", list(props.keys()), index=1)
val2_str = st.text_input(f"Valor {display_names.get(prop2, prop2)} ({input_units[prop2]})", value="101325.0")
try:
    val2 = float(val2_str.replace(',', '.'))
except:
    val2 = 0.0

# Conversión a SI
val1_SI = to_SI(prop1, val1, input_units[prop1])
val2_SI = to_SI(prop2, val2, input_units[prop2])

# Calcular estado
kwargs = {}
if prop1=="T": kwargs["T"]=val1_SI
elif prop1=="P": kwargs["P"]=val1_SI
elif prop1=="h": kwargs["h"]=val1_SI
elif prop1=="s": kwargs["s"]=val1_SI
elif prop1=="u": kwargs["u"]=val1_SI
elif prop1=="rho": kwargs["rho"]=val1_SI
elif prop1=="x": kwargs["x"]=val1_SI

if prop2=="T": kwargs["T"]=val2_SI
elif prop2=="P": kwargs["P"]=val2_SI
elif prop2=="h": kwargs["h"]=val2_SI
elif prop2=="s": kwargs["s"]=val2_SI
elif prop2=="u": kwargs["u"]=val2_SI
elif prop2=="rho": kwargs["rho"]=val2_SI
elif prop2=="x": kwargs["x"]=val2_SI

estado = get_state(fluido_seleccionado, dentro_campana=dentro_campana, **kwargs)

st.subheader("Propiedades calculadas")
for p in to_return:
    val = estado.get(p,None)
    if val is not None:
        st.write(f"{display_names.get(p,p)}: {from_SI(p,val,output_units[p]):.4f} {output_units[p]}")

# Historial (ahora 20 entradas)
if "historial" not in st.session_state:
    st.session_state.historial = []

if st.button("Agregar al historial"):
    st.session_state.historial.insert(0, (fluido_seleccionado, prop1, val1, prop2, val2, datetime.now()))
    st.session_state.historial = st.session_state.historial[:20]

st.subheader("Historial (últimas 20 entradas)")
for h in st.session_state.historial:
    st.write(f"{h[5].strftime('%H:%M:%S')} - {h[0]}: {h[1]}={h[2]}, {h[3]}={h[4]}")
