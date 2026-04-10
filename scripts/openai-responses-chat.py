import os
import platform
import uuid
from dataclasses import dataclass
from typing import Any, Literal, TypeVar, overload

from openai import APIConnectionError, APIStatusError, RateLimitError
from pydantic import BaseModel

from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.openai.responses_serializer import ResponsesAPIMessageSerializer
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar("T", bound=BaseModel)


@dataclass
class ChatOpenAIResponses(ChatOpenAI):
    """
    Responses-API variant of browser-use's OpenAI wrapper.

    This keeps the browser-use integration surface the same while aligning the wire
    protocol with Codex-style providers that only expose `/v1/responses`.
    """

    store: bool | None = False
    truncation: Literal["auto", "disabled"] | None = None
    verbosity: Literal["low", "medium", "high"] | None = None
    codex_compat_mode: bool = False
    codex_originator: str = "codex_cli_rs"
    codex_user_agent: str | None = None
    codex_installation_id: str | None = None
    codex_window_id: str | None = None
    codex_conversation_id: str | None = None

    def _compat_enabled(self) -> bool:
        return self.codex_compat_mode

    def _resolved_conversation_id(self) -> str:
        if not self.codex_conversation_id:
            self.codex_conversation_id = os.getenv("OPENAI_CODEX_CONVERSATION_ID") or str(uuid.uuid4())
        return self.codex_conversation_id

    def _resolved_installation_id(self) -> str:
        if not self.codex_installation_id:
            self.codex_installation_id = os.getenv("OPENAI_CODEX_INSTALLATION_ID") or str(uuid.uuid4())
        return self.codex_installation_id

    def _resolved_window_id(self) -> str:
        if not self.codex_window_id:
            self.codex_window_id = os.getenv("OPENAI_CODEX_WINDOW_ID") or str(uuid.uuid4())
        return self.codex_window_id

    def _resolved_user_agent(self) -> str:
        if self.codex_user_agent:
            return self.codex_user_agent

        system = platform.system() or "Unknown"
        release = platform.release() or "Unknown"
        return f"{self.codex_originator}/0.0.0 ({system} {release}; Codex)"

    def _compat_headers(self) -> dict[str, str]:
        if not self._compat_enabled():
            return {}

        conversation_id = self._resolved_conversation_id()
        return {
            "originator": self.codex_originator,
            "User-Agent": self._resolved_user_agent(),
            "session_id": conversation_id,
            "x-client-request-id": conversation_id,
            "x-codex-window-id": self._resolved_window_id(),
        }

    def _compat_body(self) -> dict[str, Any]:
        if not self._compat_enabled():
            return {}

        return {
            "prompt_cache_key": self._resolved_conversation_id(),
            "client_metadata": {
                "x-codex-installation-id": self._resolved_installation_id(),
            },
        }

    def _request_overrides(self, **kwargs: Any) -> dict[str, Any]:
        overrides: dict[str, Any] = {}

        extra_headers = dict(self._compat_headers())
        caller_headers = kwargs.pop("extra_headers", None) or {}
        extra_headers.update(caller_headers)
        if extra_headers:
            overrides["extra_headers"] = extra_headers

        extra_body = dict(self._compat_body())
        caller_body = kwargs.pop("extra_body", None) or {}
        extra_body.update(caller_body)
        if extra_body:
            overrides["extra_body"] = extra_body

        extra_query = kwargs.pop("extra_query", None)
        if extra_query:
            overrides["extra_query"] = extra_query

        timeout = kwargs.pop("timeout", None)
        if timeout is not None:
            overrides["timeout"] = timeout

        return overrides

    def _build_response_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}

        if self.max_completion_tokens is not None:
            params["max_output_tokens"] = self.max_completion_tokens

        if self.top_p is not None:
            params["top_p"] = self.top_p

        if self.service_tier is not None:
            params["service_tier"] = self.service_tier

        if self.truncation is not None:
            params["truncation"] = self.truncation

        if self.verbosity is not None:
            params["verbosity"] = self.verbosity

        if self.reasoning_models and any(str(m).lower() in str(self.model).lower() for m in self.reasoning_models):
            params["reasoning"] = {"effort": self.reasoning_effort}
        elif self.temperature is not None:
            params["temperature"] = self.temperature

        return params

    def _get_usage(self, response: Any) -> ChatInvokeUsage | None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return None

        input_details = getattr(usage, "input_tokens_details", None)
        return ChatInvokeUsage(
            prompt_tokens=usage.input_tokens,
            prompt_cached_tokens=input_details.cached_tokens if input_details is not None else None,
            prompt_cache_creation_tokens=None,
            prompt_image_tokens=None,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
        )

    def _serialize_messages(self, messages: list[BaseMessage]) -> Any:
        return ResponsesAPIMessageSerializer.serialize_messages(messages)

    @overload
    async def ainvoke(
        self, messages: list[BaseMessage], output_format: None = None, **kwargs: Any
    ) -> ChatInvokeCompletion[str]: ...

    @overload
    async def ainvoke(
        self, messages: list[BaseMessage], output_format: type[T], **kwargs: Any
    ) -> ChatInvokeCompletion[T]: ...

    async def ainvoke(
        self, messages: list[BaseMessage], output_format: type[T] | None = None, **kwargs: Any
    ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
        try:
            input_items = self._serialize_messages(messages)
            model_params = self._build_response_params()
            request_overrides = self._request_overrides(**kwargs)

            if output_format is None:
                response = await self.get_client().responses.create(
                    model=self.model,
                    input=input_items,
                    store=self.store,
                    **model_params,
                    **request_overrides,
                )
                usage = self._get_usage(response)
                stop_reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
                if stop_reason is None and getattr(response, "status", None) == "completed":
                    stop_reason = "end_turn"

                return ChatInvokeCompletion(
                    completion=response.output_text or "",
                    usage=usage,
                    stop_reason=stop_reason,
                )

            if self.dont_force_structured_output:
                response = await self.get_client().responses.create(
                    model=self.model,
                    input=input_items,
                    store=self.store,
                    **model_params,
                    **request_overrides,
                )
                usage = self._get_usage(response)
                completion_text = response.output_text or ""
                parsed = output_format.model_validate_json(completion_text)
                stop_reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
                if stop_reason is None and getattr(response, "status", None) == "completed":
                    stop_reason = "end_turn"

                return ChatInvokeCompletion(
                    completion=parsed,
                    usage=usage,
                    stop_reason=stop_reason,
                )

            response = await self.get_client().responses.parse(
                model=self.model,
                input=input_items,
                text_format=output_format,
                store=self.store,
                **model_params,
                **request_overrides,
            )

            parsed = response.output_parsed
            if parsed is None:
                completion_text = response.output_text or ""
                if not completion_text:
                    raise ModelProviderError(
                        message="Failed to parse structured output from Responses API response",
                        status_code=500,
                        model=self.name,
                    )
                parsed = output_format.model_validate_json(completion_text)

            usage = self._get_usage(response)
            stop_reason = getattr(getattr(response, "incomplete_details", None), "reason", None)
            if stop_reason is None and getattr(response, "status", None) == "completed":
                stop_reason = "end_turn"

            return ChatInvokeCompletion(
                completion=parsed,
                usage=usage,
                stop_reason=stop_reason,
            )

        except ModelProviderError:
            raise
        except RateLimitError as e:
            raise ModelRateLimitError(message=e.message, model=self.name) from e
        except APIConnectionError as e:
            raise ModelProviderError(message=str(e), model=self.name) from e
        except APIStatusError as e:
            raise ModelProviderError(message=e.message, status_code=e.status_code, model=self.name) from e
        except Exception as e:
            raise ModelProviderError(message=str(e), model=self.name) from e
