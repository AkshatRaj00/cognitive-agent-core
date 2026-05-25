"""plugins package — dynamic plugin loading for cognitive-agent-core."""

from .plugin_loader import LoadedPlugin, PluginLoader, PluginMeta

__all__ = ["PluginLoader", "PluginMeta", "LoadedPlugin"]
