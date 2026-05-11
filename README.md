# Bazhuayu Dify Plugin

This Dify tool plugin wraps the Bazhuayu Streamable HTTP MCP server and exposes Bazhuayu cloud scraping tools inside Dify.

It supports the core scraping workflow:

1. `search_templates` - find a cloud-runnable scraping template
2. `execute_task` - validate parameters, create a cloud task, and start it
3. `export_data` - check progress and export structured data

It also exposes task management and promotion helpers:

4. `search_tasks` - search existing cloud tasks
5. `start_or_stop_task` - start or stop an existing task
6. `redeem_coupon_code` - redeem a Bazhuayu coupon or promotion code

## How it works

The plugin does not reimplement Bazhuayu scraping logic. It forwards Dify tool calls to the existing Bazhuayu MCP server:

```text
Dify Tool Plugin -> Bazhuayu MCP Server -> Bazhuayu Client API
```

Default MCP endpoint:

```text
https://mcp.bazhuayu.com/
```

You can override it in provider credentials or with:

```env
BAZHUAYU_MCP_SERVER_URL=https://mcp.bazhuayu.com/
```

## Authentication

The plugin supports API key and OAuth credential modes.

### API Key

Configure:

```text
api_key
mcp_server_url
```

The plugin sends:

```http
X-API-Key: <api_key>
```

This reuses the API key path already implemented by the Bazhuayu MCP server.

### OAuth

Click **Add OAuth** in Dify to authorize your Bazhuayu account.

The plugin uses the Bazhuayu OAuth client:

```text
client_id: DifyMCP
client_secret: *
authorization_url: https://identity.bazhuayu.com/connect/authorize
token_url: https://identity.bazhuayu.com/connect/token
scope: openid profile offline_access
```

Dify handles user authorization and token refresh. The plugin then calls the MCP server with:

```http
Authorization: Bearer <access_token>
```

This reuses the Bearer-token path already implemented by the Bazhuayu MCP server.

## Tools

### `search_templates`

Search cloud-runnable Bazhuayu templates.

Typical input:

```json
{
  "keyword": "amazon",
  "limit": 8
}
```

Use `recommendedTemplate.templateName` from the response when calling `execute_task`.

### `execute_task`

Validate parameters, create a cloud task, and start it.

Typical validation input:

```json
{
  "templateName": "amazon-product-scraper",
  "validateOnly": true,
  "parameters": "{\"SearchKeyword\":[\"iphone\"]}"
}
```

Typical execution input:

```json
{
  "templateName": "amazon-product-scraper",
  "parameters": "{\"SearchKeyword\":[\"iphone\"]}"
}
```

`parameters` is a JSON object string. Use the `inputSchema[].field` keys returned by `search_templates` or `validateOnly`.

### `export_data`

Check task progress and export data.

Typical input:

```json
{
  "taskId": "your-task-id",
  "exportFileType": "JSON",
  "previewRows": 5
}
```

Supported export types:

```text
JSON, CSV, EXCEL, HTML, XML
```

### `search_tasks`

Search existing Bazhuayu cloud tasks.

Typical input:

```json
{
  "keyword": "amazon",
  "page": 1,
  "size": 10
}
```

You can also filter by status:

```json
{
  "status": "Running"
}
```

Supported status values:

```text
Running, Stopped, Completed, Failed
```

### `start_or_stop_task`

Start or stop an existing Bazhuayu cloud task.

Typical input:

```json
{
  "taskId": "your-task-id",
  "action": "start"
}
```

Supported actions:

```text
start, stop
```

### `redeem_coupon_code`

Redeem a Bazhuayu coupon or promotion code.

Typical input:

```json
{
  "code": "RESOURCE_TMPL_01"
}
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m main
```

## Package

Install the Dify plugin CLI, then run:

```bash
dify plugin package .
```

The generated `.difypkg` can be submitted to `langgenius/dify-plugins`.
