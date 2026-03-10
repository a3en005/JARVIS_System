import ipaddress
import json
import os
import platform
import sys
import urllib.parse
from hashlib import sha256
from os import PathLike
from pathlib import Path
from typing import (
  Any,
  Callable,
  Dict,
  List,
  Literal,
  Mapping,
  Optional,
  Sequence,
  Type,
  TypeVar,
  Union,
  overload,
)

import anyio
from pydantic.json_schema import JsonSchemaValue

from ollama._utils import convert_function_to_tool

if sys.version_info < (3, 9):
  from typing import AsyncIterator, Iterator
else:
  from collections.abc import AsyncIterator, Iterator

from importlib import metadata

try:
  __version__ = metadata.version('ollama')
except metadata.PackageNotFoundError:
  __version__ = '0.0.0'

import httpx

from ollama._types import (
  ChatRequest,
  ChatResponse,
  CopyRequest,
  CreateRequest,
  DeleteRequest,
  EmbeddingsRequest,
  EmbeddingsResponse,
  EmbedRequest,
  EmbedResponse,
  GenerateRequest,
  GenerateResponse,
  Image,
  ListResponse,
  Message,
  Options,
  ProcessResponse,
  ProgressResponse,
  PullRequest,
  PushRequest,
  ResponseError,
  ShowRequest,
  ShowResponse,
  StatusResponse,
  Tool,
  WebFetchRequest,
  WebFetchResponse,
  WebSearchRequest,
  WebSearchResponse,
)

T = TypeVar('T')


class BaseClient:
  def __init__(
    self,
    client,
    host: Optional[str] = None,
    *,
    follow_redirects: bool = True,
    timeout: Any = None,
    headers: Optional[Mapping[str, str]] = None,
    **kwargs,
  ) -> None:
    headers = {
      k.lower(): v
      for k, v in {
        **(headers or {}),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': f'ollama-python/{__version__} ({platform.machine()} {platform.system().lower()}) Python/{platform.python_version()}',
      }.items()
      if v is not None
    }
    api_key = os.getenv('OLLAMA_API_KEY', None)
    if not headers.get('authorization') and api_key:
      headers['authorization'] = f'Bearer {api_key}'

    self._client = client(
      base_url=_parse_host(host or os.getenv('OLLAMA_HOST')),
      follow_redirects=follow_redirects,
      timeout=timeout,
      headers=headers,
      **kwargs,
    )


CONNECTION_ERROR_MESSAGE = 'Failed to connect to Ollama. Please check that Ollama is downloaded, running and accessible. https://ollama.com/download'


class Client(BaseClient):
  def __init__(self, host: Optional[str] = None, **kwargs) -> None:
    super().__init__(httpx.Client, host, **kwargs)

  def _request_raw(self, *args, **kwargs):
    try:
      r = self._client.request(*args, **kwargs)
      r.raise_for_status()
      return r
    except httpx.HTTPStatusError as e:
      raise ResponseError(e.response.text, e.response.status_code) from None
    except httpx.ConnectError:
      raise ConnectionError(CONNECTION_ERROR_MESSAGE) from None

  @overload
  def _request(
    self,
    cls: Type[T],
    *args,
    stream: Literal[False] = False,
    **kwargs,
  ) -> T: ...

  @overload
  def _request(
    self,
    cls: Type[T],
    *args,
    stream: Literal[True] = True,
    **kwargs,
  ) -> Iterator[T]: ...

  @overload
  def _request(
    self,
    cls: Type[T],
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[T, Iterator[T]]: ...

  def _request(
    self,
    cls: Type[T],
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[T, Iterator[T]]:
    if stream:

      def inner():
        with self._client.stream(*args, **kwargs) as r:
          try:
            r.raise_for_status()
          except httpx.HTTPStatusError as e:
            e.response.read()
            raise ResponseError(e.response.text, e.response.status_code) from None

          for line in r.iter_lines():
            part = json.loads(line)
            if err := part.get('error'):
              raise ResponseError(err)
            yield cls(**part)

      return inner()

    return cls(**self._request_raw(*args, **kwargs).json())

  @overload
  def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    *,
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[False] = False,
    think: Optional[bool] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: bool = False,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> GenerateResponse: ...

  @overload
  def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    *,
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[True] = True,
    think: Optional[bool] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: bool = False,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Iterator[GenerateResponse]: ...

  def generate(
    self,
    model: str = '',
    prompt: Optional[str] = None,
    suffix: Optional[str] = None,
    *,
    system: Optional[str] = None,
    template: Optional[str] = None,
    context: Optional[Sequence[int]] = None,
    stream: bool = False,
    think: Optional[bool] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: Optional[bool] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Union[GenerateResponse, Iterator[GenerateResponse]]:
    return self._request(
      GenerateResponse,
      'POST',
      '/api/generate',
      json=GenerateRequest(
        model=model,
        prompt=prompt,
        suffix=suffix,
        system=system,
        template=template,
        context=context,
        stream=stream,
        think=think,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        raw=raw,
        format=format,
        images=list(_copy_images(images)) if images else None,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: Literal[False] = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> ChatResponse: ...

  @overload
  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: Literal[True] = True,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Iterator[ChatResponse]: ...

  def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: bool = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Union[ChatResponse, Iterator[ChatResponse]]:
    return self._request(
      ChatResponse,
      'POST',
      '/api/chat',
      json=ChatRequest(
        model=model,
        messages=list(_copy_messages(messages)),
        tools=list(_copy_tools(tools)),
        stream=stream,
        think=think,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        format=format,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  def embed(
    self,
    model: str = '',
    input: Union[str, Sequence[str]] = '',
    truncate: Optional[bool] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
    dimensions: Optional[int] = None,
  ) -> EmbedResponse:
    return self._request(
      EmbedResponse,
      'POST',
      '/api/embed',
      json=EmbedRequest(
        model=model,
        input=input,
        truncate=truncate,
        options=options,
        keep_alive=keep_alive,
        dimensions=dimensions,
      ).model_dump(exclude_none=True),
    )

  def embeddings(
    self,
    model: str = '',
    prompt: Optional[str] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> EmbeddingsResponse:
    return self._request(
      EmbeddingsResponse,
      'POST',
      '/api/embeddings',
      json=EmbeddingsRequest(
        model=model,
        prompt=prompt,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
    )

  @overload
  def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> Iterator[ProgressResponse]: ...

  def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: bool = False,
  ) -> Union[ProgressResponse, Iterator[ProgressResponse]]:
    return self._request(
      ProgressResponse,
      'POST',
      '/api/pull',
      json=PullRequest(
        model=model,
        insecure=insecure,
        stream=stream,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> Iterator[ProgressResponse]: ...

  def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: bool = False,
  ) -> Union[ProgressResponse, Iterator[ProgressResponse]]:
    return self._request(
      ProgressResponse,
      'POST',
      '/api/push',
      json=PushRequest(
        model=model,
        insecure=insecure,
        stream=stream,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: Literal[True] = True,
  ) -> Iterator[ProgressResponse]: ...

  def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: bool = False,
  ) -> Union[ProgressResponse, Iterator[ProgressResponse]]:
    return self._request(
      ProgressResponse,
      'POST',
      '/api/create',
      json=CreateRequest(
        model=model,
        stream=stream,
        quantize=quantize,
        from_=from_,
        files=files,
        adapters=adapters,
        license=license,
        template=template,
        system=system,
        parameters=parameters,
        messages=messages,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  def create_blob(self, path: Union[str, Path]) -> str:
    sha256sum = sha256()
    with open(path, 'rb') as r:
      while True:
        chunk = r.read(32 * 1024)
        if not chunk:
          break
        sha256sum.update(chunk)

    digest = f'sha256:{sha256sum.hexdigest()}'

    with open(path, 'rb') as r:
      self._request_raw('POST', f'/api/blobs/{digest}', content=r)

    return digest

  def list(self) -> ListResponse:
    return self._request(
      ListResponse,
      'GET',
      '/api/tags',
    )

  def delete(self, model: str) -> StatusResponse:
    r = self._request_raw(
      'DELETE',
      '/api/delete',
      json=DeleteRequest(
        model=model,
      ).model_dump(exclude_none=True),
    )
    return StatusResponse(
      status='success' if r.status_code == 200 else 'error',
    )

  def copy(self, source: str, destination: str) -> StatusResponse:
    r = self._request_raw(
      'POST',
      '/api/copy',
      json=CopyRequest(
        source=source,
        destination=destination,
      ).model_dump(exclude_none=True),
    )
    return StatusResponse(
      status='success' if r.status_code == 200 else 'error',
    )

  def show(self, model: str) -> ShowResponse:
    return self._request(
      ShowResponse,
      'POST',
      '/api/show',
      json=ShowRequest(
        model=model,
      ).model_dump(exclude_none=True),
    )

  def ps(self) -> ProcessResponse:
    return self._request(
      ProcessResponse,
      'GET',
      '/api/ps',
    )

  def web_search(self, query: str, max_results: int = 3) -> WebSearchResponse:
    if not self._client.headers.get('authorization', '').startswith('Bearer '):
      raise ValueError('Authorization header with Bearer token is required for web search')

    return self._request(
      WebSearchResponse,
      'POST',
      'https://ollama.com/api/web_search',
      json=WebSearchRequest(
        query=query,
        max_results=max_results,
      ).model_dump(exclude_none=True),
    )

  def web_fetch(self, url: str) -> WebFetchResponse:
    if not self._client.headers.get('authorization', '').startswith('Bearer '):
      raise ValueError('Authorization header with Bearer token is required for web fetch')

    return self._request(
      WebFetchResponse,
      'POST',
      'https://ollama.com/api/web_fetch',
      json=WebFetchRequest(
        url=url,
      ).model_dump(exclude_none=True),
    )


class AsyncClient(BaseClient):
  def __init__(self, host: Optional[str] = None, **kwargs) -> None:
    super().__init__(httpx.AsyncClient, host, **kwargs)

  async def _request_raw(self, *args, **kwargs):
    try:
      r = await self._client.request(*args, **kwargs)
      r.raise_for_status()
      return r
    except httpx.HTTPStatusError as e:
      raise ResponseError(e.response.text, e.response.status_code) from None
    except httpx.ConnectError:
      raise ConnectionError(CONNECTION_ERROR_MESSAGE) from None

  @overload
  async def _request(
    self,
    cls: Type[T],
    *args,
    stream: Literal[False] = False,
    **kwargs,
  ) -> T: ...

  @overload
  async def _request(
    self,
    cls: Type[T],
    *args,
    stream: Literal[True] = True,
    **kwargs,
  ) -> AsyncIterator[T]: ...

  @overload
  async def _request(
    self,
    cls: Type[T],
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[T, AsyncIterator[T]]: ...

  async def _request(
    self,
    cls: Type[T],
    *args,
    stream: bool = False,
    **kwargs,
  ) -> Union[T, AsyncIterator[T]]:
    if stream:

      async def inner():
        async with self._client.stream(*args, **kwargs) as r:
          try:
            r.raise_for_status()
          except httpx.HTTPStatusError as e:
            await e.response.aread()
            raise ResponseError(e.response.text, e.response.status_code) from None

          async for line in r.aiter_lines():
            part = json.loads(line)
            if err := part.get('error'):
              raise ResponseError(err)
            yield cls(**part)

      return inner()

    return cls(**(await self._request_raw(*args, **kwargs)).json())

  async def web_search(self, query: str, max_results: int = 3) -> WebSearchResponse:
    return await self._request(
      WebSearchResponse,
      'POST',
      'https://ollama.com/api/web_search',
      json=WebSearchRequest(
        query=query,
        max_results=max_results,
      ).model_dump(exclude_none=True),
    )

  async def web_fetch(self, url: str) -> WebFetchResponse:
    return await self._request(
      WebFetchResponse,
      'POST',
      'https://ollama.com/api/web_fetch',
      json=WebFetchRequest(
        url=url,
      ).model_dump(exclude_none=True),
    )

  @overload
  async def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    *,
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[False] = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: bool = False,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> GenerateResponse: ...

  @overload
  async def generate(
    self,
    model: str = '',
    prompt: str = '',
    suffix: str = '',
    *,
    system: str = '',
    template: str = '',
    context: Optional[Sequence[int]] = None,
    stream: Literal[True] = True,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: bool = False,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> AsyncIterator[GenerateResponse]: ...

  async def generate(
    self,
    model: str = '',
    prompt: Optional[str] = None,
    suffix: Optional[str] = None,
    *,
    system: Optional[str] = None,
    template: Optional[str] = None,
    context: Optional[Sequence[int]] = None,
    stream: bool = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    raw: Optional[bool] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    images: Optional[Sequence[Union[str, bytes, Image]]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Union[GenerateResponse, AsyncIterator[GenerateResponse]]:
    return await self._request(
      GenerateResponse,
      'POST',
      '/api/generate',
      json=GenerateRequest(
        model=model,
        prompt=prompt,
        suffix=suffix,
        system=system,
        template=template,
        context=context,
        stream=stream,
        think=think,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        raw=raw,
        format=format,
        images=list(_copy_images(images)) if images else None,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  async def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: Literal[False] = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> ChatResponse: ...

  @overload
  async def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: Literal[True] = True,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> AsyncIterator[ChatResponse]: ...

  async def chat(
    self,
    model: str = '',
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None,
    stream: bool = False,
    think: Optional[Union[bool, Literal['low', 'medium', 'high']]] = None,
    logprobs: Optional[bool] = None,
    top_logprobs: Optional[int] = None,
    format: Optional[Union[Literal['', 'json'], JsonSchemaValue]] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> Union[ChatResponse, AsyncIterator[ChatResponse]]:
    return await self._request(
      ChatResponse,
      'POST',
      '/api/chat',
      json=ChatRequest(
        model=model,
        messages=list(_copy_messages(messages)),
        tools=list(_copy_tools(tools)),
        stream=stream,
        think=think,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        format=format,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  async def embed(
    self,
    model: str = '',
    input: Union[str, Sequence[str]] = '',
    truncate: Optional[bool] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
    dimensions: Optional[int] = None,
  ) -> EmbedResponse:
    return await self._request(
      EmbedResponse,
      'POST',
      '/api/embed',
      json=EmbedRequest(
        model=model,
        input=input,
        truncate=truncate,
        options=options,
        keep_alive=keep_alive,
        dimensions=dimensions,
      ).model_dump(exclude_none=True),
    )

  async def embeddings(
    self,
    model: str = '',
    prompt: Optional[str] = None,
    options: Optional[Union[Mapping[str, Any], Options]] = None,
    keep_alive: Optional[Union[float, str]] = None,
  ) -> EmbeddingsResponse:
    return await self._request(
      EmbeddingsResponse,
      'POST',
      '/api/embeddings',
      json=EmbeddingsRequest(
        model=model,
        prompt=prompt,
        options=options,
        keep_alive=keep_alive,
      ).model_dump(exclude_none=True),
    )

  @overload
  async def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  async def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> AsyncIterator[ProgressResponse]: ...

  async def pull(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: bool = False,
  ) -> Union[ProgressResponse, AsyncIterator[ProgressResponse]]:
    return await self._request(
      ProgressResponse,
      'POST',
      '/api/pull',
      json=PullRequest(
        model=model,
        insecure=insecure,
        stream=stream,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  async def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  async def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: Literal[True] = True,
  ) -> AsyncIterator[ProgressResponse]: ...

  async def push(
    self,
    model: str,
    *,
    insecure: bool = False,
    stream: bool = False,
  ) -> Union[ProgressResponse, AsyncIterator[ProgressResponse]]:
    return await self._request(
      ProgressResponse,
      'POST',
      '/api/push',
      json=PushRequest(
        model=model,
        insecure=insecure,
        stream=stream,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  @overload
  async def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: Literal[False] = False,
  ) -> ProgressResponse: ...

  @overload
  async def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: Literal[True] = True,
  ) -> AsyncIterator[ProgressResponse]: ...

  async def create(
    self,
    model: str,
    quantize: Optional[str] = None,
    from_: Optional[str] = None,
    files: Optional[Dict[str, str]] = None,
    adapters: Optional[Dict[str, str]] = None,
    template: Optional[str] = None,
    license: Optional[Union[str, List[str]]] = None,
    system: Optional[str] = None,
    parameters: Optional[Union[Mapping[str, Any], Options]] = None,
    messages: Optional[Sequence[Union[Mapping[str, Any], Message]]] = None,
    *,
    stream: bool = False,
  ) -> Union[ProgressResponse, AsyncIterator[ProgressResponse]]:
    return await self._request(
      ProgressResponse,
      'POST',
      '/api/create',
      json=CreateRequest(
        model=model,
        stream=stream,
        quantize=quantize,
        from_=from_,
        files=files,
        adapters=adapters,
        license=license,
        template=template,
        system=system,
        parameters=parameters,
        messages=messages,
      ).model_dump(exclude_none=True),
      stream=stream,
    )

  async def create_blob(self, path: Union[str, Path]) -> str:
    sha256sum = sha256()
    async with await anyio.open_file(path, 'rb') as r:
      while True:
        chunk = await r.read(32 * 1024)
        if not chunk:
          break
        sha256sum.update(chunk)

    digest = f'sha256:{sha256sum.hexdigest()}'

    async def upload_bytes():
      async with await anyio.open_file(path, 'rb') as r:
        while True:
          chunk = await r.read(32 * 1024)
          if not chunk:
            break
          yield chunk

    await self._request_raw('POST', f'/api/blobs/{digest}', content=upload_bytes())

    return digest

  async def list(self) -> ListResponse:
    return await self._request(
      ListResponse,
      'GET',
      '/api/tags',
    )

  async def delete(self, model: str) -> StatusResponse:
    r = await self._request_raw(
      'DELETE',
      '/api/delete',
      json=DeleteRequest(
        model=model,
      ).model_dump(exclude_none=True),
    )
    return StatusResponse(
      status='success' if r.status_code == 200 else 'error',
    )

  async def copy(self, source: str, destination: str) -> StatusResponse:
    r = await self._request_raw(
      'POST',
      '/api/copy',
      json=CopyRequest(
        source=source,
        destination=destination,
      ).model_dump(exclude_none=True),
    )
    return StatusResponse(
      status='success' if r.status_code == 200 else 'error',
    )

  async def show(self, model: str) -> ShowResponse:
    return await self._request(
      ShowResponse,
      'POST',
      '/api/show',
      json=ShowRequest(
        model=model,
      ).model_dump(exclude_none=True),
    )

  async def ps(self) -> ProcessResponse:
    return await self._request(
      ProcessResponse,
      'GET',
      '/api/ps',
    )


def _copy_images(images: Optional[Sequence[Union[Image, Any]]]) -> Iterator[Image]:
  for image in images or []:
    yield image if isinstance(image, Image) else Image(value=image)


def _copy_messages(messages: Optional[Sequence[Union[Mapping[str, Any], Message]]]) -> Iterator[Message]:
  for message in messages or []:
    yield Message.model_validate(
      {k: list(_copy_images(v)) if k == 'images' else v for k, v in dict(message).items() if v},
    )


def _copy_tools(tools: Optional[Sequence[Union[Mapping[str, Any], Tool, Callable]]] = None) -> Iterator[Tool]:
  for unprocessed_tool in tools or []:
    yield convert_function_to_tool(unprocessed_tool) if callable(unprocessed_tool) else Tool.model_validate(unprocessed_tool)


def _as_path(s: Optional[Union[str, PathLike]]) -> Union[Path, None]:
  if isinstance(s, (str, Path)):
    try:
      if (p := Path(s)).exists():
        return p
    except Exception:
      pass
  return None


def _parse_host(host: Optional[str]) -> str:
  host, port = host or '', 11434
  scheme, _, hostport = host.partition('://')
  if not hostport:
    scheme, hostport = 'http', host
  elif scheme == 'http':
    port = 80
  elif scheme == 'https':
    port = 443

  split = urllib.parse.urlsplit(f'{scheme}://{hostport}')
  host = split.hostname or '127.0.0.1'
  port = split.port or port

  try:
    if isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address):
      host = f'[{host}]'
  except ValueError:
    pass

  if path := split.path.strip('/'):
    return f'{scheme}://{host}:{port}/{path}'

  return f'{scheme}://{host}:{port}'

