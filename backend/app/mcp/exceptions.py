class MCPException(Exception):
    """Base exception for all MCP-related errors."""
    pass


class MCPConnectionError(MCPException):
    """Raised when establishing or communicating over an MCP connection fails."""
    pass


class MCPToolNotFoundError(MCPException):
    """Raised when an requested MCP tool cannot be found or is inactive."""
    pass


class MCPAuthorizationError(MCPException):
    """Raised when an agent attempts to execute an unauthorized MCP tool."""
    pass


class MCPExecutionError(MCPException):
    """Raised when an MCP tool invocation returns an error or fails."""
    pass


class MCPSecurityError(MCPException):
    """Raised when a command or transport violates MCP security policies."""
    pass
