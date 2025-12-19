import json

# Simulate different LLM responses
test_responses = [
    # With code block and json tag
    """```json
{"passed": true, "issues": "", "should_retry": false, "reasoning": "All facts verified"}
```""",
    # With code block, no json tag
    """```
{"passed": false, "issues": "Missing citation", "should_retry": true, "reasoning": "Fixable"}
```""",
    # Raw JSON (no code block)
    '{"passed": true, "issues": "", "should_retry": false, "reasoning": "Looks good"}',
]

for i, response in enumerate(test_responses):
    print(f"\n--- Test {i + 1} ---")
    print(f"Input: {repr(response[:50])}...")

    response_text = response.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        print(f"After split: {repr(response_text[:50])}...")
        if response_text.startswith("json"):
            response_text = response_text[4:]
            print(f"After removing 'json': {repr(response_text[:50])}...")

    result = json.loads(response_text)
    print(f"Parsed result: {result}")
    print(f"  passed: {result.get('passed')}")
    print(f"  issues: {result.get('issues')}")
    print(f"  should_retry: {result.get('should_retry')}")
