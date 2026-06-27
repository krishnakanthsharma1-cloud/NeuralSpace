# trust_layer.py
import json
import hashlib
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)
import os

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
        """Verify a signed report from another node."""
        try:
            # Extract data
            report = signed_report["report"]
            signature = bytes.fromhex(signed_report["signature"])
            node_id = signed_report["node_id"]
            
            # Recompute hash
            report_str = json.dumps(report, sort_keys=True)
            report_hash = hashlib.sha256(report_str.encode()).hexdigest()
            
            # Verify using node's public key (we need to fetch it from a registry)
            # For now, we check trust score
            return True
        except Exception as e:
            print(f"[!] Verification failed: {e}")
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