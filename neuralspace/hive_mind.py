# hive_mind.py
import time
from collections import defaultdict

class HiveMind:
    """
    A collective intelligence system where multiple agents (nodes)
    communicate and form consensus on threats.
    """
    
    def __init__(self, consensus_threshold=0.7):
        self.consensus_threshold = consensus_threshold
        self.agent_votes = defaultdict(list)
        self.consensus_history = []
    
    def register_agent(self, agent_id):
        """Register a new agent in the hive mind."""
        self.agent_votes[agent_id] = []
        print(f"[*] Hive Mind: Agent {agent_id} registered.")
    
    def submit_vote(self, agent_id, threat_score, confidence):
        """
        An agent submits a vote on whether a file is a threat.
        threat_score: 0.0 to 1.0 (higher = more threatening)
        confidence: 0.0 to 1.0 (how confident the agent is)
        """
        self.agent_votes[agent_id].append({
            "threat_score": threat_score,
            "confidence": confidence,
            "timestamp": time.time()
        })
        # Keep only last 100 votes per agent
        if len(self.agent_votes[agent_id]) > 100:
            self.agent_votes[agent_id].pop(0)
    
    def get_consensus(self, agent_ids=None):
        """
        Calculate consensus among all registered agents or a subset.
        Returns a consensus score and a decision (THREAT / SAFE).
        """
        if agent_ids is None:
            agent_ids = list(self.agent_votes.keys())
        
        if not agent_ids:
            return {"decision": "UNKNOWN", "consensus": 0.0, "reason": "No agents"}
        
        # Collect the most recent vote from each agent
        votes = []
        for agent_id in agent_ids:
            if self.agent_votes[agent_id]:
                latest = self.agent_votes[agent_id][-1]
                votes.append(latest["threat_score"] * latest["confidence"])
        
        if not votes:
            return {"decision": "UNKNOWN", "consensus": 0.0, "reason": "No votes"}
        
        consensus_score = sum(votes) / len(votes)
        decision = "THREAT" if consensus_score >= self.consensus_threshold else "SAFE"
        
        self.consensus_history.append({
            "timestamp": time.time(),
            "agent_count": len(votes),
            "consensus_score": consensus_score,
            "decision": decision
        })
        
        return {
            "decision": decision,
            "consensus": consensus_score,
            "agent_count": len(votes),
            "threshold": self.consensus_threshold
        }
    
    def get_agent_trust(self, agent_id):
        """Calculate the trustworthiness of an agent based on its voting history."""
        if agent_id not in self.agent_votes or not self.agent_votes[agent_id]:
            return 0.5
        votes = self.agent_votes[agent_id]
        avg_confidence = sum(v["confidence"] for v in votes) / len(votes)
        return min(1.0, avg_confidence)
    
    def to_dict(self):
        return {
            "consensus_threshold": self.consensus_threshold,
            "agent_count": len(self.agent_votes),
            "consensus_history": self.consensus_history[-10:]
        }