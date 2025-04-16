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

        self.RED = '\033[91m'
        self.GREEN = '\033[92m'
        self.YELLOW = '\033[93m'
        self.RESET = '\033[0m'

    def colored_print(self, message, color):
        print(f"{color}{message}{self.RESET}")
        
    def load_scripts(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            self.colored_print(f"Created scripts directory: {self.path}", self.YELLOW)
            
        for filename in os.listdir(self.path):
            if filename.endswith('.py') and not filename.startswith('__'):
                script_path = os.path.join(self.path, filename)
                script_name = filename[:-3]
                
                try:
                    spec = importlib.util.spec_from_file_location(script_name, script_path)
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[script_name] = module
                    spec.loader.exec_module(module)
                    
                    script_loaded = False
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and hasattr(obj, 'is_game_script') and obj.is_game_script:
                            script_instance = obj()
                            setattr(script_instance, 'e', self.e)
                            self.script_instances.append(script_instance)
                            self.scripts[script_name] = script_instance
                            script_loaded = True
                    
                    if script_loaded:
                        self.colored_print(f"Loaded script: {script_name}", self.GREEN)
                    else:
                        self.colored_print(f"No game scripts found in {script_name}", self.YELLOW)
                        
                except Exception as e:
                    self.colored_print(f"Error loading script {script_name}: {e}", self.RED)

    def update(self):
        for script in self.script_instances:
            script.update()