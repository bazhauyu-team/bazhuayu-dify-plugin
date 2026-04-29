from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict, optional_int


class ExportDataTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        args = compact_dict(
            {
                "taskId": tool_parameters.get("taskId"),
                "exportFileType": tool_parameters.get("exportFileType"),
                "previewRows": optional_int(tool_parameters.get("previewRows")),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "export_data",
            args,
        )
        yield self.create_json_message(result)
