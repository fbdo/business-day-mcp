"""business-day-mcp: MCP server for business-day and holiday queries."""

__version__ = "0.1.0"

from business_day_mcp.server import main, mcp

__all__ = ["__version__", "main", "mcp"]
