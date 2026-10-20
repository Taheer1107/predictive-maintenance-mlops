import mlflow, shutil, os
from mlflow.tracking import MlflowClient

client = MlflowClient()
exp = client.get_experiment_by_name("cmapss-fd001-rul")
best = client.search_runs([exp.experiment_id], order_by=["metrics.rmse ASC"], max_results=1)[0]
print("Best run:", best.data.params["model"], "RMSE:", best.data.metrics["rmse"])

shutil.rmtree("model", ignore_errors=True)
os.makedirs("model")
mlflow.artifacts.download_artifacts(run_id=best.info.run_id, artifact_path="model", dst_path="model")
if best.data.params["model"] == "lstm":
    mlflow.artifacts.download_artifacts(run_id=best.info.run_id, artifact_path="scaler.pkl", dst_path="model")