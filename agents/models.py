from typing import Callable, Optional, Mapping, Any, Literal
from dataclasses import dataclass, field
from pathlib import Path
from pydantic import BaseModel
from pydantic import model_serializer
from base64 import b64encode, b64decode

class Image(BaseModel):
  value: str | bytes | Path

  @model_serializer
  def serialize_model(self):
    if isinstance(self.value, (Path, bytes)):
      return b64encode(self.value.read_bytes() if isinstance(self.value, Path) else self.value).decode()

    if isinstance(self.value, str):
      try:
        if Path(self.value).exists():
          return b64encode(Path(self.value).read_bytes()).decode()
      except Exception:
        # Long base64 string can't be wrapped in Path, so try to treat as base64 string
        pass

      # String might be a file path, but might not exist
      if self.value.split('.')[-1] in ('png', 'jpg', 'jpeg', 'webp'):
        raise ValueError(f'File {self.value} does not exist')

      try:
        # Try to decode to check if it's already base64
        b64decode(self.value)
        return self.value
      except Exception:
        raise ValueError('Invalid image data, expected base64 string or path to image file') from Exception
    

@dataclass
class Message():
    """
    Chat message.
    """

    role: str
    "Assumed role of the message. Response messages has role 'assistant' or 'tool'."

    content: Optional[str] = None
    'Content of the message. Response messages contains message fragments when streaming.'

    thinking: Optional[str] = None
    'Thinking content. Only present when thinking is enabled.'

    images: Optional[list[Image]] = None
    """
    Optional list of image data for multimodal models.

    Valid input types are:

    - `str` or path-like object: path to image file
    - `bytes` or bytes-like object: raw image data

    Valid image formats depend on the model. See the model card for more information.
    """
    
    @dataclass
    class ToolFunction:
        """
        Tool call function.
        """

        name: str
        'Name of the function.'

        arguments: Mapping[str, Any]
        'Arguments of the function.'

    tool_calls: Optional[list[ToolFunction]] = None
    """
    Tools calls to be made by the model.
    """


@dataclass
class ChatResponse(Message):
    """
    Chat response.
    """
    
    model: Optional[str] = None
    'Model used to generate response.'

    created_at: Optional[str] = None
    'Time when the request was created.'

    prompt_eval_count: Optional[int] = None
    'Number of tokens evaluated in the prompt.'

    eval_count: Optional[int] = None
    'Number of tokens evaluated in inference.'


@dataclass
class ChatRequest:
    messages: Optional[list[dict[str, Any]]] = None
    'Messages to chat with.'
    
    model: str = field(default="gpt-oss:20b")
    'Model to use for the chat.'

    think: Optional[bool | Literal['low', 'medium', 'high']] = None
    'Enable thinking mode (for thinking models).'
    
    tools: Optional[list[Callable]] = None
    'Tools to use for the chat.'
    
    num_ctx: int = field(default=1024)
    'Context length for the model.'
    
    temperature: float = field(default=0.7)
    'Sampling temperature for the model.'
    
    format: Optional[str] = None
    'Response format for the model.'