# LLM Robustness & Reasoning Stability Framework

A systematic evaluation framework for measuring how stable LLM reasoning is under adversarial prompt perturbations.

## Architecture

```
llm-robustness/
├── backend/
│   ├── core/
│   │   ├── perturbation.py   # Adversarial prompt generator (8 perturbation types)
│   │   ├── reasoning.py      # Trace extraction & stability analysis
│   │   ├── inference.py      # Multi-model inference router (OpenAI/Anthropic/Mock)
│   │   └── pipeline.py       # Evaluation orchestration pipeline
│   ├── api/
│   │   └── main.py           # FastAPI REST API
│   └── requirements.txt
├── frontend/
│   └── src/
│       └── App.jsx           # React dashboard with interactive charts
├── start.sh                  # One-command startup
└── README.md
```

## Quick Start

### Option A: Dashboard Only (no backend needed)
Open the `frontend/src/App.jsx` as a React artifact — it runs fully in-browser with mock data and optional live Claude API calls.

### Option B: Full Stack

**Prerequisites:** Python 3.10+, Node.js 18+

```bash
# Clone and start everything
chmod +x start.sh
./start.sh

# Dashboard → http://localhost:3000
# API Docs  → http://localhost:8000/docs
```

### Option C: Backend Only (headless evaluation)

```bash
cd backend
pip install -r requirements.txt
export PYTHONPATH=.

# Run a quick demo via API
uvicorn api.main:app --reload

# Trigger demo evaluation
curl http://localhost:8000/demo
```

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/evaluate/sync` | POST | Run evaluation synchronously |
| `/evaluate` | POST | Start async evaluation job |
| `/evaluate/{job_id}` | GET | Poll job status |
| `/demo` | GET | Run built-in demo |
| `/models` | GET | List available models |
| `/perturbation-types` | GET | List perturbation types |

### Example Request

```bash
curl -X POST http://localhost:8000/evaluate/sync \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "John has 5 apples. He buys 3 more. How many does he have?",
    "models": ["gpt-4o", "claude-3-sonnet", "llama-3-70b"],
    "ground_truth": "8",
    "num_variants": 5,
    "force_mock": true
  }'
```

## Perturbation Types

| Type | Description |
|---|---|
| `lexical_substitution` | Replace words with synonyms |
| `paraphrase` | Restructure sentences |
| `instruction_injection` | Prepend CoT instructions |
| `token_deletion` | Remove non-essential tokens |
| `cot_manipulation` | Add explicit reasoning frames |
| `step_reordering` | Reorder prompt sentences |
| `negation_insertion` | Add clarifying negations |
| `formality_shift` | Shift formal/casual register |

## Metrics

| Metric | Formula | Interpretation |
|---|---|---|
| **Answer Stability** | `consistent_answers / total_prompts` | % of variants producing same answer |
| **Reasoning Drift** | `1 - SequenceMatcher(trace1, trace2)` | Structural change in reasoning |
| **Semantic Consistency** | `Jaccard(tokens_i, tokens_j)` | Token overlap across traces |
| **Hallucination Rate** | Unsupported steps / total steps | Fraction of suspicious reasoning |
| **Robustness Score** | Weighted composite | Overall stability score (0–1) |

## Adding Real API Keys

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Now set force_mock: false in requests to use real models
```

## Extending the Framework

### Add a new perturbation type
1. Add to `PerturbationType` enum in `perturbation.py`
2. Implement handler method `_my_perturbation(prompt) -> str`
3. Register in `_apply_perturbation` dispatch dict

### Add a new model provider
1. Create class `MyProviderEngine` with `async generate(model, prompt, system) -> InferenceResult`
2. Register in `InferenceRouter.get_engine()`
3. Add model IDs to `MOCK_MODELS` for mock fallback

## Datasets Supported

- **GSM8K** — Grade school math reasoning
- **MATH** — Competition mathematics  
- **BIG-Bench** — Diverse reasoning tasks
- **TruthfulQA** — Factual accuracy
- **StrategyQA** — Multi-hop reasoning

## Future Extensions

- [ ] Self-consistency voting across reasoning samples
- [ ] RL-based prompt repair for unstable prompts
- [ ] Red-teaming module for automated adversarial discovery
- [ ] Embedding-based semantic similarity (sentence-transformers)
- [ ] DuckDB persistence layer for experiment tracking
- [ ] W&B / MLflow integration for run logging
