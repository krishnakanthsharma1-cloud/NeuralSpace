# trust_layer.py
import json
import hashlib
import time
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
    load_pem_public_key,
    load_pem_private_key
)

# --- SIMPLE KEY REGISTRY (Public Key Infrastructure) ---
# In production, this would be a database. For now, it's a local file.
KEY_REGISTRY_PATH = "trust_registry.json"

def load_registry():
    """Load the public key registry from disk."""
    if os.path.exists(KEY_REGISTRY_PATH):
        with open(KEY_REGISTRY_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_registry(registry):
    """Save the public key registry to disk."""
    with open(KEY_REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=4)

class TrustNode:
    """
    A node in the NeuralSpace trust network.
    Each node has a unique identity and can sign/verify reports.
    """
    
    def __init__(self, node_id=None):
        if node_id is None:
            node_id = hashlib.md5(os.urandom(32)).hexdigest()[:16]
        self.node_id = node_id
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.trust_score = 1.0
        self.reputation_history = []
        self.verified_reports = 0
        self.false_reports = 0
        
        # Register this node's public key in the registry
        registry = load_registry()
        if node_id not in registry:
            registry[node_id] = self.public_key.public_bytes(
                Encoding.PEM,
                PublicFormat.SubjectPublicKeyInfo
            ).decode()
            save_registry(registry)
            print(f"[*] Trust Node {node_id[:8]} registered in key registry.")
    
    def sign_report(self, report):
        """Sign a threat report with the node's private key."""
        report_str = json.dumps(report, sort_keys=True)
        report_hash = hashlib.sha256(report_str.encode()).hexdigest()
        
        signature = self.private_key.sign(
            report_hash.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return {
            "report": report,
            "signature": signature.hex(),
            "node_id": self.node_id,
            "timestamp": time.time()
        }
    
    def verify_report(self, signed_report):
        """
        Verify a signed report from another node.
        Returns True if the signature is valid and the node is trusted.
        """
        try:
            # Extract data
            report = signed_report["report"]
            signature = bytes.fromhex(signed_report["signature"])
            node_id = signed_report["node_id"]
            
            # Load the node's public key from the registry
            registry = load_registry()
            if node_id not in registry:
                print(f"[!] Node {node_id[:8]} not registered in key registry.")
                self.update_trust(node_id, False)
                return False
            
            # Load the public key
            public_key = load_pem_public_key(registry[node_id].encode())
            
            # Recompute hash
            report_str = json.dumps(report, sort_keys=True)
            report_hash = hashlib.sha256(report_str.encode()).hexdigest()
            
            # Verify the signature
            public_key.verify(
                signature,
                report_hash.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # If we get here, the signature is valid
            self.update_trust(node_id, True)
            return True
            
        except Exception as e:
            print(f"[!] Verification failed: {e}")
            self.update_trust(node_id, False)
            return False
    
    def get_public_key_pem(self):
        """Export public key in PEM format for sharing."""
        return self.public_key.public_bytes(
            Encoding.PEM,
            PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def update_trust(self, node_id, report_verified):
        """Update trust score based on report accuracy."""
        if report_verified:
            self.verified_reports += 1
            trust_delta = 0.05
        else:
            self.false_reports += 1
            trust_delta = -0.2
        
        # Find or create node entry
        for node in self.reputation_history:
            if node["node_id"] == node_id:
                node["trust_score"] = max(0.1, min(1.0, node["trust_score"] + trust_delta))
                return
        
        # New node
        initial_score = 0.5 + trust_delta
        self.reputation_history.append({
            "node_id": node_id,
            "trust_score": max(0.1, min(1.0, initial_score))
        })
    
    def get_trust_score(self, node_id):
        """Get the trust score of another node."""
        for node in self.reputation_history:
            if node["node_id"] == node_id:
                return node["trust_score"]
        return 0.5  # Unknown nodes start neutral
    
    def to_dict(self):
        return {
            "node_id": self.node_id,
            "trust_score": self.trust_score,
            "verified_reports": self.verified_reports,
            "false_reports": self.false_reports,
            "reputation_history": self.reputation_history
        }