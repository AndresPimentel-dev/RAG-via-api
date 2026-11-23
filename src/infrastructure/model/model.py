from google import genai
from google.genai import types

from src.domain.exceptions import InfrastructureException
from src.domain.interfaces import LLMService, LogProvider


class LLMServiceInfrastructure(LLMService):
    def __init__(self, api_key: str, log_provider: LogProvider):
        self.client = genai.Client(api_key=api_key)
        self.log_provider = log_provider

    def generate_embeddings(self, plain_chunks: str | list[str]):
        try:
            response = self.client.models.embed_content(
                model="gemini-embedding-001", contents=plain_chunks
            )
            return response
        except Exception as e:
            self.log_provider.error_log(
                message="error generating embeddings",
                context=str(e),
                confid=types.EmbedContentConfig(output_dimensionality=3072),
            )
            raise InfrastructureException("error generating embeddings") from e

    def get_answer(self, prompt: str):
        try:
            response = self.client.models.generate_content(
                model="gemini-3.5-flash-lite", contents=prompt
            )
            return response
        except Exception as e:
            self.log_provider.error_log(
                message="error generating answer from llm", context=str(e)
            )
            raise InfrastructureException("error generating LLM answer") from e
