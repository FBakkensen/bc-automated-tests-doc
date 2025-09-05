__all__ = ["ToolConfig"]

def __getattr__(name: str):  # lazy import to avoid hard dependency during lightweight test imports
	if name == "ToolConfig":
		from .config import ToolConfig  # type: ignore
		return ToolConfig
	raise AttributeError(f"module 'pdf2md' has no attribute {name!r}")

def __dir__():  # maintain introspection
	return sorted(list(globals().keys()) + ["ToolConfig"])
