# Bazhuayu Dify Plugin

This Dify tool plugin wraps the Bazhuayu Streamable HTTP MCP server and exposes a stable 3-tool scraping workflow inside Dify:

1. `search_templates`
2. `execute_task`
3. `export_data`

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

The plugin supports both credential modes.

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

Use the default OAuth client in Dify.

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
