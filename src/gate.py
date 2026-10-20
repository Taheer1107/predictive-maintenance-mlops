import sys
from mlflow.tracking import MlflowClient

THRESHOLD = 20.0
c = MlflowClient()
exp = c.get_experiment_by_name("cmapss-fd001-rul")
best = c.search_runs([exp.experiment_id], order_by=["metrics.rmse ASC"], max_results=1)[0]
rmse = best.data.metrics["rmse"]
print(f"Best model: {best.data.params['model']} | RMSE {rmse:.2f} | threshold {THRESHOLD}")
sys.exit(0 if rmse <= THRESHOLD else 1)