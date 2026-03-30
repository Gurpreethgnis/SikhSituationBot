import os
import sys
import json
import logging

# Add server path to sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))

# Try importing the function
try:
    from llm_synthesis import synthesize_chat_response
except ImportError as e:
    print(f"Failed to import synthesize_chat_response: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_golden_dataset():
    dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset block not found: {dataset_path}")
        return
        
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    results = {}
    passed = 0
    
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
            
        results[item['id']] = {
            "passed": result_correct,
            "is_fallback_triggered": is_fallback,
            "response_preview": response_text[:100].replace('\n', ' ') + "..." if response_text else "None"
        }
    
    logger.info(f"EVAL RESULTS: {passed}/{len(dataset)} passed.")
    for k, v in results.items():
        pass_str = "PASS" if v['passed'] else "FAIL"
        logger.info(f"  [{pass_str}] {k}: fallback={v['is_fallback_triggered']}")

if __name__ == "__main__":
    evaluate_golden_dataset()
