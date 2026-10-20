import json, os, time
import numpy as np, pandas as pd, mlflow.pyfunc
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
from src.data import SENSORS, FEATURES

MODEL_PATH = os.getenv(r"D:\CMAPSSData\scaler.pkl", "model/model")
LOG_PATH = os.getenv("LOG_PATH", "logs/requests.jsonl")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

model = mlflow.pyfunc.load_model(MODEL_PATH)
app = FastAPI(title="Predictive Maintenance API")

class Reading(BaseModel):
    s2: float; s3: float; s4: float; s7: float; s8: float; s9: float; s11: float
    s12: float; s13: float; s14: float; s15: float; s17: float; s20: float; s21: float

class PredictRequest(BaseModel):
    engine_id: str
    readings: List[Reading] = Field(..., min_length=1)   # recent cycles, oldest to newest

def status_from_rul(rul: float) -> str:
    return "critical" if rul < 30 else "warning" if rul < 60 else "healthy"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    df = pd.DataFrame([r.model_dump() for r in req.readings])[SENSORS].tail(5)
    row = df.iloc[-1].to_dict()                                   # latest reading
    row.update({f"{s}_rm": df[s].mean() for s in SENSORS})        # rolling mean, same as training
    X = pd.DataFrame([row])[FEATURES]
    rul = float(np.clip(model.predict(X)[0], 0, 125))

    with open(LOG_PATH, "a") as f:                                # saved for drift monitoring later
        f.write(json.dumps({"ts": time.time(), "engine_id": req.engine_id,
                            **row, "predicted_rul": rul}) + "\n")

    return {"engine_id": req.engine_id, "predicted_rul": round(rul, 1),
            "status": status_from_rul(rul)}