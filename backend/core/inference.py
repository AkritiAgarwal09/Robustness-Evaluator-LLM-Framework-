"""
Multi-Model Inference Layer — Local-Model First
Supports: Ollama · vLLM · LangChain · OpenAI (fallback) · Mock (demo)

Priority order:  Ollama  →  vLLM  →  OpenAI  →  Mock
"""
import asyncio
import time
import random
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx
import os

from config import get_settings, InferenceBackend


# ─── Result type ──────────────────────────────────────────────────────────────

class ModelProvider(str, Enum):
    OLLAMA = "ollama"
    VLLM = "vllm"
    LANGCHAIN = "langchain"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class InferenceResult:
    model: str
    prompt: str
    output: str
    latency_ms: float
    tokens_used: int
    provider: ModelProvider
    error: Optional[str] = None


# ─── Model profiles (mock + display metadata) ─────────────────────────────────

_LOCAL_MOCK_PROFILES: Dict[str, Dict] = {
    "llama3":       {"stability": 0.82, "hallucination": 0.10, "speed_ms": 900,  "provider": "ollama"},
    "llama3:70b":   {"stability": 0.88, "hallucination": 0.07, "speed_ms": 2200, "provider": "ollama"},
    "llama3:8b":    {"stability": 0.80, "hallucination": 0.11, "speed_ms": 750,  "provider": "ollama"},
    "mistral":      {"stability": 0.80, "hallucination": 0.12, "speed_ms": 700,  "provider": "ollama"},
    "mistral:7b":   {"stability": 0.78, "hallucination": 0.14, "speed_ms": 650,  "provider": "ollama"},
    "codellama":    {"stability": 0.76, "hallucination": 0.15, "speed_ms": 800,  "provider": "ollama"},
    "phi3":         {"stability": 0.74, "hallucination": 0.16, "speed_ms": 500,  "provider": "ollama"},
    "gemma2":       {"stability": 0.81, "hallucination": 0.11, "speed_ms": 750,  "provider": "ollama"},
    "qwen2":        {"stability": 0.79, "hallucination": 0.13, "speed_ms": 720,  "provider": "ollama"},
}

_CLOUD_MOCK_PROFILES: Dict[str, Dict] = {
    "gpt-4o":          {"stability": 0.92, "hallucination": 0.05, "speed_ms": 1200, "provider": "openai"},
    "gpt-3.5-turbo":   {"stability": 0.78, "hallucination": 0.14, "speed_ms": 400,  "provider": "openai"},
    "claude-3-opus":   {"stability": 0.94, "hallucination": 0.03, "speed_ms": 1500, "provider": "anthropic"},
    "claude-3-sonnet": {"stability": 0.88, "hallucination": 0.07, "speed_ms": 800,  "provider": "anthropic"},
}

MOCK_MODELS = {**_LOCAL_MOCK_PROFILES, **_CLOUD_MOCK_PROFILES}

MOCK_REASONING_TEMPLATES = [
    """Let me solve this step by step.

Step 1: Read the problem carefully.
{context}

Step 2: Identify what we need to find.
We need to {operation}.

Step 3: Calculate.
{calc}

Step 4: Verify.
The answer is {answer}.""",

    """I'll work through this carefully.

First: {context}
Then: {operation}
Computing: {calc}
Therefore the answer is {answer}.""",

    """Reasoning step by step:
- Given: {context}
- Operation: {operation}
- Result: {calc}
- Answer: {answer}""",
]


# ─── Ollama engine ────────────────────────────────────────────────────────────

class OllamaEngine:
    """Calls a local Ollama server via REST API."""

    def __init__(self):
        cfg = get_settings()
        self.base_url = cfg.ollama_base_url.rstrip("/")
        self.max_tokens = cfg.default_max_tokens
        self.temperature = cfg.default_temperature

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> InferenceResult:
        """Use /api/chat (instruct models) with /api/generate fallback."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{self.base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                latency = (time.time() - start) * 1000
                output = data.get("message", {}).get("content", "")
                tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                return InferenceResult(
                    model=model, prompt=prompt, output=output,
                    latency_ms=latency, tokens_used=tokens,
                    provider=ModelProvider.OLLAMA,
                )
        except Exception as e:
            # Fallback: raw generate
            try:
                gen_payload = {
                    "model": model, "prompt": prompt, "stream": False,
                    "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
                }
                if system:
                    gen_payload["system"] = system
                async with httpx.AsyncClient(timeout=120.0) as client:
                    r = await client.post(f"{self.base_url}/api/generate", json=gen_payload)
                    r.raise_for_status()
                    data = r.json()
                    latency = (time.time() - start) * 1000
                    return InferenceResult(
                        model=model, prompt=prompt,
                        output=data.get("response", ""),
                        latency_ms=latency,
                        tokens_used=data.get("eval_count", 0),
                        provider=ModelProvider.OLLAMA,
                    )
            except Exception as e2:
                return InferenceResult(
                    model=model, prompt=prompt, output="",
                    latency_ms=0, tokens_used=0,
                    provider=ModelProvider.OLLAMA, error=str(e2),
                )


# ─── vLLM engine ─────────────────────────────────────────────────────────────

class VLLMEngine:
    """
    Calls a local vLLM server (OpenAI-compatible API).
    Start: python -m vllm.entrypoints.openai.api_server \\
               --model meta-llama/Meta-Llama-3-8B-Instruct --port 8001
    """

    def __init__(self):
        cfg = get_settings()
        self.base_url = cfg.vllm_base_url.rstrip("/")
        self.max_tokens = cfg.default_max_tokens
        self.temperature = cfg.default_temperature

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.base_url}/v1/models")
                data = r.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> InferenceResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model, "messages": messages,
            "max_tokens": self.max_tokens, "temperature": self.temperature,
        }
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{self.base_url}/v1/chat/completions", json=payload)
                r.raise_for_status()
                data = r.json()
                latency = (time.time() - start) * 1000
                output = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return InferenceResult(
                    model=model, prompt=prompt, output=output,
                    latency_ms=latency, tokens_used=tokens,
                    provider=ModelProvider.VLLM,
                )
        except Exception as e:
            return InferenceResult(
                model=model, prompt=prompt, output="",
                latency_ms=0, tokens_used=0,
                provider=ModelProvider.VLLM, error=str(e),
            )


# ─── LangChain wrapper ────────────────────────────────────────────────────────

class LangChainOllamaEngine:
    """
    Uses langchain-ollama for structured CoT chain prompting.
    Preferred when you want PromptTemplate / OutputParser pipelines.
    """

    def __init__(self):
        cfg = get_settings()
        self.base_url = cfg.ollama_base_url
        self.max_tokens = cfg.default_max_tokens
        self.temperature = cfg.default_temperature

    def _build_llm(self, model: str):
        try:
            from langchain_ollama import OllamaLLM
            return OllamaLLM(
                model=model, base_url=self.base_url,
                temperature=self.temperature, num_predict=self.max_tokens,
            )
        except ImportError:
            from langchain_community.llms import Ollama
            return Ollama(
                model=model, base_url=self.base_url,
                temperature=self.temperature, num_predict=self.max_tokens,
            )

    async def generate(
        self, model: str, prompt: str, system: Optional[str] = None,
        use_cot_chain: bool = True,
    ) -> InferenceResult:
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        try:
            llm = self._build_llm(model)
            if use_cot_chain:
                template = PromptTemplate.from_template(
                    "{sys}Think step by step to solve the following:\n\n{input}\n\nStep-by-step reasoning:"
                )
                chain = template | llm | StrOutputParser()
                sys_str = f"[System: {system}]\n\n" if system else ""
                start = time.time()
                output = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: chain.invoke({"sys": sys_str, "input": prompt})
                )
            else:
                full = f"{system}\n\n{prompt}" if system else prompt
                start = time.time()
                output = await asyncio.get_event_loop().run_in_executor(None, lambda: llm.invoke(full))
            latency = (time.time() - start) * 1000
            return InferenceResult(
                model=model, prompt=prompt, output=str(output),
                latency_ms=latency, tokens_used=len(str(output).split()),
                provider=ModelProvider.LANGCHAIN,
            )
        except Exception as e:
            return InferenceResult(
                model=model, prompt=prompt, output="",
                latency_ms=0, tokens_used=0,
                provider=ModelProvider.LANGCHAIN, error=str(e),
            )


# ─── OpenAI (cloud fallback) ──────────────────────────────────────────────────

class OpenAIEngine:
    def __init__(self):
        self.api_key = get_settings().openai_api_key or os.getenv("OPENAI_API_KEY")

    async def generate(self, model: str, prompt: str, system: Optional[str] = None) -> InferenceResult:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)
            messages = ([{"role": "system", "content": system}] if system else [])
            messages.append({"role": "user", "content": prompt})
            start = time.time()
            resp = await client.chat.completions.create(model=model, messages=messages, max_tokens=512)
            return InferenceResult(
                model=model, prompt=prompt, output=resp.choices[0].message.content,
                latency_ms=(time.time() - start) * 1000,
                tokens_used=resp.usage.total_tokens, provider=ModelProvider.OPENAI,
            )
        except Exception as e:
            return InferenceResult(model=model, prompt=prompt, output="",
                                   latency_ms=0, tokens_used=0,
                                   provider=ModelProvider.OPENAI, error=str(e))


# ─── Mock engine ──────────────────────────────────────────────────────────────

class MockEngine:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate(self, model: str, prompt: str, system: Optional[str] = None) -> InferenceResult:
        profile = MOCK_MODELS.get(model, {"stability": 0.78, "hallucination": 0.12, "speed_ms": 800})
        latency = max(100.0, self.rng.gauss(profile["speed_ms"], profile["speed_ms"] * 0.15))
        numbers = [int(n) for n in re.findall(r'\b\d+\b', prompt)]
        will_hallucinate = self.rng.random() < profile["hallucination"]

        if len(numbers) >= 2:
            correct = sum(numbers)
            answer = str(correct + self.rng.randint(-2, 2)) if will_hallucinate else str(correct)
        else:
            answer = str(self.rng.randint(10, 100)) if will_hallucinate else "42"

        nums_str = " + ".join(str(n) for n in numbers[:3]) if numbers else "the values"
        tpl = self.rng.choice(MOCK_REASONING_TEMPLATES)
        output = tpl.format(
            context=f"problem values: {nums_str}",
            operation=f"compute {nums_str}",
            calc=f"{nums_str} = {answer}",
            answer=answer,
        )
        if self.rng.random() > profile["stability"]:
            output += self.rng.choice([
                "\n\nWait, let me reconsider...\nActually, my answer stands.",
                "\n\nDouble-checking: yes, that is correct.",
            ])
        return InferenceResult(
            model=model, prompt=prompt, output=output,
            latency_ms=latency, tokens_used=self.rng.randint(60, 350),
            provider=ModelProvider.MOCK,
        )


# ─── Router ───────────────────────────────────────────────────────────────────

class InferenceRouter:
    """
    Picks the right engine per model.
    Priority: vLLM → Ollama → OpenAI → Mock
    """

    def __init__(self):
        self.ollama = OllamaEngine()
        self.vllm = VLLMEngine()
        self.langchain = LangChainOllamaEngine()
        self.openai_engine = OpenAIEngine()
        self.mock = MockEngine()
        self._ollama_alive: Optional[bool] = None
        self._vllm_alive: Optional[bool] = None

    async def _check_backends(self):
        if self._ollama_alive is None:
            self._ollama_alive = await self.ollama.health_check()
        if self._vllm_alive is None:
            self._vllm_alive = await self.vllm.health_check()

    async def probe(self) -> Dict[str, Any]:
        cfg = get_settings()
        ollama_up = await self.ollama.health_check()
        vllm_up = await self.vllm.health_check()
        ollama_models = await self.ollama.list_models() if ollama_up else []
        vllm_models = await self.vllm.list_models() if vllm_up else []
        return {
            "ollama": {"alive": ollama_up, "url": cfg.ollama_base_url, "models": ollama_models},
            "vllm":   {"alive": vllm_up,   "url": cfg.vllm_base_url,  "models": vllm_models},
            "openai": {"alive": bool(cfg.openai_api_key)},
            "mock":   {"alive": True},
        }

    async def infer(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        force_mock: bool = False,
        use_langchain: bool = False,
    ) -> InferenceResult:
        if force_mock:
            return self.mock.generate(model, prompt, system)

        cfg = get_settings()
        await self._check_backends()

        # vLLM
        if model in cfg.vllm_model_list and self._vllm_alive:
            result = await self.vllm.generate(model, prompt, system)
            if not result.error:
                return result

        # Ollama / LangChain
        is_local = (
            model in cfg.ollama_model_list
            or cfg.inference_backend == InferenceBackend.OLLAMA
            or ("/" not in model and not model.startswith(("gpt", "claude")))
        )
        if is_local and self._ollama_alive:
            engine = self.langchain if use_langchain else self.ollama
            result = await engine.generate(model, prompt, system)
            if not result.error:
                return result
            print(f"[Router] Ollama error for {model}: {result.error} → mock fallback")

        # OpenAI
        if model.startswith("gpt") and cfg.openai_api_key:
            result = await self.openai_engine.generate(model, prompt, system)
            if not result.error:
                return result

        return self.mock.generate(model, prompt, system)

    async def infer_batch(
        self,
        model: str,
        prompts: List[str],
        system: Optional[str] = None,
        force_mock: bool = False,
        use_langchain: bool = False,
    ) -> List[InferenceResult]:
        cfg = get_settings()
        sem = asyncio.Semaphore(cfg.inference_concurrency)

        async def _limited(p: str) -> InferenceResult:
            async with sem:
                return await self.infer(model, p, system, force_mock, use_langchain)

        return await asyncio.gather(*[_limited(p) for p in prompts])


# ─── Singletons ───────────────────────────────────────────────────────────────

_router = InferenceRouter()


def get_router() -> InferenceRouter:
    return _router


async def get_available_models() -> List[Dict[str, Any]]:
    cfg = get_settings()
    router = get_router()
    probe = await router.probe()
    models = []

    # Live Ollama models (pulled)
    for m in probe["ollama"]["models"]:
        base = m.split(":")[0]
        profile = _LOCAL_MOCK_PROFILES.get(base, _LOCAL_MOCK_PROFILES.get(m, {}))
        models.append({"id": m, "provider": "ollama", "live": True, **profile})

    # Configured but not-yet-pulled Ollama models
    for m in cfg.ollama_model_list:
        if not any(x["id"] == m for x in models):
            base = m.split(":")[0]
            profile = _LOCAL_MOCK_PROFILES.get(base, {})
            models.append({"id": m, "provider": "ollama", "live": False, **profile})

    # vLLM live models
    for m in probe["vllm"]["models"]:
        models.append({"id": m, "provider": "vllm", "live": True,
                       "stability": 0.86, "hallucination": 0.08, "speed_ms": 300})

    # Cloud entries (always shown)
    for mid, prof in _CLOUD_MOCK_PROFILES.items():
        models.append({"id": mid, "live": False, **prof})

    return models
