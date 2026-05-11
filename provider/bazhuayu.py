import time
import urllib.parse
from collections.abc import Mapping
from typing import Any

import requests
from werkzeug import Request

from dify_plugin import ToolProvider
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import (
    ToolProviderCredentialValidationError,
    ToolProviderOAuthError,
)

from utils.mcp_client import BazhuayuMcpClient


CLIENT_ID = "DifyMCP"
CLIENT_SECRET = "*"
AUTHORIZATION_URL = "https://identity.bazhuayu.com/connect/authorize"
TOKEN_URL = "https://identity.bazhuayu.com/connect/token"
DEFAULT_SCOPE = "openid profile offline_access"
MCP_SERVER_URL = "https://mcp.bazhuayu.com/"


class BazhuayuProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            client = BazhuayuMcpClient.from_credentials(credentials)
            client.call_tool("search_templates", {"keyword": "test", "limit": 1})
        except Exception as exc:
            raise ToolProviderCredentialValidationError(str(exc)) from exc

    def _oauth_get_authorization_url(
        self,
        redirect_uri: str,
        system_credentials: Mapping[str, Any],
    ) -> str:
        params = {
            "client_id": CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": DEFAULT_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"

    def _oauth_get_credentials(
        self,
        redirect_uri: str,
        system_credentials: Mapping[str, Any],
        request: Request,
    ) -> ToolOAuthCredentials:
        error = request.args.get("error")
        if error:
            description = request.args.get("error_description", "")
            raise ToolProviderOAuthError(f"OAuth authorization failed: {error} {description}")

        code = request.args.get("code")
        if not code:
            raise ToolProviderOAuthError("Authorization code not provided")

        token_data = _post_token(
            TOKEN_URL,
            {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )

        credentials, expires_at = _build_oauth_credentials(
            token_data,
            fallback_mcp_server_url=MCP_SERVER_URL,
        )
        return ToolOAuthCredentials(credentials=credentials, expires_at=expires_at)

    def _oauth_refresh_credentials(
        self,
        redirect_uri: str,
        system_credentials: Mapping[str, Any],
        credentials: Mapping[str, Any],
    ) -> ToolOAuthCredentials:
        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ToolProviderOAuthError("No refresh token available")

        token_data = _post_token(
            TOKEN_URL,
            {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        new_credentials, expires_at = _build_oauth_credentials(
            token_data,
            fallback_refresh_token=str(refresh_token),
            fallback_mcp_server_url=credentials.get("mcp_server_url") or MCP_SERVER_URL,
        )
        return ToolOAuthCredentials(credentials=new_credentials, expires_at=expires_at)


def _required(mapping: Mapping[str, Any], key: str) -> str:
    value = str(mapping.get(key) or "").strip()
    if not value:
        raise ToolProviderOAuthError(f"Missing OAuth client setting: {key}")
    return value


def _post_token(token_url: str, data: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        response.raise_for_status()
        token_data = response.json()
    except requests.RequestException as exc:
        raise ToolProviderOAuthError(f"OAuth token request failed: {exc}") from exc
    except ValueError as exc:
        raise ToolProviderOAuthError("OAuth token response is not valid JSON") from exc

    if token_data.get("error"):
        description = token_data.get("error_description") or token_data["error"]
        raise ToolProviderOAuthError(f"OAuth token request failed: {description}")

    if not token_data.get("access_token"):
        raise ToolProviderOAuthError("OAuth token response does not include access_token")

    return token_data


def _build_oauth_credentials(
    token_data: Mapping[str, Any],
    *,
    fallback_refresh_token: str | None = None,
    fallback_mcp_server_url: Any = None,
) -> tuple[dict[str, Any], int]:
    expires_in = int(token_data.get("expires_in") or 3600)
    expires_at = int(time.time()) + expires_in

    credentials: dict[str, Any] = {
        "access_token": token_data["access_token"],
        "token_type": token_data.get("token_type") or "Bearer",
    }

    refresh_token = token_data.get("refresh_token") or fallback_refresh_token
    if refresh_token:
        credentials["refresh_token"] = refresh_token

    mcp_server_url = str(fallback_mcp_server_url or "").strip()
    if mcp_server_url:
        credentials["mcp_server_url"] = mcp_server_url

    return credentials, expires_at
