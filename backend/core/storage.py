"""
DuckDB persistence layer.
Stores evaluation runs, variant results, and metrics for history/comparison.
"""
import duckdb
import json
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from config import get_settings


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id   VARCHAR PRIMARY KEY,
    prompt          TEXT,
    ground_truth    VARCHAR,
    models          VARCHAR,       -- JSON array
    num_variants    INTEGER,
    timestamp       DOUBLE,
    duration_s      DOUBLE,
    config          TEXT           -- full config JSON
);

CREATE TABLE IF NOT EXISTS model_results (
    id              VARCHAR PRIMARY KEY,
    evaluation_id   VARCHAR,
    model           VARCHAR,
    provider        VARCHAR,
    robustness_score    DOUBLE,
    answer_stability    DOUBLE,
    hallucination_rate  DOUBLE,
    reasoning_drift     DOUBLE,
    semantic_consistency DOUBLE,
    total_traces    INTEGER,
    timestamp       DOUBLE
);

CREATE TABLE IF NOT EXISTS variant_results (
    variant_id          VARCHAR PRIMARY KEY,
    evaluation_id       VARCHAR,
    model               VARCHAR,
    perturbation_type   VARCHAR,
    prompt              TEXT,
    output              TEXT,
    final_answer        VARCHAR,
    reasoning_steps     TEXT,   -- JSON
    latency_ms          DOUBLE,
    tokens_used         INTEGER,
    has_cot             BOOLEAN,
    error               VARCHAR
);
"""


class ResultsDB:
    """Thin DuckDB wrapper for evaluation persistence."""

    def __init__(self, db_path: Optional[str] = None):
        cfg = get_settings()
        path = db_path or cfg.db_path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(path)
        self.conn.execute(_CREATE_SQL)

    def save_report(self, report: Dict[str, Any]) -> None:
        """Persist a full evaluation report dict."""
        eid = report["evaluation_id"]
        cfg = report.get("config", {})

        # evaluations table
        self.conn.execute(
            """INSERT OR REPLACE INTO evaluations
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                eid,
                cfg.get("prompt", ""),
                cfg.get("ground_truth"),
                json.dumps(cfg.get("models", [])),
                cfg.get("num_variants", 0),
                report.get("timestamp", time.time()),
                report.get("duration_seconds", 0),
                json.dumps(cfg),
            ],
        )

        for mr in report.get("model_results", []):
            model = mr["model"]
            metrics = mr.get("metrics", {})
            self.conn.execute(
                """INSERT OR REPLACE INTO model_results VALUES
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    f"{eid}-{model}",
                    eid, model,
                    "ollama" if not model.startswith(("gpt", "claude")) else model.split("-")[0],
                    metrics.get("robustness_score", 0),
                    metrics.get("answer_stability", 0),
                    metrics.get("hallucination_rate", 0),
                    metrics.get("reasoning_drift", 0),
                    metrics.get("semantic_consistency", 0),
                    metrics.get("total_traces", 0),
                    time.time(),
                ],
            )

            for v in mr.get("variants", []):
                self.conn.execute(
                    """INSERT OR REPLACE INTO variant_results VALUES
                       (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [
                        v.get("variant_id", f"{eid}-{model}-?"),
                        eid, model,
                        v.get("perturbation_type", "unknown"),
                        v.get("prompt", ""),
                        v.get("output", ""),
                        v.get("final_answer"),
                        json.dumps(v.get("reasoning_steps", [])),
                        v.get("latency_ms", 0),
                        v.get("tokens_used", 0),
                        v.get("has_cot", False),
                        v.get("error"),
                    ],
                )

    def list_evaluations(self, limit: int = 50) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT evaluation_id, prompt, models, timestamp, duration_s "
            "FROM evaluations ORDER BY timestamp DESC LIMIT ?",
            [limit],
        ).fetchall()
        return [
            {
                "evaluation_id": r[0],
                "prompt": r[1][:80] + ("…" if len(r[1]) > 80 else ""),
                "models": json.loads(r[2]),
                "timestamp": r[3],
                "duration_s": r[4],
            }
            for r in rows
        ]

    def get_model_leaderboard(self) -> List[Dict]:
        """Average metrics per model across all evaluations."""
        rows = self.conn.execute(
            """SELECT model,
                      AVG(robustness_score)     AS avg_robustness,
                      AVG(answer_stability)     AS avg_stability,
                      AVG(hallucination_rate)   AS avg_hallucination,
                      AVG(reasoning_drift)      AS avg_drift,
                      COUNT(*)                  AS eval_count
               FROM model_results
               GROUP BY model
               ORDER BY avg_robustness DESC"""
        ).fetchall()
        return [
            {
                "model": r[0],
                "avg_robustness": round(r[1], 4),
                "avg_stability": round(r[2], 4),
                "avg_hallucination": round(r[3], 4),
                "avg_drift": round(r[4], 4),
                "eval_count": r[5],
            }
            for r in rows
        ]

    def get_evaluation(self, evaluation_id: str) -> Optional[Dict]:
        row = self.conn.execute(
            "SELECT config FROM evaluations WHERE evaluation_id = ?",
            [evaluation_id],
        ).fetchone()
        return json.loads(row[0]) if row else None

    def close(self):
        self.conn.close()


# Singleton
_db: Optional[ResultsDB] = None


def get_db() -> ResultsDB:
    global _db
    if _db is None:
        _db = ResultsDB()
    return _db
