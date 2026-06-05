# /adversarial-simulation — Red vs Blue Autonomous Adversarial Simulation

> **Skill type:** Advanced Reasoning / Simulation  
> **Source:** studiofarzulla/adversarial-security-agents (red vs blue), ckduy/redamon EvoGraph, Phantom RL (sushaan-k), Ayyub2110/red_team_agent (LangGraph ReAct)  
> **Chains into:** All offensive skills  
> **Chained from:** Complex engagement planning

---

## Purpose

Run a structured adversarial simulation where an AI agent plays both attacker and defender perspectives — identifying the most likely real-world attack paths while predicting defensive responses. Produces more realistic findings than a pure red-team-only perspective.

---

## The Dual-Agent Mental Model

```
RED AGENT (Attacker mindset):
  "What's the fastest path to compromise?"
  "Which vulnerabilities combine for maximum impact?"
  "What would evade detection long enough to succeed?"

BLUE AGENT (Defender mindset):
  "What would the SOC see if RED did that?"
  "What controls are in place at each step?"
  "At which point does this become detectable?"

OUTCOME:
  Findings that reflect REAL risk (not theoretical risk)
  Attack paths that survive compensating controls
  Detection gaps that matter
```

---

## Phase 1: EvoGraph — Evolutionary Attack Graph

```python
class AttackGraph:
    """
    Evolutionary attack graph that adapts based on discovered environment.
    Based on ckduy/redamon EvoGraph approach.
    """
    
    def __init__(self, target: str):
        self.target = target
        self.nodes = {}       # {id: AttackNode}
        self.edges = []       # [(src, dst, technique)]
        self.current_pos = "initial_access"
        self.objectives = ["domain_admin", "data_exfil", "persistence"]
        self.generation = 0
    
    def evolve(self, new_finding: dict):
        """
        Update graph when new information is discovered.
        New findings open new paths, close dead ends.
        """
        self.generation += 1
        
        # Add new node for the finding
        node_id = f"node_{self.generation}"
        self.nodes[node_id] = {
            "type": new_finding["type"],
            "description": new_finding["description"],
            "confidence": new_finding["confidence"],
            "opens_paths": new_finding.get("enables", []),
        }
        
        # Connect to current position
        self.edges.append((self.current_pos, node_id, new_finding.get("technique")))
        
        # Re-evaluate all paths to objectives
        self._recompute_paths()
    
    def get_optimal_path(self) -> list:
        """Find shortest/highest-confidence path to nearest objective."""
        paths = []
        for obj in self.objectives:
            path = self._bfs(self.current_pos, obj)
            if path:
                paths.append({
                    "objective": obj,
                    "path": path,
                    "confidence": self._path_confidence(path),
                    "steps": len(path),
                })
        
        # Sort by: highest confidence × fewest steps
        return sorted(paths, key=lambda p: p["confidence"] / p["steps"], reverse=True)
    
    def _recompute_paths(self):
        """Prune dead ends, update path weights."""
        # Remove nodes with confidence < 0.2
        for node_id, node in list(self.nodes.items()):
            if node["confidence"] < 0.2:
                del self.nodes[node_id]
                self.edges = [(s, d, t) for s, d, t in self.edges
                             if s != node_id and d != node_id]
```

---

## Phase 2: LangGraph ReAct Kill-Chain Agent

```python
"""
ReAct (Reasoning + Acting) agent for kill-chain execution.
Based on Ayyub2110/red_team_agent LangGraph implementation.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated

class AgentState(TypedDict):
    target: str
    phase: str  # recon|exploit|post_exploit|report
    findings: List[dict]
    current_hypothesis: str
    tools_tried: List[str]
    attack_graph: dict
    step_count: int
    max_steps: int

def should_continue(state: AgentState) -> str:
    """Decide: continue, escalate phase, or end."""
    if state["step_count"] >= state["max_steps"]:
        return "end"
    
    phase = state["phase"]
    
    # Check phase completion criteria
    if phase == "recon" and len(state["findings"]) >= 3:
        return "exploit"
    elif phase == "exploit" and any(f["type"] == "rce" for f in state["findings"]):
        return "post_exploit"
    elif phase == "post_exploit" and any(f["type"] == "domain_admin" for f in state["findings"]):
        return "report"
    
    return "continue"

def reason_step(state: AgentState) -> AgentState:
    """Think about what to do next."""
    prompt = f"""
    Current phase: {state['phase']}
    Target: {state['target']}
    Findings so far: {state['findings'][-3:]}  # Last 3 findings
    Tools tried: {state['tools_tried'][-5:]}   # Last 5 tools
    
    Based on the current state, what is the SINGLE BEST action to take next?
    
    Reason step by step:
    1. What do I know for certain?
    2. What gaps exist in my knowledge?
    3. What technique would most likely advance my objective?
    4. What evidence would confirm or deny this hypothesis?
    
    Output: {{"action": "...", "tool": "...", "parameters": {{...}}, "reasoning": "..."}}
    """
    # Call LLM with prompt → structured action
    return update_state_with_reasoning(state, prompt)

# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("reason", reason_step)
workflow.add_node("act", execute_action)
workflow.add_node("observe", process_result)
workflow.add_node("reflect", update_hypothesis)

workflow.set_entry_point("reason")
workflow.add_edge("reason", "act")
workflow.add_edge("act", "observe")
workflow.add_edge("observe", "reflect")
workflow.add_conditional_edges("reflect", should_continue, {
    "continue": "reason",
    "exploit": "reason",    # Continue but phase changed
    "post_exploit": "reason",
    "report": END,
    "end": END,
})

agent = workflow.compile()
```

---

## Phase 3: Adversarial Competition (Red vs Blue)

```python
"""
Autonomous red vs blue simulation.
Based on studiofarzulla/adversarial-security-agents.
"""

class RedBlueSimulation:
    """
    Run red and blue agents against each other.
    Blue agent tries to detect and block; Red tries to evade and succeed.
    """
    
    def __init__(self, target_env: dict):
        self.env = target_env  # Describes the target environment
        self.red_score = 0     # Points for successful attacks
        self.blue_score = 0    # Points for successful detections
        self.timeline = []     # Chronological event log
    
    def red_action(self, technique: str, parameters: dict) -> dict:
        """Red agent performs an attack technique."""
        result = self._simulate_technique(technique, parameters)
        
        # Record action with stealth assessment
        event = {
            "time": len(self.timeline),
            "actor": "red",
            "technique": technique,
            "mitre_id": self._map_to_mitre(technique),
            "success": result["success"],
            "noise_level": result["noise_level"],  # 0-10
            "artifacts_created": result["artifacts"],
        }
        self.timeline.append(event)
        
        if result["success"]:
            self.red_score += result["impact"]
        
        return result
    
    def blue_action(self, alert_type: str) -> dict:
        """Blue agent responds to detection."""
        # Assess what blue can see from the timeline
        recent_events = [e for e in self.timeline[-10:] if e["noise_level"] > 5]
        
        # Can blue agent correlate these into a detected attack?
        detection = self._assess_detection(recent_events, alert_type)
        
        if detection["detected"]:
            self.blue_score += 1
            return {"blocked": True, "confidence": detection["confidence"]}
        
        return {"blocked": False, "confidence": detection["confidence"]}
    
    def run_simulation(self, rounds: int = 20) -> dict:
        """Run a full red vs blue engagement simulation."""
        
        for round_n in range(rounds):
            # Red: choose next technique based on current state
            red_move = self._red_strategy(self.timeline)
            red_result = self.red_action(red_move["technique"], red_move["params"])
            
            # Blue: check for detection
            blue_result = self.blue_action("periodic_check")
            
            if blue_result["blocked"]:
                # Blue detected → red must evade or change technique
                self._adapt_red_strategy("detected")
        
        return {
            "red_score": self.red_score,
            "blue_score": self.blue_score,
            "detection_rate": self.blue_score / rounds,
            "techniques_used": list(set(e["technique"] for e in self.timeline)),
            "timeline": self.timeline,
            "verdict": "RED WIN" if self.red_score > self.blue_score * 3 else "BLUE WIN",
        }
```

---

## Phase 4: Defender Blind Spot Analysis

Based on red vs blue simulation, identify where the blue team is weakest:

```python
def identify_blind_spots(simulation_results: dict) -> list:
    """
    Find attack techniques that consistently evaded detection.
    These represent the real, highest-priority risks.
    """
    timeline = simulation_results["timeline"]
    
    blind_spots = []
    for event in timeline:
        if event["actor"] == "red" and event["success"]:
            # Was this technique detected within 2 events?
            detected = any(
                e["actor"] == "blue" and e.get("target_technique") == event["technique"]
                for e in timeline[event["time"]:event["time"]+2]
            )
            if not detected:
                blind_spots.append({
                    "technique": event["technique"],
                    "mitre_id": event["mitre_id"],
                    "noise_level": event["noise_level"],
                    "times_evaded": sum(1 for e in timeline 
                                       if e["technique"] == event["technique"] 
                                       and e["success"]),
                })
    
    # Deduplicate and sort by: times_evaded DESC, noise_level ASC (quiet + effective = worst)
    return sorted(
        {t["technique"]: t for t in blind_spots}.values(),
        key=lambda x: (x["times_evaded"], -x["noise_level"]),
        reverse=True
    )
```

---

## Simulation Output Template

```
## Red vs Blue Simulation Results — [Target]

### Final Score
Red Agent:  [N] successful techniques | Impact: [LEVEL]
Blue Agent: [N] detections | Detection Rate: [%]

### Techniques That Evaded Detection (Critical Blind Spots)
1. [Technique] (MITRE: T1xxx) — evaded [N] times, noise level [X]/10
   → Blue team has NO detection for this technique
   → Recommend: [specific detection rule]

2. [Technique] (MITRE: T1xxx) — evaded [N] times
   → Detected once out of [N] attempts
   → Recommend: [specific detection improvement]

### Attack Path That Succeeded
[Step 1] → [Step 2] → [Step 3 - objective reached]
Total time to objective: [N] simulated steps
Blue team detected: [Step X] only (too late)

### Defensive Gaps
- No detection for lateral movement via WMI
- No alerting on LSASS memory reads
- No monitoring of certificate template changes (ADCS)
- 15-minute average time to detect unusual outbound traffic
```
