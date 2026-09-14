"""
AbleBridge++ MCP Server Tools Package.

This package contains all the tools for controlling Ableton Live via MCP.
"""

from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Callable] = {}
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_module(self, module: Any):
        """
        Register all tools from a module.
        
        Args:
            module: Module containing tool functions
        """
        # Look for tool functions in the module
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, '_tool_metadata'):
                self._tools[attr_name] = attr
                self._tool_metadata[attr_name] = attr._tool_metadata
    
    def register_tool(self, name: str, func: Callable, metadata: Optional[Dict[str, Any]] = None):
        """
        Register a single tool.
        
        Args:
            name: Tool name
            func: Tool function
            metadata: Optional metadata for the tool
        """
        self._tools[name] = func
        if metadata:
            self._tool_metadata[name] = metadata
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool function or None if not found
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools.
        
        Returns:
            List of tool definitions
        """
        tools = []
        for name, func in self._tools.items():
            tool_def = {
                'name': name,
                'description': func.__doc__ or f"Execute {name}",
                'inputSchema': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
            
            # Add metadata if available
            if name in self._tool_metadata:
                metadata = self._tool_metadata[name]
                if 'description' in metadata:
                    tool_def['description'] = metadata['description']
                if 'inputSchema' in metadata:
                    tool_def['inputSchema'] = metadata['inputSchema']
            
            tools.append(tool_def)
        
        return tools
    
    @property
    def tool_count(self) -> int:
        """Get the number of registered tools."""
        return len(self._tools)


def tool(name: str, description: str = "", input_schema: Optional[Dict[str, Any]] = None, **kwargs):
    """
    Decorator to mark a function as an MCP tool.
    
    Args:
        name: Tool name
        description: Tool description
        input_schema: Input schema for the tool
        **kwargs: Accepts ``inputSchema`` as an alias for ``input_schema``
            (the ported tool modules use camelCase).
    """
    if input_schema is None and 'inputSchema' in kwargs:
        input_schema = kwargs['inputSchema']
    def decorator(func: Callable):
        func._tool_metadata = {
            'name': name,
            'description': description or func.__doc__ or "",
            'inputSchema': input_schema or {
                'type': 'object',
                'properties': {},
                'required': []
            }
        }
        return func
    return decorator
