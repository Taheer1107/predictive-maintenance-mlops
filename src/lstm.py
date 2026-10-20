import numpy as np, torch, torch.nn as nn, mlflow, mlflow.pytorch, joblib
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from data import load_train, SENSORS, COLS
import pandas as pd
import warnings
warnings.filterwarnings("ignore", message="The given buffer is not writable")

W = 30
DATA_PATH = Path(__file__).resolve().parent
torch.manual_seed(42); np.random.seed(42)

tr = load_train(path=DATA_PATH)
scaler = MinMaxScaler().fit(tr[SENSORS])
tr[SENSORS] = scaler.transform(tr[SENSORS])

def train_windows(df):
    X, y = [], []
    for _, g in df.groupby("unit"):
        a, r = g[SENSORS].values, g["RUL"].values
        for i in range(len(a) - W + 1):
            X.append(a[i:i + W]); y.append(r[i + W - 1])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

def test_windows(fd="FD001", path=DATA_PATH):
    df = pd.read_csv(f"{path}/test_{fd}.txt", sep=r"\s+", header=None, names=COLS)
    df[SENSORS] = scaler.transform(df[SENSORS])
    X = []
    for _, g in df.groupby("unit"):
        a = g[SENSORS].values[-W:]
        if len(a) < W:                                   # pad short engines
            a = np.vstack([np.repeat(a[:1], W - len(a), 0), a])
        X.append(a)
    y = pd.read_csv(f"{path}/RUL_{fd}.txt", header=None)[0].clip(upper=125).values
    return np.array(X, dtype=np.float32), y.astype(np.float32)

class RULNet(nn.Module):
    def __init__(self, n_in, h=64):
        super().__init__()
        self.lstm = nn.LSTM(n_in, h, num_layers=2, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(nn.Linear(h, 32), nn.ReLU(), nn.Linear(32, 1))
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1]).squeeze(-1)

Xtr, ytr = train_windows(tr)
Xte, yte = test_windows()
Xtr_t, ytr_t, Xte_t = map(torch.tensor, (Xtr, ytr, Xte))

EPOCHS, LR, BS = 30, 1e-3, 256
model = RULNet(len(SENSORS))
opt = torch.optim.Adam(model.parameters(), lr=LR)
loss_fn = nn.MSELoss()

mlflow.set_experiment("cmapss-fd001-rul")
with mlflow.start_run(run_name="lstm"):
    mlflow.log_params({"model": "lstm", "dataset": "FD001", "window": W,
                       "epochs": EPOCHS, "lr": LR, "batch_size": BS})
    for ep in range(EPOCHS):
        model.train()
        perm = torch.randperm(len(Xtr_t))
        for i in range(0, len(perm), BS):
            idx = perm[i:i + BS]
            opt.zero_grad()
            loss = loss_fn(model(Xtr_t[idx]), ytr_t[idx])
            loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            rmse = float(np.sqrt(np.mean((model(Xte_t).numpy() - yte) ** 2)))
        mlflow.log_metric("rmse", rmse, step=ep)
        print(f"epoch {ep+1}: test RMSE={rmse:.2f}")
    joblib.dump(scaler, "scaler.pkl")
    mlflow.log_artifact("scaler.pkl")                    # needed later by the API
    mlflow.pytorch.log_model(
        model,
        name="model",
        serialization_format="pt2",
        input_example=Xte[:2],
    )