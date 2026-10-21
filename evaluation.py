"""LLM-as-a-judge scoring with DeepEval, using Gemini as the judge model."""
import json

from deepeval.metrics import GEval
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from google.genai import types

try:
    from deepeval.test_case import SingleTurnParams as EvalParams    # DeepEval 4.x
except ImportError:
    from deepeval.test_case import LLMTestCaseParams as EvalParams   # DeepEval 3.x

from . import config
from .llm import a_gemini_generate, gemini, gemini_generate
from .prompts import QUALITY_CRITERIA


class GeminiJudge(DeepEvalBaseLLM):
    """Lets DeepEval metrics use Gemini (via google-genai) as the judge model."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = gemini
        self.model = self.client

    def load_model(self):
        return self.client

    def _config(self, schema):
        if schema is None:
            return types.GenerateContentConfig(temperature=0)
        # DeepEval asks for JSON that matches a schema
        return types.GenerateContentConfig(temperature=0, response_mime_type="application/json")

    def generate(self, prompt: str, schema=None):
        resp = gemini_generate(model=self.model_name, contents=prompt, config=self._config(schema))
        return schema(**json.loads(resp.text)) if schema else resp.text

    async def a_generate(self, prompt: str, schema=None):
        resp = await a_gemini_generate(
            model=self.model_name, contents=prompt, config=self._config(schema)
        )
        return schema(**json.loads(resp.text)) if schema else resp.text

    def get_model_name(self):
        return self.model_name


judge_model = GeminiJudge(config.JUDGE_MODEL)


def score_chatbot_response(user_query: str, chatbot_response: str):
    """Grade a response with GEval. Returns (score 0-10, reason), or (None, None) on failure."""
    try:
        metric = GEval(
            name="Response quality",
            criteria=QUALITY_CRITERIA,
            evaluation_params=[EvalParams.INPUT, EvalParams.ACTUAL_OUTPUT],
            model=judge_model,
            threshold=0.7,
            async_mode=False,  # avoids event-loop clashes inside Streamlit
        )
        metric.measure(LLMTestCase(input=user_query, actual_output=chatbot_response))
        return round(metric.score * 10), metric.reason
    except Exception as e:
        print(f"DeepEval scoring error: {e}")
        return None, None
