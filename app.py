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

# === Conversiónes ===
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
        if val is None:
            return None
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

# === Buscador de bracket para la raíz en presión ===
def find_pressure_bracket(func, p_min=1e-6, p_max=1e8, n=80):
    ps = np.logspace(np.log10(max(p_min,1e-12)), np.log10(p_max), n)
    prev_f = None
    prev_p = None
    for p in ps:
        try:
            f = func(p)
            if not math.isfinite(f):
                prev_f = None
                prev_p = None
                continue
            if prev_f is None:
                prev_f = f
                prev_p = p
                continue
            if prev_f * f < 0:
                return prev_p, p
            prev_f = f
            prev_p = p
        except Exception:
            prev_f = None
            prev_p = None
    return None

# === Calcula P a partir de (T,h) o (T,u) ===
def P_from_T_H_or_U(T_SI, val_SI, fluid, prop="H", dentro_campana=False):
    """
    Devuelve presión (Pa) para (T, H) o (T, U).
    Si dentro_campana=True devuelve la presión de saturación en T.
    """
    try:
        # si el usuario fuerza dentro de la campana devolvemos la presión de saturación
        if dentro_campana:
            return CP.PropsSI("P", "T", T_SI, "Q", 0, fluid)
        # comprobar si val_SI cae entre liquido y vapor (entonces estado en campana)
        try:
            if prop == "H":
                h_l = CP.PropsSI("H", "T", T_SI, "Q", 0, fluid)
                h_v = CP.PropsSI("H", "T", T_SI, "Q", 1, fluid)
            else:
                h_l = CP.PropsSI("U", "T", T_SI, "Q", 0, fluid)
                h_v = CP.PropsSI("U", "T", T_SI, "Q", 1, fluid)
            if (h_l is not None and h_v is not None) and (min(h_l, h_v) <= val_SI <= max(h_l, h_v)):
                return CP.PropsSI("P", "T", T_SI, "Q", 0, fluid)
        except Exception:
            pass

        # definir función para raíz
        def f(P):
            return CP.PropsSI(prop, "T", T_SI, "P", P, fluid) - val_SI

        bracket = find_pressure_bracket(f)
        if bracket is None:
            return None
        p_lo, p_hi = bracket
        # comprobación final de signos
        f_lo = f(p_lo); f_hi = f(p_hi)
        if not (math.isfinite(f_lo) and math.isfinite(f_hi)) or (f_lo * f_hi > 0):
            return None
        P_root = opt.brentq(f, p_lo, p_hi, maxiter=100)
        return P_root
    except Exception:
        return None

# === Función principal completa (mantiene todas las propiedades) ===
def get_state(prop1, val1, prop2, val2, fluid, dentro_campana_flag=False):
    # convertir entradas a SI
    val1_SI = to_SI(prop1, val1, input_units.get(prop1, "°C"))
    val2_SI = to_SI(prop2, val2, input_units.get(prop2, "Pa"))

    # preparar call props
    call_prop1 = prop1
    call_val1_SI = val1_SI
    call_prop2 = prop2
    call_val2_SI = val2_SI

    # caso (T,h) o (T,u) -> intentar obtener P (respetando el flag de la UI)
    if ("T" in (prop1, prop2)) and (("h" in (prop1, prop2)) or ("u" in (prop1, prop2))):
        if prop1 == "T":
            T_SI = val1_SI
            prop_HU = prop2
            val_HU_SI = val2_SI
        else:
            T_SI = val2_SI
            prop_HU = prop1
            val_HU_SI = val1_SI
        prop_for_func = "H" if prop_HU == "h" else "U"
        P_guess = P_from_T_H_or_U(T_SI, val_HU_SI, fluid, prop=prop_for_func, dentro_campana=dentro_campana_flag)
        if P_guess is not None:
            call_prop1 = "T"
            call_val1_SI = T_SI
            call_prop2 = "P"
            call_val2_SI = P_guess
        else:
            # intentar dejarlos tal cual y CoolProp lo manejará (puede fallar)
            call_prop1 = prop1
            call_val1_SI = val1_SI
            call_prop2 = prop2
            call_val2_SI = val2_SI

    results = {}

    # calcular propiedades principales
    for k, v in to_return.items():
        try:
            raw = CP.PropsSI(v, props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
            # 'x' es adimensional, from_SI lo devolverá sin cambios en general
            results[k] = from_SI(k, raw, output_units.get(k, output_units["T"]))
        except Exception:
            results[k] = None

    # volumen específico (v = 1/rho) — lo calculamos explícitamente porque suele ser útil
    try:
        rho_raw = CP.PropsSI("D", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        if rho_raw is None or rho_raw == 0:
            results["v"] = None
        else:
            v_raw = 1.0 / rho_raw
            results["v"] = from_SI("v", v_raw, output_units.get("v", output_units["v"]))
    except Exception:
        results["v"] = None

    # velocidad del sonido
    try:
        a_raw = CP.PropsSI("A", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        results["vel_sonido"] = from_SI("vel_sonido", a_raw, output_units.get("vel_sonido", output_units["vel_sonido"]))
    except Exception:
        results["vel_sonido"] = None

    # exergía
    try:
        h_raw = CP.PropsSI("H", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        s_raw = CP.PropsSI("S", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        h0 = CP.PropsSI("H", "T", T_ref + 273.15, "P", P_ref, fluid)
        s0 = CP.PropsSI("S", "T", T_ref + 273.15, "P", P_ref, fluid)
        ex_raw = (h_raw - h0) - (T_ref + 273.15) * (s_raw - s0)
        results["exergia"] = from_SI("exergia", ex_raw, output_units.get("exergia", output_units["exergia"]))
    except Exception:
        results["exergia"] = None

    # viscosidad
    try:
        mu_raw = CP.PropsSI("V", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        results["mu"] = from_SI("mu", mu_raw, output_units.get("mu", output_units["mu"]))
    except Exception:
        results["mu"] = None

    # cp, cv, k
    try:
        cp_raw = CP.PropsSI("Cpmass", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        cv_raw = CP.PropsSI("Cvmass", props[call_prop1], call_val1_SI, props[call_prop2], call_val2_SI, fluid)
        k_val = None
        if (cv_raw is not None) and (cv_raw != 0):
            k_val = cp_raw / cv_raw
        results["cp"] = from_SI("cp", cp_raw, output_units.get("cp", output_units["cp"])) if cp_raw is not None else None
        results["cv"] = from_SI("cv", cv_raw, output_units.get("cv", output_units["cv"])) if cv_raw is not None else None
        results["k"] = k_val
    except Exception:
        results["cp"], results["cv"], results["k"] = None, None, None

    # --- CORRECCIÓN ROBUSTA PARA LA CALIDAD (x) SI TENEMOS (T,P) ---
    try:
        if ("T" in (call_prop1, call_prop2)) and ("P" in (call_prop1, call_prop2)):
            # extraer T_SI y P_SI
            T_SI = call_val1_SI if call_prop1 == "T" else call_val2_SI
            P_SI = call_val1_SI if call_prop1 == "P" else call_val2_SI
            Tsat = CP.PropsSI("T", "P", P_SI, "Q", 0, fluid)  # saturación a esa P
            if np.isfinite(Tsat):
                tol = 1e-6  # tolerancia en K
                if T_SI < Tsat - tol:
                    results["x"] = 0.0
                elif T_SI > Tsat + tol:
                    results["x"] = 1.0
                else:
                    # en la frontera de saturación: calculamos calidad por entalpías
                    try:
                        h_state = CP.PropsSI("H", "T", T_SI, "P", P_SI, fluid)
                        h_l = CP.PropsSI("H", "T", T_SI, "Q", 0, fluid)
                        h_v = CP.PropsSI("H", "T", T_SI, "Q", 1, fluid)
                        if h_l is not None and h_v is not None and (h_v - h_l) != 0:
                            q_calc = (h_state - h_l) / (h_v - h_l)
                            # limitar a [0,1]
                            q_calc = max(0.0, min(1.0, float(q_calc)))
                            results["x"] = q_calc
                        else:
                            # fallback: intentar PropsSI('Q',...)
                            q_try = CP.PropsSI("Q", "T", T_SI, "P", P_SI, fluid)
                            if np.isfinite(q_try):
                                results["x"] = float(q_try)
                    except Exception:
                        # fallback final: no tocar results["x"]
                        pass
    except Exception:
        pass

    return results

# === Streamlit UI ===
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

# Unidades (sidebar)
st.sidebar.header("Configuración de unidades")
st.sidebar.subheader("Entrada")
for p in list(props.keys()) + extra_props:
    input_units[p] = st.sidebar.selectbox(f"Unidad ingreso {display_names.get(p,p)}",
                                          unit_options[p], index=unit_options[p].index(input_units.get(p, unit_options[p][0])))
st.sidebar.subheader("Salida")
for p in list(props.keys()) + extra_props:
    output_units[p] = st.sidebar.selectbox(f"Unidad salida {display_names.get(p,p)}",
                                           unit_options[p], index=unit_options[p].index(output_units.get(p, unit_options[p][0])))

# Estado referencia exergía
st.sidebar.header("Estado referencia exergía")
T_ref = st.sidebar.number_input("Temperatura referencia [°C]", value=T_ref)
P_ref = st.sidebar.number_input("Presión referencia [Pa]", value=P_ref)

# Propiedades independientes (usar text_input para permitir coma)
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

# Checkbox "dentro de la campana" solo visible si entras por T & H o T & U
dentro_campana_checkbox = False
if ("T" in (prop1, prop2)) and (("h" in (prop1, prop2)) or ("u" in (prop1, prop2))):
    dentro_campana_checkbox = st.checkbox("Dentro de la campana?", value=False)

# Caso especial T & H o T & U
if ("T" in (prop1, prop2)) and (("h" in (prop1, prop2)) or ("u" in (prop1, prop2))):
    if prop1 == "T":
        T_SI = val1
        prop_HU = prop2
        val_HU_SI = val2
    else:
        T_SI = val2
        prop_HU = prop1
        val_HU_SI = val1

    prop_for_func = "H" if prop_HU.lower() in ("h",) else "U"

    # Llamamos a la función pasándole la opción "dentro_campana"
    P_guess = P_from_T_H_or_U(T_SI, val_HU_SI, fluido_cp, prop=prop_for_func,
                              dentro_campana=dentro_campana_checkbox)
    if P_guess is not None:
        call_prop1 = "T"
        call_val1_SI = T_SI
        call_prop2 = "P"
        call_val2_SI = P_guess

# Inicializar historial
if 'historial' not in st.session_state:
    st.session_state['historial'] = []

# Zona horaria
tz = pytz.timezone("America/Argentina/Buenos_Aires")

# Botón calcular
if st.button("Calcular"):
    res = get_state(prop1, val1, prop2, val2, fluido_cp, dentro_campana_flag=dentro_campana_flag)
    st.subheader("Resultados")
    for k, v in res.items():
        if v is not None:
            unit = output_units.get(k, "")
            # k adimensional (k) -> no unidad
            st.write(f"**{display_names.get(k,k)}** = {v:.5g} {unit}")
        else:
            st.write(f"**{display_names.get(k,k)}**: No disponible")
    if len(st.session_state['historial']) >= 20:
        st.session_state['historial'].pop(0)
    st.session_state['historial'].append({
        "fecha": datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S"),
        "entrada": {prop1: val1, prop2: val2},
        "resultado": res
    })

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
                unit = output_units.get(k, "")
                st.write(f"**{display_names.get(k,k)}** = {v:.5g} {unit}")
            else:
                st.write(f"**{display_names.get(k,k)}**: No disponible")

# === Gráfico interactivo plegable ===
with st.expander("Mostrar Gráfico"):
    grafico_tipo = st.selectbox("Selecciona diagrama", ["T vs S", "P vs v"])
    fig = go.Figure()
    try:
        fluid = fluido_cp
        T_triple = CP.PropsSI('Ttriple', fluid)
        T_crit = CP.PropsSI('Tcrit', fluid)
        if (T_triple is None) or (T_crit is None) or (not np.isfinite(T_triple)) or (not np.isfinite(T_crit)):
            T_triple = 273.15 * 0.5
            T_crit = 650.0
        T_vals = np.linspace(T_triple + 0.01, T_crit - 0.01, 200)

        if grafico_tipo == "T vs S":
            S_liq = []
            S_vap = []
            T_plot = [from_SI("T", T, output_units["T"]) for T in T_vals]
            for T in T_vals:
                try:
                    S_liq.append(CP.PropsSI('S', 'T', T, 'Q', 0, fluid))
                except Exception:
                    S_liq.append(np.nan)
                try:
                    S_vap.append(CP.PropsSI('S', 'T', T, 'Q', 1, fluid))
                except Exception:
                    S_vap.append(np.nan)
            S_liq_plot = [from_SI("s", s, output_units["s"]) if (s is not None and np.isfinite(s)) else None for s in S_liq]
            S_vap_plot = [from_SI("s", s, output_units["s"]) if (s is not None and np.isfinite(s)) else None for s in S_vap]
            S_liq_x = [s for s in S_liq_plot if s is not None]
            S_liq_y = [T_plot[i] for i,s in enumerate(S_liq_plot) if s is not None]
            S_vap_x = [s for s in S_vap_plot if s is not None]
            S_vap_y = [T_plot[i] for i,s in enumerate(S_vap_plot) if s is not None]

            fig.add_trace(go.Scatter(x=S_liq_x, y=S_liq_y, mode='lines', name="Líquido saturado"))
            fig.add_trace(go.Scatter(x=S_vap_x, y=S_vap_y, mode='lines', name="Vapor saturado"))
            fig.update_layout(xaxis_title=f"S ({output_units['s']})", yaxis_title=f"T ({output_units['T']})")

            x_vals = [h["resultado"].get("s") for h in hist if h["resultado"].get("s") is not None]
            y_vals = [h["resultado"].get("T") for h in hist if h["resultado"].get("T") is not None]

        else:  # P vs v
            P_liq = []
            P_vap = []
            v_liq = []
            v_vap = []
            for T in T_vals:
                try:
                    P_liq.append(CP.PropsSI('P', 'T', T, 'Q', 0, fluid))
                except Exception:
                    P_liq.append(np.nan)
                try:
                    P_vap.append(CP.PropsSI('P', 'T', T, 'Q', 1, fluid))
                except Exception:
                    P_vap.append(np.nan)
                try:
                    d_liq = CP.PropsSI('D', 'T', T, 'Q', 0, fluid)
                    v_liq.append(1.0/d_liq if (d_liq is not None and d_liq != 0) else np.nan)
                except Exception:
                    v_liq.append(np.nan)
                try:
                    d_vap = CP.PropsSI('D', 'T', T, 'Q', 1, fluid)
                    v_vap.append(1.0/d_vap if (d_vap is not None and d_vap != 0) else np.nan)
                except Exception:
                    v_vap.append(np.nan)

            P_liq_plot = [from_SI("P", p, output_units["P"]) if (p is not None and np.isfinite(p)) else None for p in P_liq]
            P_vap_plot = [from_SI("P", p, output_units["P"]) if (p is not None and np.isfinite(p)) else None for p in P_vap]
            v_liq_plot = [from_SI("v", v, output_units["v"]) if (v is not None and np.isfinite(v)) else None for v in v_liq]
            v_vap_plot = [from_SI("v", v, output_units["v"]) if (v is not None and np.isfinite(v)) else None for v in v_vap]

            v_liq_x = [v for v in v_liq_plot if v is not None]
            P_liq_y = [P_liq_plot[i] for i,v in enumerate(v_liq_plot) if v is not None]
            v_vap_x = [v for v in v_vap_plot if v is not None]
            P_vap_y = [P_vap_plot[i] for i,v in enumerate(v_vap_plot) if v is not None]

            fig.add_trace(go.Scatter(x=v_liq_x, y=P_liq_y, mode='lines', name="Líquido saturado"))
            fig.add_trace(go.Scatter(x=v_vap_x, y=P_vap_y, mode='lines', name="Vapor saturado"))
            fig.update_layout(xaxis_title=f"v ({output_units['v']})", yaxis_title=f"P ({output_units['P']})")

            x_vals = [h["resultado"].get("v") for h in hist if h["resultado"].get("v") is not None]
            y_vals = [h["resultado"].get("P") for h in hist if h["resultado"].get("P") is not None]

        # puntos históricos y flechas
        if x_vals and y_vals and len(x_vals) == len(y_vals):
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='markers+text',
                text=[str(i) for i in range(len(x_vals))],
                textposition="top right",
                marker=dict(size=8, color='red'),
                name="Historial"
            ))
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
            # traza invisible para la leyenda 'Sentido'
            fig.add_trace(go.Scatter(
                x=[None],
                y=[None],
                mode='lines',
                line=dict(color='green', width=2),
                name="Sentido"
            ))

    except Exception as e:
        st.write("No se pudo generar la curva de saturación:", e)

    st.plotly_chart(fig, use_container_width=True)

# === Sección de contacto plegable ===
with st.expander("Contacto"):
    st.write("**Creador:** Greco Agustin")
    st.write("**Contacto:** pvt.student657@passfwd.com")
    st.markdown("###### Si encuentra algún bug, error o inconsistencia en los valores, o tiene sugerencias para mejorar la aplicación, por favor contacte al correo indicado para realizar la corrección.")


