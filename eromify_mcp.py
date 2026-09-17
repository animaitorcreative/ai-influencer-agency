"""Minimal Streamable HTTP MCP client for the Eromify integration."""

from __future__ import annotations

import json
import os
from typing import Any

import requests


class EromifyMCPError(RuntimeError):
    """Raised when Eromify MCP returns a protocol or transport error."""


class EromifyMCPClient:
    def __init__(self, url: str, token: str = "", timeout: int = 30):
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self._request_id = 0
        self.session_id: str | None = None

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _decode_response(self, response: requests.Response) -> dict[str, Any]:
        response.raise_for_status()
        session_id = response.headers.get("Mcp-Session-Id")
        if session_id:
            self.session_id = session_id

        if not response.content:
            return {}
        content_type = response.headers.get("Content-Type", "")
        if "text/event-stream" not in content_type:
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise EromifyMCPError("Eromify MCP returned a non-object response.")

        messages: list[dict[str, Any]] = []
        event_data: list[str] = []
        for line in response.text.splitlines():
            if line.startswith("data:"):
                event_data.append(line[5:].strip())
            elif not line and event_data:
                messages.append(json.loads("\n".join(event_data)))
                event_data = []
        if event_data:
            messages.append(json.loads("\n".join(event_data)))
        if not messages:
            raise EromifyMCPError("Eromify MCP returned an empty event stream.")
        return messages[-1]

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = dict(self.headers)
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        response = self.session.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        result = self._decode_response(response)
        if "error" in result:
            error = result["error"]
            raise EromifyMCPError(
                f"{error.get('code', 'unknown')}: {error.get('message', error)}"
            )
        return result

    def initialize(self) -> dict[str, Any]:
        result = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "ai-influencer-agency", "version": "1.0.0"},
                },
            }
        )
        self._post(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            }
        )
        return result.get("result", result)

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/list",
                "params": {},
            }
        )
        return result.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        result = self._post(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        return result.get("result", result)


def configured_client() -> EromifyMCPClient:
    return EromifyMCPClient(
        os.getenv("EROMIFY_MCP_URL", "https://api.eromify.com/mcp"),
        os.getenv("EROMIFY_MCP_TOKEN", ""),
    )
