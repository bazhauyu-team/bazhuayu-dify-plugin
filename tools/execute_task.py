from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict, optional_bool, optional_int, parse_json_object


class ExecuteTaskTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        parameters = parse_json_object(tool_parameters.get("parameters"))
        args = compact_dict(
            {
                "templateName": tool_parameters.get("templateName"),
                "taskName": tool_parameters.get("taskName"),
                "parameters": parameters,
                "targetMaxRows": optional_int(tool_parameters.get("targetMaxRows")),
                "validateOnly": optional_bool(tool_parameters.get("validateOnly")),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "execute_task",
            args,
        )
        yield self.create_json_message(result)
