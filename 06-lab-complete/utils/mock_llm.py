"""Mock LLM used for local lab runs."""
import random
import time


MOCK_RESPONSES = {
    "default": [
        "Day 12 production agent is working with mock LLM output.",
        "The request was processed successfully by the mock production agent.",
        "This is a mock response from the production-ready AI agent.",
    ],
    "docker": ["Containers package code and dependencies so apps run consistently anywhere."],
    "deploy": ["Deployment moves your application from local development to a reachable runtime environment."],
    "health": ["The service is healthy and able to respond to requests."],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.03))
    lowered = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in lowered:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])
