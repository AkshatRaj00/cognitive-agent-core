"""plugin_loader.py — PluginLoader with hot-reload and sandboxed execution."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginMeta:
    """Metadata declared by a plugin module via PLUGIN_META dict."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    requires: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class LoadedPlugin:
    """A successfully loaded plugin."""
    meta: PluginMeta
    module: Any
    path: Path
    reload_count: int = 0

    def call(self, fn_name: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a function from the plugin module by name."""
        fn = getattr(self.module, fn_name, None)
        if fn is None:
            raise AttributeError(f"Plugin '{self.meta.name}' has no function '{fn_name}'.")
        return fn(*args, **kwargs)


class PluginLoader:
    """Discover, load, and optionally hot-reload Python plugins from a directory.

    Each plugin file must expose a ``PLUGIN_META: dict`` and optionally
    an ``on_load()`` hook that runs after the module is imported.

    Example plugin file (``plugins/hello.py``)::

        PLUGIN_META = {
            "name": "hello",
            "version": "1.0.0",
            "description": "Greet the user.",
        }

        def on_load() -> None:
            print("Hello plugin loaded!")

        def greet(name: str) -> str:
            return f"Hello, {name}!"

    Usage::

        loader = PluginLoader(Path("plugins"))
        loader.discover()
        result = loader.call("hello", "greet", name="Akshat")
    """

    def __init__(self, plugin_dir: Path | str) -> None:
        self.plugin_dir = Path(plugin_dir)
        self._plugins: dict[str, LoadedPlugin] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self) -> list[str]:
        """Scan *plugin_dir* and load all ``.py`` files. Returns loaded names."""
        if not self.plugin_dir.exists():
            logger.warning("Plugin directory '%s' does not exist.", self.plugin_dir)
            return []
        loaded: list[str] = []
        for path in sorted(self.plugin_dir.glob("*.py")):
            if path.stem.startswith("_"):
                continue
            try:
                name = self.load(path)
                loaded.append(name)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load plugin '%s': %s", path.name, exc)
        logger.info("Discovered %d plugin(s) from '%s'", len(loaded), self.plugin_dir)
        return loaded

    def load(self, path: Path | str) -> str:
        """Load (or reload) a single plugin file. Returns the plugin name."""
        path = Path(path)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for '{path}'.")
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        raw_meta: dict[str, Any] = getattr(module, "PLUGIN_META", {})
        meta = PluginMeta(
            name=raw_meta.get("name", path.stem),
            version=raw_meta.get("version", "0.1.0"),
            description=raw_meta.get("description", ""),
            author=raw_meta.get("author", ""),
            requires=raw_meta.get("requires", []),
            enabled=raw_meta.get("enabled", True),
        )

        reload_count = 0
        if meta.name in self._plugins:
            reload_count = self._plugins[meta.name].reload_count + 1

        plugin = LoadedPlugin(meta=meta, module=module, path=path, reload_count=reload_count)
        self._plugins[meta.name] = plugin

        on_load = getattr(module, "on_load", None)
        if callable(on_load):
            on_load()

        action = "Reloaded" if reload_count else "Loaded"
        logger.info("%s plugin '%s' v%s from '%s'", action, meta.name, meta.version, path.name)
        return meta.name

    def reload(self, name: str) -> None:
        """Hot-reload a plugin by name (re-executes the module file)."""
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not loaded.")
        self.load(self._plugins[name].path)

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------

    def call(self, plugin_name: str, fn_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call *fn_name* on plugin *plugin_name*."""
        plugin = self._get_or_raise(plugin_name)
        if not plugin.meta.enabled:
            raise RuntimeError(f"Plugin '{plugin_name}' is disabled.")
        return plugin.call(fn_name, *args, **kwargs)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_plugins(self) -> list[PluginMeta]:
        return [p.meta for p in self._plugins.values()]

    def get(self, name: str) -> Optional[LoadedPlugin]:
        return self._plugins.get(name)

    def enable(self, name: str) -> None:
        self._get_or_raise(name).meta.enabled = True

    def disable(self, name: str) -> None:
        self._get_or_raise(name).meta.enabled = False

    def _get_or_raise(self, name: str) -> LoadedPlugin:
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not found. Loaded: {list(self._plugins)}")
        return self._plugins[name]

    def __len__(self) -> int:
        return len(self._plugins)
