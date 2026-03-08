"""
Evaluation Pipeline
Orchestrates: prompt generation → inference → trace extraction → metrics
"""
import asyncio
import time
import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from core.perturbation import PerturbationEngine, PerturbationType, PromptVariant
from core.reasoning import ReasoningTraceParser, ReasoningStabilityAnalyzer, ReasoningTrace
from core.inference import InferenceRouter, InferenceResult


@dataclass
class EvaluationConfig:
    models: List[str]
    prompt: str
    ground_truth: Optional[str] = None
    num_variants: int = 5
    perturbation_types: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    force_mock: bool = False       # False = try real Ollama first
    use_langchain: bool = False    # True = use LangChain CoT chain
    api_key: Optional[str] = None


@dataclass
class VariantResult:
    variant_id: str
    perturbation_type: str
    prompt: str
    model: str
    output: str
    final_answer: Optional[str]
    reasoning_steps: List[Dict]
    latency_ms: float
    tokens_used: int
    has_cot: bool
    error: Optional[str] = None


@dataclass
class ModelEvaluationResult:
    model: str
    original_prompt: str
    variants: List[VariantResult]
    metrics: Dict[str, Any]
    evaluation_id: str
    timestamp: float


@dataclass
class EvaluationReport:
    evaluation_id: str
    config: Dict[str, Any]
    model_results: List[ModelEvaluationResult]
    cross_model_comparison: Dict[str, Any]
    timestamp: float
    duration_seconds: float


class EvaluationPipeline:
    def __init__(self):
        self.perturbation_engine = PerturbationEngine()
        self.trace_parser = ReasoningTraceParser()
        self.analyzer = ReasoningStabilityAnalyzer()
        self.inference_router = InferenceRouter()

    async def run(self, config: EvaluationConfig) -> EvaluationReport:
        start_time = time.time()
        evaluation_id = str(uuid.uuid4())[:8]

        # Step 1: Generate prompt variants
        perturbation_types = None
        if config.perturbation_types:
            perturbation_types = [PerturbationType(p) for p in config.perturbation_types]

        variants = self.perturbation_engine.generate_variants(
            prompt=config.prompt,
            perturbation_types=perturbation_types,
            num_variants=config.num_variants,
        )

        # Step 2: Run inference for each model
        model_results = []
        for model in config.models:
            result = await self._evaluate_model(
                model=model,
                original_prompt=config.prompt,
                variants=variants,
                config=config,
                evaluation_id=evaluation_id,
            )
            model_results.append(result)

        # Step 3: Cross-model comparison
        cross_model = self._compare_models(model_results)

        duration = time.time() - start_time

        return EvaluationReport(
            evaluation_id=evaluation_id,
            config={
                "models": config.models,
                "prompt": config.prompt,
                "ground_truth": config.ground_truth,
                "num_variants": config.num_variants,
            },
            model_results=model_results,
            cross_model_comparison=cross_model,
            timestamp=time.time(),
            duration_seconds=round(duration, 2),
        )

    async def _evaluate_model(
        self,
        model: str,
        original_prompt: str,
        variants: List[PromptVariant],
        config: EvaluationConfig,
        evaluation_id: str,
    ) -> ModelEvaluationResult:
        # Run original + all variants
        all_prompts = [original_prompt] + [v.perturbed for v in variants]
        all_types = ["original"] + [v.perturbation_type.value for v in variants]

        # Batch inference
        results = await self.inference_router.infer_batch(
            model=model,
            prompts=all_prompts,
            system=config.system_prompt,
            force_mock=config.force_mock,
            use_langchain=config.use_langchain,
        )

        # Parse traces
        traces: List[ReasoningTrace] = []
        variant_results: List[VariantResult] = []

        for i, (result, ptype) in enumerate(zip(results, all_types)):
            trace = self.trace_parser.parse(result.output)
            traces.append(trace)

            variant_results.append(VariantResult(
                variant_id=f"{evaluation_id}-{model}-{i}",
                perturbation_type=ptype,
                prompt=result.prompt,
                model=model,
                output=result.output,
                final_answer=trace.final_answer,
                reasoning_steps=[
                    {"index": s.index, "content": s.content, "type": s.step_type}
                    for s in trace.steps
                ],
                latency_ms=result.latency_ms,
                tokens_used=result.tokens_used,
                has_cot=trace.has_cot,
                error=result.error,
            ))

        # Compute metrics
        metrics = self.analyzer.analyze_traces(traces, config.ground_truth)

        return ModelEvaluationResult(
            model=model,
            original_prompt=original_prompt,
            variants=variant_results,
            metrics=metrics,
            evaluation_id=evaluation_id,
            timestamp=time.time(),
        )

    def _compare_models(self, model_results: List[ModelEvaluationResult]) -> Dict[str, Any]:
        if not model_results:
            return {}

        comparison = {
            "rankings": {},
            "best_model": None,
            "worst_model": None,
            "metric_comparison": {},
        }

        metric_keys = ["robustness_score", "answer_stability", "hallucination_rate", "reasoning_drift"]

        for key in metric_keys:
            values = {r.model: r.metrics.get(key, 0) for r in model_results}
            comparison["metric_comparison"][key] = values

        # Rank by robustness score
        scores = {r.model: r.metrics.get("robustness_score", 0) for r in model_results}
        sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        comparison["rankings"] = {model: rank + 1 for rank, (model, _) in enumerate(sorted_models)}
        comparison["best_model"] = sorted_models[0][0] if sorted_models else None
        comparison["worst_model"] = sorted_models[-1][0] if sorted_models else None

        return comparison


def report_to_dict(report: EvaluationReport) -> Dict[str, Any]:
    """Convert report to JSON-serializable dict."""
    return {
        "evaluation_id": report.evaluation_id,
        "config": report.config,
        "timestamp": report.timestamp,
        "duration_seconds": report.duration_seconds,
        "cross_model_comparison": report.cross_model_comparison,
        "model_results": [
            {
                "model": r.model,
                "metrics": r.metrics,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "perturbation_type": v.perturbation_type,
                        "prompt": v.prompt,
                        "output": v.output,
                        "final_answer": v.final_answer,
                        "reasoning_steps": v.reasoning_steps,
                        "latency_ms": v.latency_ms,
                        "tokens_used": v.tokens_used,
                        "has_cot": v.has_cot,
                        "error": v.error,
                    }
                    for v in r.variants
                ],
            }
            for r in report.model_results
        ],
    }


# Singleton
_pipeline = EvaluationPipeline()


def get_pipeline() -> EvaluationPipeline:
    return _pipeline
