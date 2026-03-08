"""
Reasoning Trace Extraction & Analysis Module
Parses, compares, and scores reasoning chains from LLM outputs.
"""
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import difflib


@dataclass
class ReasoningStep:
    index: int
    content: str
    step_type: str  # 'calculation', 'inference', 'assumption', 'conclusion'
    confidence: float = 1.0
    is_supported: bool = True


@dataclass
class ReasoningTrace:
    steps: List[ReasoningStep]
    final_answer: Optional[str]
    raw_output: str
    has_cot: bool = False

    def to_text(self) -> str:
        return "\n".join(f"Step {s.index}: {s.content}" for s in self.steps)

    def step_contents(self) -> List[str]:
        return [s.content for s in self.steps]


class ReasoningTraceParser:
    """Extract structured reasoning traces from LLM outputs."""

    STEP_PATTERNS = [
        r'(?:step\s*\d+[:\.\)]\s*)(.+)',
        r'(?:^\d+[:\.\)]\s*)(.+)',
        r'(?:first[,:]?\s*)(.+)',
        r'(?:next[,:]?\s*)(.+)',
        r'(?:then[,:]?\s*)(.+)',
        r'(?:finally[,:]?\s*)(.+)',
        r'(?:therefore[,:]?\s*)(.+)',
        r'(?:so[,:]?\s*)(.+)',
    ]

    ANSWER_PATTERNS = [
        r'(?:the answer is|answer:?)\s*(.+)',
        r'(?:therefore[,\s]+the answer[^=]*=?\s*)(\S+)',
        r'(?:total[^\d]*)([\d,]+)',
        r'(?:=\s*)([\d,]+)(?:\s*$)',
        r'(\d+)\s*(?:apples?|items?|units?|dollars?|years?|days?|hours?)?\s*\.?\s*$',
    ]

    STEP_TYPES = {
        'calculation': r'(?:\d+\s*[\+\-\×\÷\*\/]\s*\d+|=\s*\d+|sum|total|multiply|divide|add|subtract)',
        'inference': r'(?:therefore|thus|hence|so|because|since|implies|means)',
        'assumption': r'(?:assume|given|let|suppose|if|when)',
        'conclusion': r'(?:answer|result|final|conclusion|therefore)',
    }

    def parse(self, raw_output: str) -> ReasoningTrace:
        """Parse raw LLM output into structured reasoning trace."""
        steps = self._extract_steps(raw_output)
        final_answer = self._extract_answer(raw_output)
        has_cot = len(steps) > 1 or bool(re.search(r'step|first|then|therefore', raw_output, re.IGNORECASE))

        return ReasoningTrace(
            steps=steps,
            final_answer=final_answer,
            raw_output=raw_output,
            has_cot=has_cot,
        )

    def _extract_steps(self, text: str) -> List[ReasoningStep]:
        steps = []
        lines = text.strip().split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Try each step pattern
            matched = False
            for pattern in self.STEP_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    if len(content) > 3:
                        step_type = self._classify_step(content)
                        steps.append(ReasoningStep(
                            index=len(steps) + 1,
                            content=content,
                            step_type=step_type,
                        ))
                        matched = True
                        break

            if not matched and len(line) > 10:
                # Include substantial lines even without explicit step markers
                step_type = self._classify_step(line)
                steps.append(ReasoningStep(
                    index=len(steps) + 1,
                    content=line,
                    step_type=step_type,
                ))

        # Deduplicate very similar steps
        return self._deduplicate_steps(steps)

    def _classify_step(self, content: str) -> str:
        for step_type, pattern in self.STEP_TYPES.items():
            if re.search(pattern, content, re.IGNORECASE):
                return step_type
        return 'inference'

    def _deduplicate_steps(self, steps: List[ReasoningStep]) -> List[ReasoningStep]:
        if not steps:
            return steps
        unique = [steps[0]]
        for step in steps[1:]:
            ratio = difflib.SequenceMatcher(None, step.content, unique[-1].content).ratio()
            if ratio < 0.8:
                unique.append(step)
        return unique

    def _extract_answer(self, text: str) -> Optional[str]:
        # Try patterns from most specific to least
        for pattern in self.ANSWER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                # Clean up
                answer = re.sub(r'[^\w\s\.\,\-]', '', answer).strip()
                if answer:
                    return answer

        # Fallback: last number in text
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        if numbers:
            return numbers[-1]

        return None


class ReasoningStabilityAnalyzer:
    """Analyze stability across multiple reasoning traces."""

    def __init__(self):
        self.parser = ReasoningTraceParser()

    def compute_answer_stability(self, answers: List[Optional[str]]) -> float:
        """Fraction of prompts that produce the same final answer."""
        valid = [a for a in answers if a is not None]
        if not valid:
            return 0.0

        # Normalize answers
        normalized = [self._normalize_answer(a) for a in valid]
        most_common = max(set(normalized), key=normalized.count)
        consistent = sum(1 for a in normalized if a == most_common)
        return consistent / len(valid)

    def compute_reasoning_drift(self, trace1: ReasoningTrace, trace2: ReasoningTrace) -> float:
        """Edit distance between reasoning traces (normalized 0-1)."""
        text1 = trace1.to_text()
        text2 = trace2.to_text()

        if not text1 and not text2:
            return 0.0
        if not text1 or not text2:
            return 1.0

        matcher = difflib.SequenceMatcher(None, text1, text2)
        similarity = matcher.ratio()
        return round(1.0 - similarity, 4)

    def compute_semantic_consistency(self, traces: List[ReasoningTrace]) -> float:
        """Simple token overlap-based semantic consistency."""
        if len(traces) < 2:
            return 1.0

        def tokenize(text: str):
            return set(re.findall(r'\b\w+\b', text.lower()))

        all_tokens = [tokenize(t.to_text()) for t in traces]
        scores = []
        for i in range(len(all_tokens)):
            for j in range(i + 1, len(all_tokens)):
                a, b = all_tokens[i], all_tokens[j]
                if a | b:
                    jaccard = len(a & b) / len(a | b)
                    scores.append(jaccard)

        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def compute_hallucination_rate(self, traces: List[ReasoningTrace], ground_truth: Optional[str] = None) -> float:
        """
        Estimate hallucination as fraction of steps with unsupported numeric claims.
        If ground_truth provided, checks answer correctness.
        """
        if not traces:
            return 0.0

        hallucinated = 0
        total_steps = 0

        for trace in traces:
            for step in trace.steps:
                total_steps += 1
                # Check for numeric inconsistency
                numbers = re.findall(r'\b\d+(?:\.\d+)?\b', step.content)
                if len(numbers) > 2:
                    # Heuristic: steps with many unexplained numbers may be hallucinated
                    hallucinated += 0.3

        if ground_truth and traces:
            wrong = sum(1 for t in traces
                       if t.final_answer and self._normalize_answer(t.final_answer) != self._normalize_answer(ground_truth))
            hallucinated += wrong

        total = max(total_steps + (len(traces) if ground_truth else 0), 1)
        return round(min(hallucinated / total, 1.0), 4)

    def compute_robustness_score(
        self,
        answer_stability: float,
        reasoning_drift: float,
        semantic_consistency: float,
        hallucination_rate: float,
    ) -> float:
        """Composite robustness score (0-1, higher = more robust)."""
        score = (
            answer_stability * 0.35 +
            (1 - reasoning_drift) * 0.25 +
            semantic_consistency * 0.25 +
            (1 - hallucination_rate) * 0.15
        )
        return round(min(max(score, 0.0), 1.0), 4)

    def analyze_traces(self, traces: List[ReasoningTrace], ground_truth: Optional[str] = None) -> dict:
        """Full analysis of a set of reasoning traces."""
        answers = [t.final_answer for t in traces]
        answer_stability = self.compute_answer_stability(answers)

        drifts = []
        if len(traces) >= 2:
            baseline = traces[0]
            for trace in traces[1:]:
                drifts.append(self.compute_reasoning_drift(baseline, trace))
        avg_drift = sum(drifts) / len(drifts) if drifts else 0.0

        semantic_consistency = self.compute_semantic_consistency(traces)
        hallucination_rate = self.compute_hallucination_rate(traces, ground_truth)
        robustness_score = self.compute_robustness_score(
            answer_stability, avg_drift, semantic_consistency, hallucination_rate
        )

        return {
            "answer_stability": answer_stability,
            "reasoning_drift": round(avg_drift, 4),
            "semantic_consistency": semantic_consistency,
            "hallucination_rate": hallucination_rate,
            "robustness_score": robustness_score,
            "total_traces": len(traces),
            "traces_with_cot": sum(1 for t in traces if t.has_cot),
            "answers": answers,
            "drift_per_variant": drifts,
        }

    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer for comparison."""
        answer = answer.lower().strip()
        answer = re.sub(r'[^\w\d]', '', answer)
        return answer


# Singletons
_parser = ReasoningTraceParser()
_analyzer = ReasoningStabilityAnalyzer()


def get_parser() -> ReasoningTraceParser:
    return _parser


def get_analyzer() -> ReasoningStabilityAnalyzer:
    return _analyzer
