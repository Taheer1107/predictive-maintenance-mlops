import pandas as pd

COLS = ["unit", "cycle"] + [f"op{i}" for i in range(1, 4)] + [f"s{i}" for i in range(1, 22)]
DROP = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]   # constant in FD001
SENSORS = [f"s{i}" for i in range(1, 22) if f"s{i}" not in DROP]
FEATURES = SENSORS + [f"{s}_rm" for s in SENSORS]

def _add_rolling(df, w=5):
    roll = (df.groupby("unit")[SENSORS].rolling(w, min_periods=1).mean()
              .reset_index(level=0, drop=True).add_suffix("_rm"))
    return df.join(roll)

def load_train(fd="FD001", path="data/raw"):
    df = pd.read_csv(f"{path}/train_{fd}.txt", sep=r"\s+", header=None, names=COLS)
    df["RUL"] = (df.groupby("unit")["cycle"].transform("max") - df["cycle"]).clip(upper=125)
    return _add_rolling(df)




def load_test(fd="FD001", path="data/raw"):
    df = pd.read_csv(f"{path}/test_{fd}.txt", sep=r"\s+", header=None, names=COLS)
    df = _add_rolling(df)
    last = df.groupby("unit").tail(1).reset_index(drop=True)   # last row per engine
    last["RUL"] = pd.read_csv(f"{path}/RUL_{fd}.txt", header=None)[0].values
    return last


def load_train_multi(fds, path="data/raw"):
    parts, offset = [], 0
    for fd in fds:
        d = load_train(fd, path)
        d["unit"] += offset            # engine IDs repeat in every subset, so shift them
        offset = d["unit"].max()
        parts.append(d)
    return pd.concat(parts, ignore_index=True)