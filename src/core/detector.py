import json
import os
import re

import google.generativeai as genai
from dotenv import load_dotenv

from core.processor import split_sentences

load_dotenv()

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```")


def _parse_response(raw: str) -> dict:
    match = _FENCE_RE.search(raw)
    text = match.group(1) if match else raw
    return json.loads(text.strip())


class Detector:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in the environment.")
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(model_name)

    def detect(self, text: str) -> dict:
        sentences = split_sentences(text)

        numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(sentences))

        prompt = f"""You are an AI-text classifier. For each numbered sentence below, output the probability (0–100) that it was written by an AI language model.

Sentences:
{numbered}

Respond with ONLY valid JSON in this exact shape — no explanation, no markdown fences:
{{
  "overall_score": <float 0-100, weighted average across all sentences>,
  "sentences": [
    {{"text": "<exact sentence text>", "ai_probability": <float 0-100>}},
    ...one entry per sentence in the same order...
  ]
}}"""

        response = self.model.generate_content(prompt)
        result = _parse_response(response.text)
        return result
