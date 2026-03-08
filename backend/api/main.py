"""
LLM Robustness Evaluation API — local-model edition
FastAPI + LangChain + Ollama/vLLM backend
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio, time, uuid, json

from config import get_settings
from core.pipeline import EvaluationPipeline, EvaluationConfig, report_to_dict, get_pipeline
from core.inference import get_available_models, get_router, MOCK_MODELS
from core.perturbation import PerturbationType
from core.storage import get_db

app = FastAPI(
    title="LLM Robustness Evaluation API",
    description="Local-model-first robustness framework (Ollama · vLLM · LangChain)",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

jobs: Dict[str, Dict] = {}
results_store: Dict[str, Dict] = {}


class EvaluationRequest(BaseModel):
    prompt: str
    models: List[str] = Field(default_factory=list)
    ground_truth: Optional[str] = None
    num_variants: int = Field(default=5, ge=1, le=20)
    perturbation_types: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    force_mock: bool = False
    use_langchain: bool = False
    api_key: Optional[str] = None


@app.on_event("startup")
async def startup():
    cfg = get_settings()
    router = get_router()
    print(f"\n{'='*58}")
    print(f"  LLM Robustness Eval  v2.0  (local-model edition)")
    print(f"  Backend: {cfg.inference_backend.value.upper()}")
    probe = await router.probe()
    ollama_info = "✓ " + str(probe["ollama"]["models"]) if probe["ollama"]["alive"] else "✗ not running (start: ollama serve)"
    vllm_info   = "✓ running" if probe["vllm"]["alive"] else "✗ not running"
    print(f"  Ollama  {ollama_info}")
    print(f"  vLLM    {vllm_info}")
    print(f"  OpenAI  {'✓ key set' if probe['openai']['alive'] else '✗ no key'}")
    print(f"{'='*58}\n")


@app.get("/")
async def root():
    cfg = get_settings()
    return {"name": "LLM Robustness Evaluation Framework", "version": "2.0.0",
            "inference_backend": cfg.inference_backend.value, "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time(),
            "backends": await get_router().probe()}


@app.get("/models")
async def list_models():
    models = await get_available_models()
    return {"models": models, "total": len(models)}


@app.get("/models/live")
async def live_models():
    router = get_router()
    return {"ollama": await router.ollama.list_models(),
            "vllm":   await router.vllm.list_models()}


@app.post("/models/pull")
async def pull_model(model: str):
    import httpx
    cfg = get_settings()
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            r = await client.post(f"{cfg.ollama_base_url}/api/pull",
                                  json={"name": model, "stream": False})
            return {"status": "ok", "model": model, "response": r.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/perturbation-types")
async def list_perturbation_types():
    desc = {
        PerturbationType.LEXICAL_SUBSTITUTION: "Replace words with synonyms",
        PerturbationType.PARAPHRASE:           "Restructure sentences semantically",
        PerturbationType.INSTRUCTION_INJECTION:"Prepend CoT instructions",
        PerturbationType.TOKEN_DELETION:       "Remove non-essential tokens",
        PerturbationType.COT_MANIPULATION:     "Add explicit reasoning frames",
        PerturbationType.STEP_REORDERING:      "Reorder prompt sentences",
        PerturbationType.NEGATION_INSERTION:   "Add clarifying negations",
        PerturbationType.FORMALITY_SHIFT:      "Shift formal/casual register",
    }
    return {"types": [{"id": p.value, "name": p.value.replace("_"," ").title(), "description": desc[p]} for p in PerturbationType]}


@app.post("/evaluate/sync")
async def evaluate_sync(request: EvaluationRequest):
    cfg = get_settings()
    models = request.models or cfg.ollama_model_list[:3]
    config = EvaluationConfig(
        models=models, prompt=request.prompt, ground_truth=request.ground_truth,
        num_variants=request.num_variants, perturbation_types=request.perturbation_types,
        system_prompt=request.system_prompt, force_mock=request.force_mock,
        use_langchain=request.use_langchain,
    )
    report = await get_pipeline().run(config)
    result = report_to_dict(report)
    try: get_db().save_report(result)
    except Exception as e: print(f"[DB] {e}")
    return result


@app.post("/evaluate")
async def start_evaluation(request: EvaluationRequest, background_tasks: BackgroundTasks):
    cfg = get_settings()
    job_id = str(uuid.uuid4())[:8]
    models = request.models or cfg.ollama_model_list[:3]
    jobs[job_id] = {"status": "running", "created_at": time.time(),
                    "config": {**request.dict(), "models": models}, "progress": 0}
    config = EvaluationConfig(
        models=models, prompt=request.prompt, ground_truth=request.ground_truth,
        num_variants=request.num_variants, perturbation_types=request.perturbation_types,
        system_prompt=request.system_prompt, force_mock=request.force_mock,
        use_langchain=request.use_langchain,
    )
    background_tasks.add_task(_run_evaluation, job_id, config)
    return {"job_id": job_id, "status": "running"}


@app.get("/evaluate/{job_id}")
async def get_evaluation(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = jobs[job_id]
    if job["status"] == "complete" and job_id in results_store:
        return {"status": "complete", "job_id": job_id, "result": results_store[job_id]}
    return {"status": job["status"], "job_id": job_id,
            "progress": job.get("progress", 0), "error": job.get("error")}


@app.get("/demo")
async def run_demo():
    import random
    demos = [
        {"prompt": "John has 5 apples. He buys 3 more. How many does he have?", "gt": "8"},
        {"prompt": "A train travels 60 mph for 2 hours. How far?", "gt": "120"},
        {"prompt": "All humans are mortal. Socrates is human. Is Socrates mortal?", "gt": "yes"},
    ]
    demo = random.choice(demos)
    cfg = get_settings()
    models = list(dict.fromkeys(cfg.ollama_model_list[:2] + ["mistral", "llama3"]))[:4]
    config = EvaluationConfig(models=models, prompt=demo["prompt"],
                              ground_truth=demo["gt"], num_variants=4, force_mock=True)
    report = await get_pipeline().run(config)
    return report_to_dict(report)


@app.get("/history")
async def get_history(limit: int = 20):
    return {"evaluations": get_db().list_evaluations(limit)}


@app.get("/leaderboard")
async def get_leaderboard():
    return {"leaderboard": get_db().get_model_leaderboard()}


@app.get("/jobs")
async def list_jobs():
    return {"jobs": [{"job_id": jid, "status": j["status"], "created_at": j["created_at"],
                       "prompt": j["config"]["prompt"][:60] + "…"}
                     for jid, j in sorted(jobs.items(), key=lambda x: x[1]["created_at"], reverse=True)]}


async def _run_evaluation(job_id: str, config):
    try:
        jobs[job_id]["progress"] = 20
        report = await get_pipeline().run(config)
        jobs[job_id]["progress"] = 85
        result = report_to_dict(report)
        try: get_db().save_report(result)
        except Exception: pass
        results_store[job_id] = result
        jobs[job_id].update({"status": "complete", "progress": 100})
    except Exception as e:
        jobs[job_id].update({"status": "failed", "error": str(e)})
