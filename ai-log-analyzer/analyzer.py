import requests
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# إعدادات الاتصال بـ Loki (الـ service name اللي شفناه بالكلستر)
LOKI_URL = "http://loki.monitoring.svc.cluster.local:3100"
QUERY = '{namespace="default"}'
POLL_INTERVAL_SECONDS = 30


def fetch_logs_from_loki(minutes_back=1):
    """
    بيسحب آخر logs من Loki بين وقت معين ودلوقتي.
    بيرجع list من الـ log lines (نصوص خام).
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=minutes_back)

    params = {
        "query": QUERY,
        "start": int(start_time.timestamp() * 1e9),  # Loki بياخد nanoseconds
        "end": int(end_time.timestamp() * 1e9),
        "limit": 1000,
    }

    try:
        response = requests.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to query Loki: {e}")
        return []

    log_lines = []
    for result in data.get("data", {}).get("result", []):
        for entry in result.get("values", []):
            # كل entry هو [timestamp_ns, log_line]
            log_lines.append(entry[1])

    return log_lines


def extract_features(log_lines):
    """
    بياخد قايمة من الـ log lines الخام (نصوص)،
    وبيطلع منها أرقام (features) تمثل حالة الـ traffic في الفترة دي.
    """
    total_requests = len(log_lines)
    status_2xx = 0
    status_4xx = 0
    status_5xx = 0

    for line in log_lines:
        # بنفتش عن status code جوه السطر، زي:
        # 10.244.0.21 - - [22/Aug/2026 ...] "GET /metrics HTTP/1.1" 200 -
        if '" 2' in line:
            status_2xx += 1
        elif '" 4' in line:
            status_4xx += 1
        elif '" 5' in line:
            status_5xx += 1

    error_rate = (status_4xx + status_5xx) / total_requests if total_requests > 0 else 0

    return {
        "total_requests": total_requests,
        "status_2xx": status_2xx,
        "status_4xx": status_4xx,
        "status_5xx": status_5xx,
        "error_rate": error_rate,
    }


from prometheus_client import Gauge, start_http_server

# ---- Prometheus metric: هيظهر في /metrics عشان Prometheus يعمله scrape ----
anomaly_score_gauge = Gauge(
    "hivebox_log_anomaly_score",
    "Anomaly score computed from recent log patterns (lower = more anomalous)"
)
total_requests_gauge = Gauge(
    "hivebox_log_total_requests",
    "Total requests observed in the last polling window"
)
error_rate_gauge = Gauge(
    "hivebox_log_error_rate",
    "Error rate (4xx + 5xx) observed in the last polling window"
)


def run():
    """
    الحلقة الرئيسية: بتشتغل من غير توقف طول عمر الـ pod.
    كل POLL_INTERVAL_SECONDS، بتسحب logs، تحسب features، تحسب anomaly score،
    وتحدّث الـ Prometheus metrics.
    """
    logger.info("Starting ai-log-analyzer service")

    load_history_from_minio()

    start_http_server(8000)
    logger.info("Metrics server started on port 8000")

    while True:
        try:
            log_lines = fetch_logs_from_loki(minutes_back=1)
            features = extract_features(log_lines)
            score = compute_anomaly_score(features)

            anomaly_score_gauge.set(score)
            total_requests_gauge.set(features["total_requests"])
            error_rate_gauge.set(features["error_rate"])

            logger.info(
                f"requests={features['total_requests']} "
                f"error_rate={features['error_rate']:.2f} "
                f"anomaly_score={score:.4f}"
            )

        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)



import os
import json
import numpy as np
from sklearn.ensemble import IsolationForest
from collections import deque
from minio import Minio
from minio.error import S3Error
from io import BytesIO

MINIO_HOST = os.getenv("MINIO_ENDPOINT", "minio.default.svc.cluster.local:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio_strong_password")
HISTORY_BUCKET = os.getenv("HISTORY_BUCKET", "anomaly-history")
HISTORY_OBJECT_NAME = "feature_history.json"

minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

FEATURE_HISTORY = deque(maxlen=50)
MIN_SAMPLES_TO_TRAIN = 10
SAVE_EVERY_N_READINGS = 10
_readings_since_last_save = 0


def load_history_from_minio():
    try:
        if not minio_client.bucket_exists(HISTORY_BUCKET):
            minio_client.make_bucket(HISTORY_BUCKET)
            logger.info(f"Created MinIO bucket: {HISTORY_BUCKET}")
            return

        response = minio_client.get_object(HISTORY_BUCKET, HISTORY_OBJECT_NAME)
        data = json.loads(response.read())
        response.close()
        response.release_conn()

        for row in data:
            FEATURE_HISTORY.append(row)

        logger.info(f"Loaded {len(FEATURE_HISTORY)} historical readings from MinIO")

    except S3Error as e:
        logger.info(f"No previous history found in MinIO ({e.code}), starting fresh")


def save_history_to_minio():
    try:
        data = json.dumps(list(FEATURE_HISTORY)).encode("utf-8")
        data_stream = BytesIO(data)

        minio_client.put_object(
            HISTORY_BUCKET,
            HISTORY_OBJECT_NAME,
            data_stream,
            length=len(data),
            content_type="application/json"
        )
        logger.info(f"Saved {len(FEATURE_HISTORY)} readings to MinIO")

    except S3Error as e:
        logger.error(f"Failed to save history to MinIO: {e}")


def compute_anomaly_score(features):
    global _readings_since_last_save

    feature_vector = [
        features["total_requests"],
        features["status_2xx"],
        features["status_4xx"],
        features["status_5xx"],
        features["error_rate"],
    ]

    FEATURE_HISTORY.append(feature_vector)
    _readings_since_last_save += 1

    if _readings_since_last_save >= SAVE_EVERY_N_READINGS:
        save_history_to_minio()
        _readings_since_last_save = 0

    if len(FEATURE_HISTORY) < MIN_SAMPLES_TO_TRAIN:
        logger.info(f"Not enough history yet ({len(FEATURE_HISTORY)}/{MIN_SAMPLES_TO_TRAIN}), skipping scoring")
        return 0.0

    X = np.array(FEATURE_HISTORY)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)

    latest_score = model.decision_function([feature_vector])[0]
    return float(latest_score)


if __name__ == "__main__":
    run()
