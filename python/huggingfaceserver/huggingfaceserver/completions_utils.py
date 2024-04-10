# Copyright 2024 The KServe Authors.
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

import asyncio
from http import HTTPStatus
from typing import Dict, List, Optional, Union
from vllm.engine.async_llm_engine import AsyncLLMEngine
from kserve.protocol.rest.openai.types.openapi import (
    CreateCompletionRequest,
    ErrorResponse,
    Error,
    Logprobs,
)
from vllm.transformers_utils.tokenizer import get_tokenizer
from vllm.sequence import Logprob


class OpenAIServing:

    def __init__(self, engine: AsyncLLMEngine, served_model: str):
        self.engine = engine
        self.served_model = served_model

        self.max_model_len = 0
        self.tokenizer = None

        try:
            event_loop = asyncio.get_running_loop()
        except RuntimeError:
            event_loop = None

        if (
            event_loop is not None and event_loop.is_running()
        ):  # If the current is instanced by Ray Serve, there is already a running event loop
            event_loop.create_task(self._post_init())
        else:  # When using single vLLM without engine_use_ray
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._post_init())
            loop.close()

    async def _post_init(self):
        engine_model_config = await self.engine.get_model_config()
        self.max_model_len = engine_model_config.max_model_len

        # A separate tokenizer to map token IDs to strings.
        self.tokenizer = get_tokenizer(
            engine_model_config.tokenizer,
            tokenizer_mode=engine_model_config.tokenizer_mode,
            trust_remote_code=engine_model_config.trust_remote_code,
        )

    def create_error_response(
        self,
        message: str,
        err_type: str = "BadRequestError",
        status_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> ErrorResponse:

        error = Error(
            message=message, type=err_type, param="", code=str(status_code.value)
        )
        return ErrorResponse(error=error)

    def create_streaming_error_response(
        self,
        message: str,
        err_type: str = "BadRequestError",
        status_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> ErrorResponse:
        return self.create_error_response(
            message=message, err_type=err_type, status_code=status_code
        )

    async def _check_model(self, request) -> Optional[ErrorResponse]:
        if request.model == self.served_model:
            return
        return self.create_error_response(
            message=f"The model `{request.model}` does not exist.",
            err_type="NotFoundError",
            status_code=HTTPStatus.NOT_FOUND,
        )

    def _validate_prompt_and_tokenize(
        self,
        request: Union[CreateCompletionRequest],
        prompt: Optional[str] = None,
        prompt_ids: Optional[List[int]] = None,
    ) -> List[int]:
        if not (prompt or prompt_ids):
            raise ValueError("Either prompt or prompt_ids should be provided.")
        if prompt and prompt_ids:
            raise ValueError("Only one of prompt or prompt_ids should be provided.")

        input_ids = (
            prompt_ids if prompt_ids is not None else self.tokenizer(prompt).input_ids
        )
        token_num = len(input_ids)

        if request.max_tokens is None:
            request.max_tokens = self.max_model_len - token_num

        if token_num + request.max_tokens > self.max_model_len:
            raise ValueError(
                f"This model's maximum context length is "
                f"{self.max_model_len} tokens. However, you requested "
                f"{request.max_tokens + token_num} tokens "
                f"({token_num} in the messages, "
                f"{request.max_tokens} in the completion). "
                f"Please reduce the length of the messages or completion.",
            )
        else:
            return input_ids

    def _create_logprobs(
        self,
        token_ids: List[int],
        top_logprobs: Optional[List[Optional[Dict[int, Logprob]]]] = None,
        num_output_top_logprobs: Optional[int] = None,
        initial_text_offset: int = 0,
    ) -> Logprobs:
        """Create OpenAI-style logprobs."""
        logprobs = Logprobs()
        last_token_len = 0
        if num_output_top_logprobs:
            logprobs.top_logprobs = []
        for i, token_id in enumerate(token_ids):
            step_top_logprobs = top_logprobs[i]
            if step_top_logprobs is not None:
                token_logprob = step_top_logprobs[token_id].logprob
            else:
                token_logprob = None
            token = step_top_logprobs[token_id].decoded_token
            logprobs.tokens.append(token)
            logprobs.token_logprobs.append(token_logprob)
            if len(logprobs.text_offset) == 0:
                logprobs.text_offset.append(initial_text_offset)
            else:
                logprobs.text_offset.append(logprobs.text_offset[-1] + last_token_len)
            last_token_len = len(token)

            if num_output_top_logprobs:
                logprobs.top_logprobs.append(
                    {p.decoded_token: p.logprob for i, p in step_top_logprobs.items()}
                    if step_top_logprobs
                    else None
                )
        return logprobs