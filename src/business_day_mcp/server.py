"""business-day-mcp server (stub — implementation via TDD in Wave 3)."""

from fastmcp import FastMCP

mcp: FastMCP = FastMCP("business-day-mcp")


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()
