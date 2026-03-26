from fastapi import APIRouter
from core.config import settings
from openai import AsyncOpenAI

router = APIRouter()

@router.get("/test-llm")
async def test_llm(model: str = "qwen3:8b"):
    """
    Test the LLM capabilities of Ollama using an OpenAI-compatible request.

    Args:
        model (str, optional): The name of the model to test. Defaults to "qwen3:8b".

    Returns:
        dict: The LLM response, reasoning (if available), and debug information.
    """
    try:
        client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
        )
        
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=512,
            temperature=0.7
        )
        
        message = response.choices[0].message
        return {
            "status": "Success",
            "model": model,
            "response": message.content,
            "reasoning": getattr(message, "reasoning", None),
            "debug_info": {
                "finish_reason": response.choices[0].finish_reason,
                "message_obj": message.model_dump()
            }
        }
    except Exception as e:
        return {"status": "LLM test failed", "error": str(e)}
