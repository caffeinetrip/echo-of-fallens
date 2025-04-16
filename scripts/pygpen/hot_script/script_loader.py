# scripts/systems/script_loader.py
import os
import importlib
import importlib.util
import sys
import inspect

import scripts.pygpen as pp

class ScriptLoader(pp.ElementSingleton):
    def __init__(self, path):
        super().__init__()
        
        self.path = path
        
        self.scripts = {}
        self.script_instances = []
        
    def load_scripts(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f"Створено директорію для скриптів: {self.path}")
            
        for filename in os.listdir(self.path):
            if filename.endswith('.py') and not filename.startswith('__'):
                script_path = os.path.join(self.path, filename)
                script_name = filename[:-3]
                
                try:
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[script_name] = module
                    spec.loader.exec_module(module)
                    
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and hasattr(obj, 'is_game_script') and obj.is_game_script:
                            script_instance = obj()
                            self.script_instances.append(script_instance)
                            self.scripts[script_name] = script_instance
                            print(f"Завантажено скрипт: {script_name}")
                            
                except Exception as e:
                    print(f"Помилка при завантаженні скрипта {script_name}: {e}")
    
    def update(self):
        """Викликається в кожному циклі гри"""
        for script in self.script_instances:
            if hasattr(script, 'update'):
                script.update()