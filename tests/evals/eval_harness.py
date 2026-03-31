import os
import sys
import json
import logging
import re
from collections import Counter

# Add server path to sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))

# Ensure local evals can run without production DB env.
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("DATABASE_URL_TEST", "sqlite:///:memory:")

# Try importing the function
try:
    from llm_synthesis import synthesize_chat_response
    from app import app
except ImportError as e:
    print(f"Failed to import synthesize_chat_response: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _first_nonempty_line(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _last_nonempty_line(text: str) -> str:
    for line in reversed((text or "").splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _normalize_phrase(s: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", (s or "").strip().lower())


def _line_repetition_ratio(text: str) -> float:
    lines = [_normalize_phrase(l) for l in (text or "").splitlines() if _normalize_phrase(l)]
    if not lines:
        return 0.0
    counts = Counter(lines)
    repeated = sum(v for v in counts.values() if v > 1)
    return repeated / float(len(lines))

def evaluate_golden_dataset():
    dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset block not found: {dataset_path}")
        return
        
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    results = {}
    passed = 0
    openers = []
    closers = []
    line_rep_ratios = []
    
    for item in dataset:
        target = item['expected_refusal']
        logger.info(f"evaluating: {item['id']}")
        
        # If in_domain, we provide a basic shabad to see if the LLM parses it properly without returning a refusal
        # For out_of_domain, we provide no shabads normally, but to test if it forces a refusal even if given a shabad,
        # we can provide a small dummy one.
        
        shabads = [{
            'shabad_id': 'test_123',
            'gurmukhi': 'ਨਾਨਕ ਚਿੰਤਾ ਮਤਿ ਕਰਹੁ ਚਿੰਤਾ ਤਿਸ ਹੀ ਹੇਇ ॥',
            'english_translation': 'O Nanak, do not worry; the Lord will take care of you.',
            'source': 'Ang 1070',
        }]

        # Actually, for completely_unrelated or history, let's see how the prompt handles it
        raw_result = synthesize_chat_response(
            user_query=item['query'],
            shabads=shabads,
            persona="adult",
            language="en",
            guidance_mode="guidance"
        )
        
        # synthesize_chat_response returns (text, provider, model_id)
        if hasattr(raw_result, "__len__") and len(raw_result) == 3:
            response_text = raw_result[0]
        else:
            response_text = str(raw_result)
        
        # We explicitly set text = None in llm_synthesis.py on refusal token which then triggers FALLBACK_RESPONSE
        # Fallback string ends with "No relevant Gurbani verses found." or similar from prompts.py
        is_fallback = "No relevant Gurbani verses found" in response_text or "Sikh wisdom" in response_text

        result_correct = (is_fallback == target)
        if result_correct:
            passed += 1
            
        opener = _normalize_phrase(_first_nonempty_line(response_text))
        closer = _normalize_phrase(_last_nonempty_line(response_text))
        rep_ratio = _line_repetition_ratio(response_text)
        if opener:
            openers.append(opener)
        if closer:
            closers.append(closer)
        line_rep_ratios.append(rep_ratio)

        results[item['id']] = {
            "passed": result_correct,
            "is_fallback_triggered": is_fallback,
            "opener": opener,
            "closer": closer,
            "line_repetition_ratio": round(rep_ratio, 3),
            "response_preview": response_text[:100].replace('\n', ' ') + "..." if response_text else "None"
        }
    
    opener_repeat_rate = 0.0
    closer_repeat_rate = 0.0
    if openers:
        opener_repeat_rate = 1.0 - (len(set(openers)) / float(len(openers)))
    if closers:
        closer_repeat_rate = 1.0 - (len(set(closers)) / float(len(closers)))
    avg_line_repetition = sum(line_rep_ratios) / float(len(line_rep_ratios) or 1)

    logger.info(f"EVAL RESULTS: {passed}/{len(dataset)} passed.")
    logger.info(
        "STYLE METRICS: opener_repeat_rate=%.3f closer_repeat_rate=%.3f avg_line_repetition=%.3f",
        opener_repeat_rate,
        closer_repeat_rate,
        avg_line_repetition,
    )
    for k, v in results.items():
        pass_str = "PASS" if v['passed'] else "FAIL"
        logger.info(f"  [{pass_str}] {k}: fallback={v['is_fallback_triggered']}")

    # Print a compact JSON block so CI can parse trend metrics.
    print(
        json.dumps(
            {
                "passed": passed,
                "total": len(dataset),
                "opener_repeat_rate": round(opener_repeat_rate, 3),
                "closer_repeat_rate": round(closer_repeat_rate, 3),
                "avg_line_repetition": round(avg_line_repetition, 3),
            }
        )
    )

if __name__ == "__main__":
    with app.app_context():
        evaluate_golden_dataset()
