# MADERA MCP - LLM CONTEXT INDEX
# Auto-read by Claude - Optimized for LLM parsing

project:
  name: "Madera MCP Tools"
  type: "MCP Server for AI-Powered Document Processing"
  stack: "FastMCP + Python 3.12 + PostgreSQL + MinIO + Multi-AI"
  version: "0.1.0"
  repo: "https://github.com/mussonking/Madera.tools"

---

# DOCUMENTATION ROUTING

when_working_on:
  mcp_server:
    read: "@.claude/MCP-SERVER.yaml"
    contains: ["FastMCP architecture", "Tool registration", "Server lifecycle", "stdio mode"]
    golden_rule: "All tools inherit BaseTool, register via registry.py"
    key_files:
      server: {path: "madera/mcp/server.py", lines: 53, purpose: "Entry point"}
      registry: {path: "madera/mcp/registry.py", lines: 131, purpose: "Auto-discovery"}
      base: {path: "madera/mcp/tools/base.py", lines: 127, purpose: "BaseTool class"}

  tools:
    read: "@.claude/TOOLS.yaml"
    contains: ["74 tools across 8 categories", "Tool signatures", "Return formats"]
    golden_rule: "New tool = new file in category folder + register in registry.py"

  web_ui:
    read: "@.claude/WEB-UI.yaml"
    contains: ["FastAPI routes", "Jinja2 templates", "Training interface"]
    key_files:
      app: {path: "madera/web/app.py", purpose: "FastAPI app"}
      routes: {path: "madera/web/routes/", purpose: "API + Dashboard + Training"}

  database:
    read: "@.claude/DATABASE.yaml"
    contains: ["AsyncPG", "Alembic migrations", "ToolExecution logging"]

  storage:
    read: "@.claude/STORAGE.yaml"
    contains: ["MinIO client", "Presigned URLs", "File download/upload"]

  patterns:
    read: "@.claude/PATTERNS.yaml"

  mistakes:
    read: "@.claude/GOTCHAS.yaml"

---

# CORE CONCEPTS

mcp_server:
  framework: "FastMCP (mcp.server.fastmcp)"
  transport: "stdio"
  init: "server.py → init_mcp_server() → registry.register_all_tools()"

tool_result:
  format: |
    {
      "success": bool,
      "data": {...},
      "error": str | null,
      "confidence": 0.0-1.0,
      "execution_time_ms": int,
      "hints": {...}  # For HINTS tools only
    }

tool_categories:
  hints: {count: 7, purpose: "Document pre-analysis for AI"}
  pdf: {count: 5, purpose: "PDF manipulation"}
  text: {count: 4, purpose: "Text extraction"}
  normalization: {count: 6, purpose: "Data cleaning"}
  financial: {count: 5, purpose: "Mortgage calculations"}
  validation: {count: 5, purpose: "Data validation"}
  advanced: {count: 8, purpose: "Advanced PDF ops"}
  visual: {count: 34, purpose: "Browser automation"}

---

# CRITICAL RULES (NEVER VIOLATE)

tool_rules:
  1: {always: "Inherit from BaseTool", never: "Standalone functions"}
  2: {always: "Return ToolResult", never: "Raw dict/values"}
  3: {always: "Use async def _execute()", never: "Sync methods"}
  4: {always: "Register in registry.py", never: "Direct import in server.py"}
  5: {always: "Graceful degradation (return error)", never: "Raise exceptions to client"}
  6: {always: "Use self.minio.download_from_presigned()", never: "Direct HTTP requests"}
  7: {always: "Log via logger", never: "print() statements"}

server_rules:
  1: {critical: "Suppress stdout during tool registration", reason: "MCP stdio mode"}
  2: {critical: "NullHandler for logging", reason: "stderr breaks MCP protocol"}
  3: {always: "mcp_server.run() for stdio", never: "Custom event loops"}

---

# QUICK TASKS

add_tool:
  steps:
    - "Create file in madera/mcp/tools/{category}/{tool_name}.py"
    - "Inherit BaseTool, implement _execute()"
    - "Add register(mcp_server) function"
    - "Add entry in registry.py under correct category"
    - "Test with: python -m madera.mcp.server"
  template: |
    from madera.mcp.tools.base import BaseTool, ToolResult

    class MyTool(BaseTool):
        def __init__(self):
            super().__init__()
            self.tool_class = "my_category"

        async def _execute(self, param: str) -> ToolResult:
            # Implementation
            return ToolResult(success=True, data={...}, confidence=0.95)

    def register(mcp_server):
        tool = MyTool()
        @mcp_server.tool()
        async def my_tool_name(param: str) -> dict:
            result = await tool.execute(param=param)
            return result.model_dump()

run_server:
  dev: "python -m madera.mcp.server"
  docker: "docker compose up -d"
  test: "pytest tests/"

---

# TOOL SIGNATURES (QUICK REF)

hints:
  detect_blank_pages: "(presigned_url) → blank_pages[], confidence_per_page"
  detect_id_card_sides: "(presigned_url) → id_cards[], groupings[]"
  identify_cra_document_type: "(presigned_url) → documents[], type, issuer"
  detect_tax_form_type: "(presigned_url) → tax_forms[], form_type, year"
  detect_document_boundaries: "(presigned_url) → split_points[], document_ranges[]"
  detect_fiscal_year: "(presigned_url) → fiscal_years{}, most_common_year"
  assess_image_quality: "(presigned_url) → pages{}, quality_score, needs_preprocessing"

pdf:
  count_pages: "(presigned_url) → page_count"
  extract_page: "(presigned_url, page_number) → output_path"
  split_pdf: "(presigned_url, page_ranges) → output_files[]"
  merge_pdfs: "(presigned_urls[]) → output_path, total_pages"
  rotate_page: "(presigned_url, page_number, degrees) → output_path"

financial:
  calculate_gds_tds: "(annual_income, mortgage_payment, property_tax, heating, ...) → gds_ratio, tds_ratio, qualified"
  calculate_ltv: "(loan_amount, property_value) → ltv_ratio, needs_cmhc"
  estimate_monthly_payment: "(principal, annual_rate, amortization_years) → monthly_payment"

validation:
  validate_sin: "(sin) → is_valid, formatted_sin"
  validate_postal_code: "(postal_code, country?) → is_valid, formatted"
  validate_phone: "(phone, country?) → is_valid, formatted_phone"
  validate_email: "(email) → is_valid, normalized_email"

---

# ENV VARS

required:
  db: "DATABASE_URL=postgresql+asyncpg://madera_user:madera_pass@localhost/madera_db"
  minio: {endpoint: "MINIO_ENDPOINT", keys: "MINIO_ACCESS_KEY/SECRET_KEY", bucket: "MINIO_BUCKET"}
  ai: {gemini: "GEMINI_API_KEY", claude: "ANTHROPIC_API_KEY", openai: "OPENAI_API_KEY"}
  app: {env: "ENVIRONMENT", debug: "DEBUG"}

optional:
  redis: "REDIS_URL=redis://localhost:6379/0"
  logging: "LOG_TOOL_EXECUTIONS=true"
  tesseract: "TESSERACT_CMD=/usr/bin/tesseract"

---

# DEV COMMANDS

server:
  mcp: "python -m madera.mcp.server"
  web: "uvicorn madera.web.app:app --reload --port 8004"

docker:
  up: "docker compose up -d"
  logs: "docker compose logs -f"
  down: "docker compose down"

db:
  migrate: "alembic upgrade head"
  revision: "alembic revision --autogenerate -m 'msg'"

test:
  all: "pytest tests/"
  hints: "pytest tests/test_hints_tools.py"
  mcp: "pytest tests/test_mcp_server.py"

---

# FILE STRUCTURE

paths:
  mcp_core: "madera/mcp/"
  tools: "madera/mcp/tools/{category}/"
  web: "madera/web/"
  config: "madera/config.py"
  storage: "madera/storage/"
  training: "madera/training/"

key_files:
  server: {path: "madera/mcp/server.py", purpose: "MCP entry point"}
  registry: {path: "madera/mcp/registry.py", purpose: "Tool auto-discovery"}
  base_tool: {path: "madera/mcp/tools/base.py", purpose: "BaseTool + ToolResult"}
  config: {path: "madera/config.py", purpose: "Pydantic Settings"}
  minio: {path: "madera/storage/minio_client.py", purpose: "MinIO client"}
  database: {path: "madera/database.py", purpose: "AsyncPG + SQLAlchemy"}

---

# ARCHITECTURE

```
Claude/AI Client
    ↓ stdio (MCP protocol)
FastMCP Server (madera/mcp/server.py)
    ↓ register_all_tools()
Tool Registry (madera/mcp/registry.py)
    ↓ auto-import
Tools (madera/mcp/tools/{category}/*.py)
    ↓↓
MinIO (presigned URLs) + PostgreSQL (logging)
```

---

# NAVIGATION

when_stuck:
  mcp_server: "@.claude/MCP-SERVER.yaml"
  tools: "@.claude/TOOLS.yaml"
  web_ui: "@.claude/WEB-UI.yaml"
  database: "@.claude/DATABASE.yaml"
  storage: "@.claude/STORAGE.yaml"
  patterns: "@.claude/PATTERNS.yaml"
  mistakes: "@.claude/GOTCHAS.yaml"

---

# METADATA

purpose: "LLM context index - auto-read"
optimization: "Structured YAML for LLM parsing"
update: "On architectural changes"
details: "In referenced YAML files"

# END
