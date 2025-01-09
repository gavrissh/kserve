# Copyright 2023 The KServe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from vllm.entrypoints.openai.protocol import (
    ChatCompletionRequest, 
    ChatCompletionResponse as ChatCompletion,
    ChatCompletionResponseChoice as ChatCompletionChoice,
    ChatCompletionLogProb,
    ChatCompletionLogProbs,
    ChatCompletionStreamResponse as ChatCompletionChunk,
    ChatCompletionResponseStreamChoice as ChunkChoice,
    ChatMessage,
    DeltaMessage as ChoiceDelta,
    CompletionResponse as Completion,
    CompletionResponseChoice as CompletionChoice,
    CompletionLogProbs,
    UsageInfo,
    ChatCompletionLogProbsContent,
    ModelCard as Model,
    ModelList,
)
from vllm.entrypoints.openai.protocol import CompletionRequest, CompletionResponse as Completion
from vllm.entrypoints.openai.protocol import EmbeddingRequest, EmbeddingResponse as Embedding, EmbeddingResponseData
from vllm.entrypoints.chat_utils import ChatCompletionMessageParam

from typing import Optional
from pydantic import BaseModel, Field

class Error(BaseModel):
    code: Optional[str] = Field(...)
    message: str
    param: Optional[str] = Field(...)
    type: str


class ErrorResponse(BaseModel):
    error: Error



# The autogenerated OpenAPI specification doesn't seem to include the base64 encoding option. Add it manually.
class EmbeddingObject(BaseEmbeddingObject):
    embedding: Union[List[float], str]


__all__ = [
    "ChatCompletion",
    "ChatCompletionChoice",
    "ChatCompletionChunk",
    "ChatMessage",
    "ChatCompletionLogProb"
    "ChatCompletionLogProbs",
    "ChoiceDelta",
    "ChunkChoice",
    "Completion",
    "CompletionChoice",
    "ChatCompletionRequest",
    "CompletionRequest",
    "Error",
    "ErrorResponse",
    "CompletionLogProbs",
    "UsageInfo",
    "ChatCompletionMessageParam",
    "ChatCompletionLogProbsContent",
    "Embedding",
    "EmbeddingRequest",
    "EmbeddingResponseData",
    "Model",
    "ModelList",
]
