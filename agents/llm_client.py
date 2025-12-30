import ollama
from ollama import Client, AsyncClient
from .models import ChatResponse, ChatRequest
from config.setting import GLOBAL_API_URL, GLOBAL_API_KEY

def parse_response(response: ollama.ChatResponse) -> ChatResponse:
    return ChatResponse(
        role=response.message.role,
        content=response.message.content,
        thinking=response.message.thinking,
        images=response.message.images,
        tool_calls=response.message.tool_calls,
        model=response.model,
        created_at=response.created_at,
        prompt_eval_count=response.prompt_eval_count,
        eval_count=response.eval_count
    )

def chat(request: ChatRequest, api_url: str = None, api_key: str = None) -> ChatResponse:
    api_url = api_url or GLOBAL_API_URL
    api_key = api_key or GLOBAL_API_KEY
    
    client = Client(
        host=api_url,
        headers={'Authorization': 'Bearer ' + api_key } if api_key else None
    )
    
    messages = request.messages or []
    response: ollama.ChatResponse = client.chat(
        model=request.model,
        messages=messages,
        tools=request.tools,
        think=request.think,
        format=request.format,
        options={
            "num_ctx": request.num_ctx,
            "temperature": request.temperature
        }
    )
    
    return parse_response(response)
    
async def async_chat(request: ChatRequest, api_url: str = None, api_key: str = None) -> ChatResponse:
    api_url = api_url or GLOBAL_API_URL
    api_key = api_key or GLOBAL_API_KEY
    
    async_client = AsyncClient(
        host=api_url,
        headers={'Authorization': 'Bearer ' + api_key} if api_key else None
    )
    
    messages = request.messages or []
    response: ollama.ChatResponse = await async_client.chat(
        model=request.model,
        messages=messages,
        tools=request.tools,
        think=request.think,
        format=request.format,
        options={
            "num_ctx": request.num_ctx,
            "temperature": request.temperature
        }
    )
    
    return parse_response(response)