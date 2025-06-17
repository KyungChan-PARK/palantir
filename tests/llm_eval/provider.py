"""Simple mock provider for promptfoo tests."""

def call_api(prompt, options=None, context=None):
    return {"output": f"ECHO: {prompt}"}
