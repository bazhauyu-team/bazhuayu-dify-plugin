from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict, optional_int, parse_json_array


class SearchTasksTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        args = compact_dict(
            {
                "page": optional_int(tool_parameters.get("page")),
                "size": optional_int(tool_parameters.get("size")),
                "keyword": tool_parameters.get("keyword"),
                "status": tool_parameters.get("status"),
                "taskIds": parse_json_array(tool_parameters.get("taskIds")),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "search_tasks",
            args,
        )
        yield self.create_json_message(result)
