import logging
import os

from openai import OpenAI, APIError, RateLimitError

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

# Cost per 1k tokens
COST_TABLE = {
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
    "gemini-1.5-flash": {"input": 0.0, "output": 0.0},
}


class OpenAIService:

    @staticmethod
    def chat(
        system_prompt: str,
        user_prompt: str,
        model: str = "llama-3.1-8b-instant",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        messages_history: list = None,
    ) -> dict:
        """
        Returns: { content, tokens_in, tokens_out, total_tokens, cost_usd }
        Raises on API failure so callers can set execution status to 'failed'.
        """
        try:
            # Auto-map models if the active provider is Groq to prevent model_not_found errors
            base_url_lower = os.getenv("OPENAI_BASE_URL", "").lower()
            if "groq.com" in base_url_lower:
                if model.startswith("gpt-4o-mini") or model.startswith("gpt-3"):
                    model = "llama-3.1-8b-instant"
                elif model.startswith("gpt-4") or model.startswith("gpt-3.5"):
                    model = "llama-3.3-70b-versatile"
                elif model.startswith("llama3"):
                    if "70b" in model:
                        model = "llama-3.3-70b-versatile"
                    else:
                        model = "llama-3.1-8b-instant"

            messages = [{"role": "system", "content": system_prompt}]
            if messages_history:
                messages.extend(messages_history)
            messages.append({"role": "user", "content": user_prompt})

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content
            usage = response.usage

            tokens_in = usage.prompt_tokens
            tokens_out = usage.completion_tokens
            total = usage.total_tokens

            rates = COST_TABLE.get(model, COST_TABLE["gpt-4o-mini"])
            cost = (tokens_in / 1000 * rates["input"]) + (tokens_out / 1000 * rates["output"])

            return {
                "content": content,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "total_tokens": total,
                "cost_usd": round(cost, 6),
            }

        except RateLimitError:
            logger.error("OpenAI rate limit hit")
            raise

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise