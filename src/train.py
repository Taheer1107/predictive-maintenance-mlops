import numpy as np, mlflow, mlflow.sklearn, mlflow.xgboost
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error
from data import load_train, load_test, FEATURES

def nasa_score(y, p):
    d = p - y
    return float(np.sum(np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)))

tr, te = load_train(path=r"D:\CMAPSSData"), load_test(path=r"D:\CMAPSSData")
Xtr, ytr, Xte, yte = tr[FEATURES], tr["RUL"], te[FEATURES], te["RUL"].clip(upper=125)

models = {
    "linear": LinearRegression(),
    "random_forest": RandomForestRegressor(n_estimators=200, max_depth=12, n_jobs=-1, random_state=42),
    "xgboost": XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42),
}

mlflow.set_experiment("cmapss-fd001-rul")
for name, m in models.items():
    with mlflow.start_run(run_name=name):
        m.fit(Xtr, ytr)
        p = m.predict(Xte)
        rmse = float(np.sqrt(mean_squared_error(yte, p)))
        mlflow.log_param("model", name)
        mlflow.log_param("dataset", "FD001")
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("nasa_score", nasa_score(yte.values, p))
        if name == "xgboost":
            mlflow.xgboost.log_model(m, name="model")
        elif name == "random_forest":
            mlflow.sklearn.log_model(
                m,
                name="model",
                skops_trusted_types=["sklearn.tree._tree.Tree"],
            )
        else:
            mlflow.sklearn.log_model(m, name="model")
        print(f"{name}: RMSE={rmse:.2f}")