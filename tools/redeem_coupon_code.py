from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.mcp_client import BazhuayuMcpClient
from utils.params import compact_dict


class RedeemCouponCodeTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        args = compact_dict(
            {
                "code": tool_parameters.get("code"),
            }
        )
        result = BazhuayuMcpClient.from_credentials(self.runtime.credentials).call_tool(
            "redeem_coupon_code",
            args,
        )
        yield self.create_json_message(result)
