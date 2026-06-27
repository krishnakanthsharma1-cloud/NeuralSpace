# federated_learning.py
import json
import os
import hashlib
import time
from typing import List, Dict, Any
import numpy as np

class FederatedLearning:
    """
    Real Federated Learning using FedAvg (Federated Averaging).
    Nodes send weight updates (not raw code) to the aggregator.
    """
    
    def __init__(self, aggregator_url: str = None, node_id: str = None):
        self.aggregator_url = aggregator_url or os.environ.get("NEURALSPACE_AGGREGATOR", "http://localhost:8000")
        self.node_id = node_id or hashlib.md5(os.urandom(32)).hexdigest()[:16]
        self.global_model_version = 0
        self.local_updates = []
        
    def extract_weights(self, model) -> Dict[str, List[float]]:
        """
        Extract weights from a PyTorch model as a dictionary of lists.
        """
        weights = {}
        for name, param in model.named_parameters():
            weights[name] = param.detach().cpu().numpy().tolist()
        return weights
    
    def compute_weight_delta(self, old_weights: Dict, new_weights: Dict) -> Dict:
        """
        Compute the difference between old and new weights.
        This is what gets sent to the aggregator.
        """
        delta = {}
        for name in old_weights:
            old = np.array(old_weights[name])
            new = np.array(new_weights[name])
            delta[name] = (new - old).tolist()
        return delta
    
    def apply_weight_delta(self, model, delta: Dict) -> None:
        """
        Apply a weight delta to a PyTorch model.
        """
        for name, param in model.named_parameters():
            if name in delta:
                # Convert back to tensor and add the delta
                delta_tensor = np.array(delta[name])
                param.data += torch.tensor(delta_tensor, dtype=param.dtype)
    
    def send_update(self, delta: Dict, model_version: int) -> bool:
        """
        Send a weight update to the aggregator.
        """
        try:
            import requests
            payload = {
                "node_id": self.node_id,
                "delta": delta,
                "model_version": model_version,
                "timestamp": time.time()
            }
            response = requests.post(
                f"{self.aggregator_url}/federated/update",
                json=payload,
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                self.global_model_version = result.get("new_version", model_version)
                return True
        except Exception as e:
            print(f"[!] Federated update failed: {e}")
        return False
    
    def fetch_global_model(self) -> Dict:
        """
        Fetch the latest global model from the aggregator.
        """
        try:
            import requests
            response = requests.get(
                f"{self.aggregator_url}/federated/global",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[!] Fetch global model failed: {e}")
        return {}
    
    def sync(self, model, model_version: int) -> Dict:
        """
        Full sync: send local updates and fetch the global model.
        """
        # Extract current weights
        current_weights = self.extract_weights(model)
        
        # Compute delta from last sync
        if hasattr(self, '_last_weights'):
            delta = self.compute_weight_delta(self._last_weights, current_weights)
        else:
            delta = {}
        
        # Send update
        success = self.send_update(delta, model_version)
        
        # Store current weights for next sync
        self._last_weights = current_weights
        
        # Fetch global model
        global_data = self.fetch_global_model()
        
        return {
            "success": success,
            "global_version": global_data.get("version", model_version),
            "global_weights": global_data.get("weights", {})
        }