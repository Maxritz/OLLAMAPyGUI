# models/model_manager.py
import requests
from threading import Lock

class ModelManager:
    def __init__(self, api_base):
        self.api_base = api_base
        self.loaded_models = set()
        self.loading_lock = Lock()

    async def pull_model(self, model_name):
        try:
            response = await requests.post(f"{self.api_base}/pull", json={"name": model_name})
            return response.status_code == 200, response.text
        except Exception as e:
            return False, str(e)

    async def load_model(self, model_name):
        with self.loading_lock:
            if model_name in self.loaded_models:
                return True, "Model already loaded"
            
            try:
                response = await requests.post(f"{self.api_base}/load", json={"name": model_name})
                if response.status_code == 200:
                    self.loaded_models.add(model_name)
                    return True, "Model loaded successfully"
                return False, response.text
            except Exception as e:
                return False, str(e)

    async def unload_model(self, model_name):
        if model_name in self.loaded_models:
            try:
                # Add actual Ollama API call here when available
                self.loaded_models.remove(model_name)
                return True, "Model unloaded successfully"
            except Exception as e:
                return False, str(e)
        return False, "Model not loaded"