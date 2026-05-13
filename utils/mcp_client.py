import json
import os
import uuid
from typing import Any

import requests


DEFAULT_MCP_SERVER_URL = "https://mcp.bazhuayu.com/"


class BazhuayuMcpError(RuntimeError):
    pass


class BazhuayuMcpClient:
    def __init__(
        self,
        *,
        server_url: str | None = None,
        api_key: str | None = None,
        access_token: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.server_url = _normalize_url(
            server_url
            or os.getenv("BAZHUAYU_MCP_SERVER_URL")
            or DEFAULT_MCP_SERVER_URL
        )
        self.api_key = api_key
        self.access_token = access_token
        self.timeout = timeout
        self.session_id: str | None = None

    @classmethod
    def from_credentials(cls, credentials: dict[str, Any]) -> "BazhuayuMcpClient":
        return cls(
            server_url=credentials.get("mcp_server_url"),
            api_key=credentials.get("api_key"),
            access_token=credentials.get("access_token"),
        )

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self._ensure_session()
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        }
        response = requests.post(
            self.server_url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._decode_response(response)

    def _ensure_session(self) -> None:
        if self.session_id:
            return

        initialize_payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "bazhuayu-dify-plugin",
                    "version": "0.0.1",
                },
            },
        }
        response = requests.post(
            self.server_url,
            json=initialize_payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        self._decode_response(response)

        session_id = response.headers.get("Mcp-Session-Id")
        if not session_id:
            raise BazhuayuMcpError("MCP initialize response did not include Mcp-Session-Id")
        self.session_id = session_id

        initialized_payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        initialized_response = requests.post(
            self.server_url,
            json=initialized_payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        if initialized_response.status_code >= 400:
            self._decode_response(initialized_response)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _decode_response(self, response: requests.Response) -> dict[str, Any]:
        _prefer_utf8_for_sse(response)
        try:
            data = response.json()
        except ValueError as exc:
            data = _decode_sse_response(response.text)
            if data is None:
                raise BazhuayuMcpError(
                    f"MCP server returned non-JSON response: HTTP {response.status_code}"
                ) from exc

        if response.status_code >= 400:
            message = _extract_error_message(data) or response.text
            raise BazhuayuMcpError(f"MCP server error HTTP {response.status_code}: {message}")

        if "error" in data:
            message = _extract_error_message(data)
            raise BazhuayuMcpError(f"MCP tool call failed: {message}")

        result = data.get("result")
        if not isinstance(result, dict):
            raise BazhuayuMcpError("MCP response does not contain an object result")

        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured

        content = result.get("content")
        return {
            "content": content,
            "raw": result,
        }


def _normalize_url(url: str) -> str:
    value = url.strip()
    if not value:
        return DEFAULT_MCP_SERVER_URL
    return value if value.endswith("/") else f"{value}/"


def _extract_error_message(data: Any) -> str | None:
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if message:
                return str(message)
        if isinstance(error, str):
            return error
        message = data.get("message")
        if message:
            return str(message)
    return None


def _prefer_utf8_for_sse(response: requests.Response) -> None:
    content_type = response.headers.get("Content-Type", "")
    if "text/event-stream" in content_type.lower() and "charset=" not in content_type.lower():
        response.encoding = "utf-8"


def _decode_sse_response(text: str) -> dict[str, Any] | None:
    for event in _iter_sse_events(text):
        payload = event.strip()
        if not payload:
            continue
        try:
            return json.loads(payload, strict=False)
        except ValueError:
            continue
    return None


def _iter_sse_events(text: str) -> list[str]:
    events: list[str] = []
    data_lines: list[str] = []

    def flush() -> None:
        if data_lines:
            events.append("\n".join(data_lines))
            data_lines.clear()

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if line == "":
            flush()
            continue
        if line.startswith("data:"):
            data_lines.append(_sse_field_value(line))
            continue
        if line.startswith(":"):
            continue
        if data_lines and not _is_non_data_sse_field(line):
            data_lines.append(line)

    flush()
    return events


def _sse_field_value(line: str) -> str:
    value = line.removeprefix("data:")
    return value[1:] if value.startswith(" ") else value


def _is_non_data_sse_field(line: str) -> bool:
    field, separator, _ = line.partition(":")
    return bool(separator) and field in {"event", "id", "retry"}
