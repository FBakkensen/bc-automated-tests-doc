__all__ = ["ToolConfig"]


def __getattr__(name: str) -> object:
    """Lazy import to avoid hard dependency during lightweight test imports."""
    if name == "ToolConfig":
        from .config import ToolConfig

        return ToolConfig
    msg_unknown_attr = "unknown attribute"
    raise AttributeError(f"{msg_unknown_attr}: {name!r}")


def __dir__() -> list[str]:
    """Maintain introspection."""
    return sorted([*list(globals().keys()), "ToolConfig"])
