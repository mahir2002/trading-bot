#!/usr/bin/env python3
"""
🔌 Plugin Manager
Handles module loading, dependency resolution, and lifecycle management
"""

import os
import sys
import importlib
import importlib.util
import logging
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import asyncio
import toposort
from dataclasses import dataclass

from .base_module import BaseModule, ModuleStatus, ModulePriority, ModuleInfo
from .event_bus import EventBus

@dataclass
class ModuleLoadResult:
    """Result of module loading operation"""
    success: bool
    module_name: str
    error_message: Optional[str] = None
    module_instance: Optional[BaseModule] = None

class PluginManager:
    """
    Plugin Manager for the unified trading platform
    
    Handles:
    - Module discovery and loading
    - Dependency resolution
    - Lifecycle management
    - Configuration validation
    """
    
    def __init__(self, modules_directory: str, event_bus: EventBus):
        self.modules_directory = Path(modules_directory)
        self.event_bus = event_bus
        self.logger = logging.getLogger("PluginManager")
        
        # Module storage
        self.loaded_modules: Dict[str, BaseModule] = {}
        self.module_classes: Dict[str, Type[BaseModule]] = {}
        self.module_configs: Dict[str, Dict[str, Any]] = {}
        self.module_info: Dict[str, ModuleInfo] = {}
        
        # Dependency tracking
        self.dependency_graph = {}
        self.startup_order = []
        
        # Loading state
        self.loading_in_progress = set()
        
        self.logger.info(f"Plugin Manager initialized with modules directory: {self.modules_directory}")
    
    async def discover_modules(self) -> List[str]:
        """
        Discover available modules in the modules directory
        
        Returns:
            List of discovered module names
        """
        discovered = []
        
        if not self.modules_directory.exists():
            self.logger.warning(f"Modules directory does not exist: {self.modules_directory}")
            return discovered
        
        # Look for Python files and packages
        for item in self.modules_directory.iterdir():
            if item.is_file() and item.suffix == '.py' and not item.name.startswith('__'):
                module_name = item.stem
                discovered.append(module_name)
                self.logger.debug(f"Discovered module file: {module_name}")
                
            elif item.is_dir() and not item.name.startswith('__'):
                # Check if it's a Python package
                if (item / '__init__.py').exists():
                    module_name = item.name
                    discovered.append(module_name)
                    self.logger.debug(f"Discovered module package: {module_name}")
        
        self.logger.info(f"Discovered {len(discovered)} modules: {discovered}")
        return discovered
    
    async def load_module(self, module_name: str, config: Dict[str, Any]) -> ModuleLoadResult:
        """
        Load a single module
        
        Args:
            module_name: Name of the module to load
            config: Configuration for the module
            
        Returns:
            ModuleLoadResult indicating success/failure
        """
        if module_name in self.loading_in_progress:
            return ModuleLoadResult(
                success=False,
                module_name=module_name,
                error_message="Module loading already in progress"
            )
        
        if module_name in self.loaded_modules:
            return ModuleLoadResult(
                success=True,
                module_name=module_name,
                module_instance=self.loaded_modules[module_name]
            )
        
        self.loading_in_progress.add(module_name)
        
        try:
            # Import the module
            module_class = await self._import_module_class(module_name)
            if not module_class:
                raise ImportError(f"Could not import module class for {module_name}")
            
            # Create module instance
            module_instance = module_class(module_name, config)
            
            # Validate module
            if not isinstance(module_instance, BaseModule):
                raise TypeError(f"Module {module_name} does not inherit from BaseModule")
            
            # Get module info
            module_info = module_instance.get_module_info()
            self.module_info[module_name] = module_info
            
            # Validate configuration
            if not module_instance.validate_config(config):
                raise ValueError(f"Invalid configuration for module {module_name}")
            
            # Store references
            self.module_classes[module_name] = module_class
            self.module_configs[module_name] = config
            self.loaded_modules[module_name] = module_instance
            
            # Register with event bus
            self.event_bus.register_module(module_name, module_instance)
            
            self.logger.info(f"Module loaded successfully: {module_name}")
            
            return ModuleLoadResult(
                success=True,
                module_name=module_name,
                module_instance=module_instance
            )
            
        except Exception as e:
            error_msg = f"Failed to load module {module_name}: {e}"
            self.logger.error(error_msg)
            
            return ModuleLoadResult(
                success=False,
                module_name=module_name,
                error_message=error_msg
            )
            
        finally:
            self.loading_in_progress.discard(module_name)
    
    async def _import_module_class(self, module_name: str) -> Optional[Type[BaseModule]]:
        """
        Import the module class from file/package
        
        Args:
            module_name: Name of the module
            
        Returns:
            Module class or None if import failed
        """
        try:
            # Add current directory to Python path for imports
            current_dir = str(Path.cwd())
            path_added = False
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                path_added = True
            
            try:
                # Try to import as file first
                module_file = self.modules_directory / f"{module_name}.py"
                if module_file.exists():
                    spec = importlib.util.spec_from_file_location(module_name, module_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                else:
                    # Try to import as package
                    package_dir = self.modules_directory / module_name
                    if package_dir.exists() and (package_dir / '__init__.py').exists():
                        # Add modules directory to path temporarily
                        sys.path.insert(0, str(self.modules_directory))
                        try:
                            module = importlib.import_module(module_name)
                        finally:
                            sys.path.remove(str(self.modules_directory))
                    else:
                        self.logger.error(f"Module not found: {module_name}")
                        return None
            finally:
                # Remove current directory from path if we added it
                if path_added and current_dir in sys.path:
                    sys.path.remove(current_dir)
            
            # Look for module class (should match module name or have 'Module' suffix)
            # Handle different naming conventions
            title_name = ''.join(word.capitalize() for word in module_name.split('_'))
            possible_names = [
                title_name + 'Module',  # AiModelsModule
                module_name.title() + 'Module',  # Ai_ModelsModule  
                module_name.title(),  # Ai_Models
                module_name.upper() + 'Module',  # AI_MODELSMODULE
                module_name.upper(),  # AI_MODELS
                'Module'
            ]
            
            for class_name in possible_names:
                if hasattr(module, class_name):
                    module_class = getattr(module, class_name)
                    if (isinstance(module_class, type) and 
                        issubclass(module_class, BaseModule)):
                        return module_class
            
            self.logger.error(f"No valid module class found in {module_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error importing module {module_name}: {e}")
            return None
    
    async def resolve_dependencies(self, modules_to_load: List[str]) -> List[str]:
        """
        Resolve module dependencies and return startup order
        
        Args:
            modules_to_load: List of module names to load
            
        Returns:
            List of modules in dependency order
        """
        # Build dependency graph
        dependency_graph = {}
        
        for module_name in modules_to_load:
            if module_name in self.module_info:
                dependencies = self.module_info[module_name].dependencies
            else:
                # Need to temporarily load module to get info
                temp_result = await self._get_module_info(module_name)
                if temp_result:
                    dependencies = temp_result.dependencies
                else:
                    dependencies = []
            
            # Filter dependencies to only include modules we're loading
            filtered_deps = [dep for dep in dependencies if dep in modules_to_load]
            dependency_graph[module_name] = set(filtered_deps)
        
        try:
            # Use topological sort to determine startup order
            sorted_modules = list(toposort.toposort_flatten(dependency_graph))
            self.startup_order = sorted_modules
            
            self.logger.info(f"Dependency resolution complete. Startup order: {sorted_modules}")
            return sorted_modules
            
        except toposort.CircularDependencyError as e:
            self.logger.error(f"Circular dependency detected: {e}")
            raise ValueError(f"Circular dependency in modules: {e}")
    
    async def _get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """Get module info without fully loading the module"""
        try:
            module_class = await self._import_module_class(module_name)
            if module_class:
                # Create temporary instance with empty config
                temp_instance = module_class(module_name, {})
                return temp_instance.get_module_info()
        except Exception as e:
            self.logger.error(f"Error getting module info for {module_name}: {e}")
        
        return None
    
    async def load_modules(self, module_configs: Dict[str, Dict[str, Any]]) -> Dict[str, ModuleLoadResult]:
        """
        Load multiple modules with dependency resolution
        
        Args:
            module_configs: Dictionary of module_name -> config
            
        Returns:
            Dictionary of module_name -> ModuleLoadResult
        """
        results = {}
        modules_to_load = list(module_configs.keys())
        
        try:
            # Resolve dependencies
            startup_order = await self.resolve_dependencies(modules_to_load)
            
            # Load modules in dependency order
            for module_name in startup_order:
                if module_name in module_configs:
                    config = module_configs[module_name]
                    result = await self.load_module(module_name, config)
                    results[module_name] = result
                    
                    if not result.success:
                        self.logger.error(f"Failed to load module {module_name}, stopping load process")
                        break
                else:
                    self.logger.warning(f"No configuration found for module: {module_name}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error during module loading: {e}")
            return results
    
    async def start_modules(self, module_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Start loaded modules
        
        Args:
            module_names: Specific modules to start (None for all loaded)
            
        Returns:
            Dictionary of module_name -> success status
        """
        if module_names is None:
            module_names = list(self.loaded_modules.keys())
        
        results = {}
        
        # Use dependency order if available
        ordered_modules = []
        for name in self.startup_order:
            if name in module_names:
                ordered_modules.append(name)
        
        # Add any remaining modules
        for name in module_names:
            if name not in ordered_modules:
                ordered_modules.append(name)
        
        # Initialize and start each module
        for module_name in ordered_modules:
            if module_name in self.loaded_modules:
                module = self.loaded_modules[module_name]
                
                try:
                    # Check dependencies
                    available_modules = [name for name, mod in self.loaded_modules.items() 
                                       if mod.is_active()]
                    
                    if not module.check_dependencies(available_modules):
                        self.logger.error(f"Dependencies not met for module: {module_name}")
                        results[module_name] = False
                        continue
                    
                    # Initialize
                    module.set_status(ModuleStatus.INITIALIZING)
                    init_success = await module.initialize()
                    
                    if not init_success:
                        module.set_status(ModuleStatus.ERROR, "Initialization failed")
                        results[module_name] = False
                        continue
                    
                    # Start
                    start_success = await module.start()
                    
                    if start_success:
                        module.set_status(ModuleStatus.ACTIVE)
                        results[module_name] = True
                        self.logger.info(f"Module started successfully: {module_name}")
                    else:
                        module.set_status(ModuleStatus.ERROR, "Start failed")
                        results[module_name] = False
                        
                except Exception as e:
                    error_msg = f"Error starting module {module_name}: {e}"
                    self.logger.error(error_msg)
                    module.set_status(ModuleStatus.ERROR, error_msg)
                    results[module_name] = False
        
        return results
    
    async def stop_modules(self, module_names: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Stop loaded modules
        
        Args:
            module_names: Specific modules to stop (None for all loaded)
            
        Returns:
            Dictionary of module_name -> success status
        """
        if module_names is None:
            module_names = list(self.loaded_modules.keys())
        
        results = {}
        
        # Stop in reverse order of dependencies
        stop_order = list(reversed(self.startup_order))
        ordered_modules = []
        
        for name in stop_order:
            if name in module_names:
                ordered_modules.append(name)
        
        # Add any remaining modules
        for name in module_names:
            if name not in ordered_modules:
                ordered_modules.append(name)
        
        # Stop each module
        for module_name in ordered_modules:
            if module_name in self.loaded_modules:
                module = self.loaded_modules[module_name]
                
                try:
                    success = await module.stop()
                    
                    if success:
                        module.set_status(ModuleStatus.INACTIVE)
                        results[module_name] = True
                        self.logger.info(f"Module stopped successfully: {module_name}")
                    else:
                        results[module_name] = False
                        
                except Exception as e:
                    self.logger.error(f"Error stopping module {module_name}: {e}")
                    results[module_name] = False
        
        return results
    
    async def unload_module(self, module_name: str) -> bool:
        """
        Unload a module completely
        
        Args:
            module_name: Name of module to unload
            
        Returns:
            bool: True if successful
        """
        try:
            if module_name in self.loaded_modules:
                module = self.loaded_modules[module_name]
                
                # Stop module if running
                if module.is_active():
                    await module.stop()
                
                # Unregister from event bus
                self.event_bus.unregister_module(module_name)
                
                # Remove from all tracking
                del self.loaded_modules[module_name]
                self.module_classes.pop(module_name, None)
                self.module_configs.pop(module_name, None)
                self.module_info.pop(module_name, None)
                
                self.logger.info(f"Module unloaded: {module_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unloading module {module_name}: {e}")
            return False
    
    def get_module(self, module_name: str) -> Optional[BaseModule]:
        """Get a loaded module by name"""
        return self.loaded_modules.get(module_name)
    
    def get_all_modules(self) -> Dict[str, BaseModule]:
        """Get all loaded modules"""
        return self.loaded_modules.copy()
    
    def get_module_status(self, module_name: str) -> Optional[ModuleStatus]:
        """Get status of a specific module"""
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name].status
        return None
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get overall platform status"""
        total_modules = len(self.loaded_modules)
        active_modules = sum(1 for module in self.loaded_modules.values() 
                           if module.is_active())
        
        module_statuses = {
            name: module.status.value 
            for name, module in self.loaded_modules.items()
        }
        
        return {
            'total_modules': total_modules,
            'active_modules': active_modules,
            'module_statuses': module_statuses,
            'startup_order': self.startup_order,
            'event_bus_stats': self.event_bus.get_statistics()
        } 