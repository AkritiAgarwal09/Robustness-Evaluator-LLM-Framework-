"""
Adversarial Prompt Perturbation Engine
Generates semantically equivalent but structurally varied prompts
"""
import re
import random
from typing import List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class PerturbationType(str, Enum):
    LEXICAL_SUBSTITUTION = "lexical_substitution"
    PARAPHRASE = "paraphrase"
    INSTRUCTION_INJECTION = "instruction_injection"
    TOKEN_DELETION = "token_deletion"
    COT_MANIPULATION = "cot_manipulation"
    STEP_REORDERING = "step_reordering"
    NEGATION_INSERTION = "negation_insertion"
    FORMALITY_SHIFT = "formality_shift"


@dataclass
class PromptVariant:
    original: str
    perturbed: str
    perturbation_type: PerturbationType
    metadata: Dict[str, Any] = field(default_factory=dict)


# Lexical substitution maps
SYNONYM_MAP = {
    "has": ["owns", "possesses", "holds", "carries"],
    "buy": ["purchase", "acquire", "obtain", "get"],
    "buys": ["purchases", "acquires", "obtains", "gets"],
    "more": ["additional", "extra", "further", "another"],
    "total": ["sum", "overall", "combined", "aggregate"],
    "how many": ["what is the count of", "what number of", "how much"],
    "calculate": ["compute", "determine", "find", "figure out"],
    "solve": ["answer", "work out", "resolve", "address"],
    "first": ["initially", "at the start", "to begin with", "originally"],
    "then": ["after that", "subsequently", "next", "following that"],
    "each": ["every", "apiece", "per", "individually"],
    "total number": ["overall count", "combined amount", "final tally"],
    "find": ["determine", "calculate", "compute", "identify"],
    "gives": ["hands", "provides", "transfers", "passes"],
    "takes": ["removes", "takes away", "subtracts"],
    "remaining": ["left", "leftover", "still available"],
}

COT_PREFIXES = [
    "Let's think step by step.",
    "Think carefully and solve step by step.",
    "Work through this methodically:",
    "Let me reason through this:",
    "Step-by-step solution:",
    "Reasoning:",
]

INSTRUCTION_INJECTIONS = [
    "Answer step by step: ",
    "Solve carefully: ",
    "Think before answering: ",
    "Work through this problem: ",
    "Calculate step by step: ",
]

FORMALITY_TRANSFORMS = {
    "formal": {
        "can't": "cannot",
        "don't": "do not",
        "won't": "will not",
        "it's": "it is",
        "they're": "they are",
        "there's": "there is",
    },
    "casual": {
        "cannot": "can't",
        "do not": "don't",
        "will not": "won't",
        "it is": "it's",
        "they are": "they're",
        "there is": "there's",
    }
}


class PerturbationEngine:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate_variants(
        self,
        prompt: str,
        perturbation_types: List[PerturbationType] = None,
        num_variants: int = 5,
    ) -> List[PromptVariant]:
        """Generate multiple perturbation variants of a prompt."""
        if perturbation_types is None:
            perturbation_types = list(PerturbationType)

        variants = []
        used_types = set()

        for _ in range(num_variants):
            available = [t for t in perturbation_types if t not in used_types]
            if not available:
                used_types.clear()
                available = perturbation_types

            ptype = self.rng.choice(available)
            used_types.add(ptype)

            variant = self._apply_perturbation(prompt, ptype)
            if variant and variant.perturbed != prompt:
                variants.append(variant)

        return variants

    def _apply_perturbation(self, prompt: str, ptype: PerturbationType) -> PromptVariant:
        """Apply a specific perturbation type."""
        handlers = {
            PerturbationType.LEXICAL_SUBSTITUTION: self._lexical_substitution,
            PerturbationType.PARAPHRASE: self._paraphrase,
            PerturbationType.INSTRUCTION_INJECTION: self._instruction_injection,
            PerturbationType.TOKEN_DELETION: self._token_deletion,
            PerturbationType.COT_MANIPULATION: self._cot_manipulation,
            PerturbationType.STEP_REORDERING: self._step_reordering,
            PerturbationType.NEGATION_INSERTION: self._negation_insertion,
            PerturbationType.FORMALITY_SHIFT: self._formality_shift,
        }
        handler = handlers.get(ptype, self._paraphrase)
        perturbed = handler(prompt)
        return PromptVariant(
            original=prompt,
            perturbed=perturbed,
            perturbation_type=ptype,
            metadata={"method": ptype.value}
        )

    def _lexical_substitution(self, prompt: str) -> str:
        """Replace words with synonyms."""
        result = prompt
        for word, synonyms in SYNONYM_MAP.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, result, re.IGNORECASE):
                replacement = self.rng.choice(synonyms)
                result = re.sub(pattern, replacement, result, count=1, flags=re.IGNORECASE)
        return result

    def _paraphrase(self, prompt: str) -> str:
        """Simple structural paraphrase."""
        sentences = prompt.replace('?', '?.').replace('!', '!.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]

        transforms = [
            lambda s: s,
            lambda s: s.lower(),
            lambda s: s[0].upper() + s[1:] if s else s,
        ]

        result_parts = []
        for sent in sentences:
            transform = self.rng.choice(transforms)
            result_parts.append(transform(sent))

        return '. '.join(result_parts) + ('?' if prompt.endswith('?') else '.')

    def _instruction_injection(self, prompt: str) -> str:
        """Prepend chain-of-thought instruction."""
        prefix = self.rng.choice(INSTRUCTION_INJECTIONS)
        return prefix + prompt

    def _token_deletion(self, prompt: str) -> str:
        """Delete non-essential tokens."""
        filler_words = ['very', 'quite', 'just', 'actually', 'basically', 'really', 'simply']
        result = prompt
        for word in filler_words:
            pattern = r'\b' + word + r'\b\s*'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        # Remove redundant spaces
        result = re.sub(r'\s+', ' ', result).strip()
        return result if result != prompt else prompt + " Show your work."

    def _cot_manipulation(self, prompt: str) -> str:
        """Add explicit chain-of-thought framing."""
        prefix = self.rng.choice(COT_PREFIXES)
        return f"{prefix}\n\n{prompt}"

    def _step_reordering(self, prompt: str) -> str:
        """Restructure multi-sentence prompt."""
        sentences = [s.strip() for s in prompt.split('.') if s.strip()]
        if len(sentences) <= 1:
            return f"Given the following: {prompt}"

        # Keep first sentence (usually context) and shuffle rest
        context = sentences[0]
        rest = sentences[1:]
        self.rng.shuffle(rest)
        return '. '.join([context] + rest) + '.'

    def _negation_insertion(self, prompt: str) -> str:
        """Rephrase using negation patterns (without changing semantics)."""
        # Add a "do not skip steps" style clarification
        clarifications = [
            " Do not skip any reasoning steps.",
            " Make sure not to miss any details.",
            " Don't rush — show all work.",
        ]
        return prompt + self.rng.choice(clarifications)

    def _formality_shift(self, prompt: str) -> str:
        """Shift formality level."""
        target = self.rng.choice(['formal', 'casual'])
        result = prompt
        for informal, formal in FORMALITY_TRANSFORMS['formal'].items():
            if target == 'formal':
                result = re.sub(r'\b' + re.escape(informal) + r'\b', formal, result, flags=re.IGNORECASE)
            else:
                result = re.sub(r'\b' + re.escape(formal) + r'\b', informal, result, flags=re.IGNORECASE)
        return result


# Singleton engine
_engine = PerturbationEngine()


def get_engine() -> PerturbationEngine:
    return _engine
