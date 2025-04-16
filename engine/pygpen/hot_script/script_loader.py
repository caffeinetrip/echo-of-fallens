import os
import importlib
import importlib.util
import sys
import inspect
import engine.pygpen as pp

class ScriptLoader(pp.ElementSingleton):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.scripts = {}
        self.script_instances = []
        
    def load_scripts(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print(f"Created scripts directory: {self.path}")
            
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
                            print(f"Loaded script: {script_name}")
                except Exception as e:
                    print(f"Error loading script {script_name}: {e}")
    
    def update(self):
        for script in self.script_instances:
            script.update()