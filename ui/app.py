import os

import requests, pandas as pd, streamlit as st
import plotly.graph_objects as go
api = st.sidebar.text_input("API URL", os.getenv("API_URL", "http://127.0.0.1:8000"))

st.set_page_config(page_title="Predictive Maintenance", layout="wide")

COLS = ["unit", "cycle"] + [f"op{i}" for i in range(1, 4)] + [f"s{i}" for i in range(1, 22)]
SENSORS = ["s2", "s3", "s4", "s7", "s8", "s9", "s11", "s12", "s13", "s14", "s15", "s17", "s20", "s21"]

api = st.sidebar.text_input("API URL", "http://127.0.0.1:8000")
st.sidebar.caption("Dataset: NASA C-MAPSS FD001 (test set)")

@st.cache_data
def load_data():
    df = pd.read_csv("data/raw/test_FD001.txt", sep=r"\s+", header=None, names=COLS)
    true = pd.read_csv("data/raw/RUL_FD001.txt", header=None)[0]
    return df, true

def predict(api, engine_id, readings):
    r = requests.post(f"{api}/predict", json={"engine_id": engine_id, "readings": readings}, timeout=10)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner="Scoring the fleet...")
def score_fleet(api):
    df, true = load_data()
    rows = []
    for unit, g in df.groupby("unit"):
        res = predict(api, f"engine_{unit}", g.tail(5)[SENSORS].to_dict("records"))
        rows.append({"engine": unit, "cycles_run": int(g.cycle.max()),
                     "predicted_rul": res["predicted_rul"],
                     "true_rul": min(int(true[unit - 1]), 125),
                     "status": res["status"]})
    return pd.DataFrame(rows).sort_values("predicted_rul").reset_index(drop=True)

@st.cache_data(show_spinner="Replaying engine history...")
def predict_history(api, unit):
    df, _ = load_data()
    g = df[df.unit == unit].reset_index(drop=True)
    return [predict(api, f"engine_{unit}", g.iloc[max(0, i - 4):i + 1][SENSORS].to_dict("records"))["predicted_rul"]
            for i in range(len(g))]

st.title("Predictive Maintenance Platform")
try:
    requests.get(f"{api}/health", timeout=3).raise_for_status()
except Exception:
    st.error("API not reachable. Start it with: uvicorn src.app:app")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Fleet overview", "Engine detail", "How it works"])

with tab1:
    fleet = score_fleet(api)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Engines", len(fleet))
    c2.metric("Critical (<30 cycles)", int((fleet.status == "critical").sum()))
    c3.metric("Warning (30-60)", int((fleet.status == "warning").sum()))
    c4.metric("Healthy (60+)", int((fleet.status == "healthy").sum()))
    colors = {"critical": "background-color:#f8b4b4", "warning": "background-color:#fde3a7",
              "healthy": "background-color:#bfe8c8"}
    st.dataframe(fleet.style.map(lambda v: colors.get(v, ""), subset=["status"]),
                 use_container_width=True, height=450)
    st.caption("Sorted by lowest predicted RUL: maintenance priority list. true_rul is capped at 125.")

with tab2:
    df, true = load_data()
    unit = st.selectbox("Engine", sorted(df.unit.unique()))
    g = df[df.unit == unit].reset_index(drop=True)
    n = len(g)
    cycle = st.slider("Replay engine up to cycle", 1, n, n)
    sub = g[g.cycle <= cycle]

    res = predict(api, f"engine_{unit}", sub.tail(5)[SENSORS].to_dict("records"))
    left, right = st.columns([1, 2])

    with left:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=res["predicted_rul"],
            title={"text": f"Predicted RUL ({res['status']})"},
            gauge={"axis": {"range": [0, 125]},
                   "steps": [{"range": [0, 30], "color": "#f8b4b4"},
                             {"range": [30, 60], "color": "#fde3a7"},
                             {"range": [60, 125], "color": "#bfe8c8"}],
                   "bar": {"color": "#333"}}))
        fig.update_layout(height=300, margin=dict(t=60, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        hist = predict_history(api, unit)
        true_final = min(int(true[unit - 1]), 125)
        true_curve = [min(int(true[unit - 1]) + (n - c), 125) for c in range(1, n + 1)]
        fig2 = go.Figure()
        fig2.add_scatter(x=list(range(1, cycle + 1)), y=hist[:cycle], name="Predicted RUL")
        fig2.add_scatter(x=list(range(1, cycle + 1)), y=true_curve[:cycle], name="True RUL", line=dict(dash="dash"))
        fig2.update_layout(height=300, margin=dict(t=30, b=0), xaxis_title="cycle", yaxis_title="RUL")
        st.plotly_chart(fig2, use_container_width=True)

    sel = st.multiselect("Sensors", SENSORS, default=["s2", "s7", "s11"])
    if sel:
        norm = (g[sel] - g[sel].min()) / (g[sel].max() - g[sel].min() + 1e-9)   # 0-1 scale so sensors are comparable
        st.line_chart(norm[g.cycle <= cycle].set_axis(sub.cycle, axis=0))
        st.caption("Each sensor scaled to 0-1 over the engine's life. Watch how they drift as the engine wears out.")

with tab3:
    st.markdown("""
**Pipeline:** NASA sensor data → features (last reading + 5-cycle rolling mean) → XGBoost model → FastAPI `/predict` → this dashboard.

- **RUL** = remaining useful life: cycles left before the engine fails (capped at 125).
- **Status:** critical below 30, warning below 60, otherwise healthy.
- The test engines stop *before* failure; the true RUL comes from NASA's `RUL_FD001.txt`.
- Use the replay slider to watch the prediction converge toward the true RUL as the engine ages.
""")