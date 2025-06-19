import importlib
import inspect
from typing import Dict, Any, List, Type, Callable
from pathlib import Path

class Plugin:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version

    async def initialize(self, framework):
        pass

    async def cleanup(self):
        pass

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}

    async def load_plugin(self, plugin_path: str, framework) -> Plugin:
        try:
            spec = importlib.util.spec_from_file_location("plugin", plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj != Plugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                raise ValueError("No Plugin class found in module")
            
            plugin = plugin_class()
            await plugin.initialize(framework)
            
            self.plugins[plugin.name] = plugin
            print(f"Plugin '{plugin.name}' loaded successfully")
            
            return plugin
            
        except Exception as e:
            print(f"Error loading plugin from {plugin_path}: {e}")
            raise

    async def unload_plugin(self, plugin_name: str):
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            await plugin.cleanup()
            del self.plugins[plugin_name]
            print(f"Plugin '{plugin_name}' unloaded")

    def register_hook(self, hook_name: str, callback: Callable):
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    async def trigger_hook(self, hook_name: str, *args, **kwargs):
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error in hook {hook_name}: {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "class": plugin.__class__.__name__
            }
            for plugin in self.plugins.values()
        ]

    async def load_plugins_from_directory(self, directory: str, framework):
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            return
        
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                await self.load_plugin(str(plugin_file), framework)
            except Exception as e:
                print(f"Failed to load plugin {plugin_file}: {e}")

# Example Plugin
class LoggingPlugin(Plugin):
    def __init__(self):
        super().__init__("logging_plugin", "1.0.0")

    async def initialize(self, framework):
        framework.message_bus.subscribe("*", self.log_message)
        print("Logging plugin initialized")

    async def log_message(self, message):
        print(f"[LOG] {message}")