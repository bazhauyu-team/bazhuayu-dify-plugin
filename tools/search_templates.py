from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict, optional_int


class SearchTemplatesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        args = compact_dict(
            {
                "keyword": tool_parameters.get("keyword"),
                "id": optional_int(tool_parameters.get("id")),
                "slug": tool_parameters.get("slug"),
                "page": optional_int(tool_parameters.get("page")),
                "limit": optional_int(tool_parameters.get("limit")),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "search_templates",
            args,
        )
        yield self.create_json_message(result)
