import requests, pandas as pd
from src.data import COLS, SENSORS

df = pd.read_csv("data/raw/test_FD001.txt", sep=r"\s+", header=None, names=COLS)
true = pd.read_csv("data/raw/RUL_FD001.txt", header=None)[0]

for unit in [1, 2, 3]:
    last5 = df[df.unit == unit].tail(5)[SENSORS].to_dict(orient="records")
    r = requests.post("http://127.0.0.1:8000/predict",
                      json={"engine_id": f"engine_{unit}", "readings": last5}).json()
    print(r, "| true RUL:", true[unit - 1])