import contextlib
import json
from base64 import b64decode, b64encode
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from pydantic import (
  BaseModel,
  ByteSize,
  ConfigDict,
  Field,
  model_serializer,
)
from pydantic.json_schema import JsonSchemaValue
from typing_extensions import Annotated, Literal


class SubscriptableBaseModel(BaseModel):
  def __getitem__(self, key: str) -> Any:
    if key in self:
      return getattr(self, key)
    raise KeyError(key)

  def __setitem__(self, key: str, value: Any) -> None:
    setattr(self, key, value)

  def __contains__(self, key: str) -> bool:
    if key in self.model_fields_set:
      return True
    if value := self.__class__.model_fields.get(key):
      return value.default is not None
    return False

  def get(self, key: str, default: Any = None) -> Any:
    return getattr(self, key) if hasattr(self, key) else default


class Options(SubscriptableBaseModel):
  numa: Optional[bool] = None
  num_ctx: Optional[int] = None
  num_batch: Optional[int] = None
  num_gpu: Optional[int] = None
  main_gpu: Optional[int] = None
  low_vram: Optional[bool] = None
  f16_kv: Optional[bool] = None
  logits_all: Optional[bool] = None
  vocab_only: Optional[bool] = None
  use_mmap: Optional[bool] = None
  use_mlock: Optional[bool] = None
  embedding_only: Optional[bool] = None
  num_thread: Optional[int] = None
  num_keep: Optional[int] = None
  seed: Optional[int] = None
  num_predict: Optional[int] = None
  top_k: Optional[int] = None
  top_p: Optional[float] = None
  tfs_z: Optional[float] = None
  typical_p: Optional[float] = None
  repeat_last_n: Optional[int] = None
  temperature: Optional[float] = None
  repeat_penalty: Optional[float] = None
  presence_penalty: Optional[float] = None
  frequency_penalty: Optional[float] = None
  mirostat: Optional[int] = None
  mirostat_tau: Optional[float] = None
  mirostat_eta: Optional[float] = None
  penalize_newline: Optional[bool] = None
  stop: Optional[Sequence[str]] = None


class BaseRequest(SubscriptableBaseModel):
  model: Annotated[str, Field(min_length=1)]


class BaseStreamableRequest(BaseRequest):
  stream: Optional[bool] = None


class BaseGenerateRequest(BaseStreamableRequest):
  options: Optional[Union[Mapping[str, Any], Options]] = None
  format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None
  keep_alive: Optional[Union[float, str]] = None


class Image(BaseModel):
  value: Union[str, bytes, Path]

  @model_serializer
  def serialize_model(self):
    if isinstance(self.value, (Path, bytes)):
      return b64encode(self.value.read_bytes() if isinstance(self.value, Path) else self.value).decode()
    if isinstance(self.value, str):
      try:
        if Path(self.value).exists():
          return b64encode(Path(self.value).read_bytes()).decode()
      except Exception:
        pass
      if self.value.split('.')[-1] in ('png', 'jpg', 'jpeg', 'webp'):
        raise ValueError(f'File {self.value} does not exist')
      try:
        b64decode(self.value)
        return self.value
      except Exception:
        raise ValueError('Invalid image data, expected base64 string or path to image file') from Exception


class GenerateRequest(BaseGenerateRequest):
  prompt: Optional[str] = None
  suffix: Optional[str] = None
  system: Optional[str] = None
  template: Optional[str] = None
  context: Optional[Sequence[int]] = None
  raw: Optional[bool] = None
  images: Optional[Sequence[Image]] = None
  think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None
  logprobs: Optional[bool] = None
  top_logprobs: Optional[int] = None


class BaseGenerateResponse(SubscriptableBaseModel):
  model: Optional[str] = None
  created_at: Optional[str] = None
  done: Optional[bool] = None
  done_reason: Optional[str] = None
  total_duration: Optional[int] = None
  load_duration: Optional[int] = None
  prompt_eval_count: Optional[int] = None
  prompt_eval_duration: Optional[int] = None
  eval_count: Optional[int] = None
  eval_duration: Optional[int] = None


class TokenLogprob(SubscriptableBaseModel):
  token: str
  logprob: float


class Logprob(TokenLogprob):
  top_logprobs: Optional[Sequence[TokenLogprob]] = None


class GenerateResponse(BaseGenerateResponse):
  response: str
  thinking: Optional[str] = None
  context: Optional[Sequence[int]] = None
  logprobs: Optional[Sequence[Logprob]] = None


class Message(SubscriptableBaseModel):
  role: str
  content: Optional[str] = None
  thinking: Optional[str] = None
  images: Optional[Sequence[Image]] = None
  tool_name: Optional[str] = None

  class ToolCall(SubscriptableBaseModel):
    class Function(SubscriptableBaseModel):
      name: str
      arguments: Mapping[str, Any]
    function: Function
  tool_calls: Optional[Sequence[ToolCall]] = None


class Tool(SubscriptableBaseModel):
  type: Optional[str] = 'function'

  class Function(SubscriptableBaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Parameters(SubscriptableBaseModel):
      model_config = ConfigDict(populate_by_name=True)
      type: Optional[Literal['object']] = 'object'
      defs: Optional[Any] = Field(None, alias='$defs')
      items: Optional[Any] = None
      required: Optional[Sequence[str]] = None

      class Property(SubscriptableBaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)

        type: Optional[Union[str, Sequence[str]]] = None
        items: Optional[Any] = None
        description: Optional[str] = None
        enum: Optional[Sequence[Any]] = None

      properties: Optional[Mapping[str, Property]] = None

    parameters: Optional[Parameters] = None
  function: Optional[Function] = None


class ChatRequest(BaseGenerateRequest):
  @model_serializer(mode='wrap')
  def serialize_model(self, nxt):
    output = nxt(self)
    if output.get('tools'):
      for tool in output['tools']:
        if 'function' in tool and 'parameters' in tool['function'] and 'defs' in tool['function']['parameters']:
          tool['function']['parameters']['$defs'] = tool['function']['parameters'].pop('defs')
    return output

  messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None
  tools: Optional[Sequence[Tool]] = None
  think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None
  logprobs: Optional[bool] = None
  top_logprobs: Optional[int] = None


class ChatResponse(BaseGenerateResponse):
  message: Message
  logprobs: Optional[Sequence[Logprob]] = None


class EmbedRequest(BaseRequest):
  input: Union[str, Sequence[str]]
  truncate: Optional[bool] = None
  options: Optional[Union[Mapping[str, Any], Options]] = None
  keep_alive: Optional[Union[float, str]] = None
  dimensions: Optional[int] = None


class EmbedResponse(BaseGenerateResponse):
  embeddings: Sequence[Sequence[float]]


class EmbeddingsRequest(BaseRequest):
  prompt: Optional[str] = None
  options: Optional[Union[Mapping[str, Any], Options]] = None
  keep_alive: Optional[Union[float, str]] = None


class EmbeddingsResponse(SubscriptableBaseModel):
  embedding: Sequence[float]


class PullRequest(BaseStreamableRequest):
  insecure: Optional[bool] = None


class PushRequest(BaseStreamableRequest):
  insecure: Optional[bool] = None


class CreateRequest(BaseStreamableRequest):
  @model_serializer(mode='wrap')
  def serialize_model(self, nxt):
    output = nxt(self)
    if 'from_' in output:
      output['from'] = output.pop('from_')
    return output

  quantize: Optional[str] = None
  from_: Optional[str] = None
  files: Optional[Dict[str, str]] = None
  adapters: Optional[Dict[str, str]] = None
  template: Optional[str] = None
  license: Optional[Union[str, List[str]]] = None
  system: Optional[str] = None
  parameters: Optional[Union[Mapping[str, Any], Options]] = None
  messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None


class ModelDetails(SubscriptableBaseModel):
  parent_model: Optional[str] = None
  format: Optional[str] = None
  family: Optional[str] = None
  families: Optional[Sequence[str]] = None
  parameter_size: Optional[str] = None
  quantization_level: Optional[str] = None


class ListResponse(SubscriptableBaseModel):
  class Model(SubscriptableBaseModel):
    model: Optional[str] = None
    modified_at: Optional[datetime] = None
    digest: Optional[str] = None
    size: Optional[ByteSize] = None
    details: Optional[ModelDetails] = None
  models: Sequence[Model]


class DeleteRequest(BaseRequest):
  pass


class CopyRequest(BaseModel):
  source: str
  destination: str


class StatusResponse(SubscriptableBaseModel):
  status: Optional[str] = None


class ProgressResponse(StatusResponse):
  completed: Optional[int] = None
  total: Optional[int] = None
  digest: Optional[str] = None


class ShowRequest(BaseRequest):
  pass


class ShowResponse(SubscriptableBaseModel):
  modified_at: Optional[datetime] = None
  template: Optional[str] = None
  modelfile: Optional[str] = None
  license: Optional[str] = None
  details: Optional[ModelDetails] = None
  modelinfo: Optional[Mapping[str, Any]] = Field(alias='model_info')
  parameters: Optional[str] = None
  capabilities: Optional[List[str]] = None


class ProcessResponse(SubscriptableBaseModel):
  class Model(SubscriptableBaseModel):
    model: Optional[str] = None
    name: Optional[str] = None
    digest: Optional[str] = None
    expires_at: Optional[datetime] = None
    size: Optional[ByteSize] = None
    size_vram: Optional[ByteSize] = None
    details: Optional[ModelDetails] = None
    context_length: Optional[int] = None
  models: Sequence[Model]


class WebSearchRequest(SubscriptableBaseModel):
  query: str
  max_results: Optional[int] = None


class WebSearchResult(SubscriptableBaseModel):
  content: Optional[str] = None
  title: Optional[str] = None
  url: Optional[str] = None


class WebFetchRequest(SubscriptableBaseModel):
  url: str


class WebSearchResponse(SubscriptableBaseModel):
  results: Sequence[WebSearchResult]


class WebFetchResponse(SubscriptableBaseModel):
  title: Optional[str] = None
  content: Optional[str] = None
  links: Optional[Sequence[str]] = None


class RequestError(Exception):
  def __init__(self, error: str):
    super().__init__(error)
    self.error = error


class ResponseError(Exception):
  def __init__(self, error: str, status_code: int = -1):
    with contextlib.suppress(json.JSONDecodeError):
      error = json.loads(error).get('error', error)
    super().__init__(error)
    self.error = error
    self.status_code = status_code

  def __str__(self) -> str:
    return f'{self.error} (status code: {self.status_code})'
