from groq import Groq

from app.config import settings

_client: Groq | None = None

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer only from the provided CONTEXT. "
    "If the answer is not present in the context, clearly state that the file does not contain this information. "
    "Respond in the same language as the user's question. "
    "Keep the answer brief and clear."
)


def get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def generate_answer(query: str, contexts: list[dict]) -> str:
    """Send the retrieved chunks and the user's question to the Groq LLM and return the answer."""
    context_text = "\n\n---\n\n".join(
        f"[{i + 1}] ({c['filename']})\n{c['content']}" for i, c in enumerate(contexts)
    )

    response = get_client().chat.completions.create(
        model=settings.groq_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"CONTEXT:\n{context_text}\n\nQUESTION: {query}",
            },
        ],
    )
    return response.choices[0].message.content or ""