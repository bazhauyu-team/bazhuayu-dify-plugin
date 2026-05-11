from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict


class StartOrStopTaskTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        args = compact_dict(
            {
                "taskId": tool_parameters.get("taskId"),
                "action": tool_parameters.get("action"),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "start_or_stop_task",
            args,
        )
        yield self.create_json_message(result)
