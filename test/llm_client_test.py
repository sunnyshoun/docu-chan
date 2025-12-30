from agents.models import ChatRequest
from agents.llm_client import chat, async_chat
import asyncio

request = ChatRequest(
    model="gemma3:4b",
    messages=[
        {"role":"user", "content":"Hello, how are you?"}
    ]
)


print(asyncio.run(async_chat(request)))