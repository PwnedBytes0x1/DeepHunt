# /per-framework — Planner-Executor-Reflector Agent Cognition

> **Skill type:** Core Reasoning  
> **Source:** LuaN1aoAgent (P-E-R + Causal Graph), RedTeamLLM (IJCAI 2025), Incalmo  
> **Applies to:** All skills — this is the meta-cognitive layer

---

## Purpose

This skill teaches an AI agent *how to think* about offensive security tasks rather than just executing commands. It implements the **P-E-R (Planner-Executor-Reflector)** framework — the most effective reasoning architecture for autonomous penetration testing based on 2025 research.

---

## Why Reasoning Matters

From RedTeamLLM (IJCAI 2025) ablation study:
> "Reasoning improves offensive capability in 80% of use cases while reducing tool calls by 37-68%. The agent performs more analysis before acting, and thus chooses better strategies."

Without structured reasoning, agents:
- Make redundant tool calls (same probe 3 times)
- Get stuck in dead ends without pivoting
- Miss chaining opportunities between findings
- Hallucinate vulnerabilities not backed by evidence
- Surface-scan instead of going deep

---

## The Three Cognitive Roles

### 🧠 Planner (Strategic Brain)

**Responsibility:** Global attack graph awareness, dynamic task planning

**Core behaviors:**
- Model the target as a Directed Acyclic Graph (DAG) of possible attack paths
- Output structured graph operations: `ADD_NODE`, `UPDATE_NODE`, `DEPRECATE_NODE`
- Automatically parallelize independent subtasks based on DAG topology
- When blocked: prune dead ends, generate alternative paths
- Allocate extra steps (`max_steps`) for complex subtasks (blind injection extraction, multi-stage bypass)

**Decision algorithm:**
```
For each discovered service/endpoint:
  1. Identify vulnerability classes applicable to this surface
  2. Estimate confidence of each path (0.0–1.0)
  3. Prioritize by: confidence × impact × exploitability
  4. Add to task graph with dependency edges
  5. Schedule parallelizable branches concurrently
```

**What NOT to do (planning anti-patterns):**
- Don't build a static list — the plan must evolve with findings
- Don't commit to a path before evidence supports it
- Don't skip phases because "it probably isn't vulnerable"
- Don't mark N/A without a tool that verified it

---

### ⚡ Executor (Tactical Brain)

**Responsibility:** Single subtask execution, tool orchestration, result analysis

**Core behaviors:**
- Invoke tools via structured calls (MCP or direct API)
- Compress context intelligently — don't overflow the context window
- Handle tool errors with retry logic and fallbacks
- Preserve hypotheses across context compression steps
- Share high-value findings with parallel subtasks via a shared bulletin board

**Execution loop:**
```
while task_not_complete and budget_remaining:
    1. Read current hypothesis from hypothesis stack
    2. Select best tool for this step
    3. Execute tool, capture full output
    4. Parse output for: findings, new attack surfaces, credentials, errors
    5. Update hypothesis: CONFIRMED / REJECTED / NEEDS_MORE_DATA
    6. If CONFIRMED finding: add to findings.json + capture evidence artifact
    7. If new attack surface found: publish to Planner's bulletin board
    8. If error/dead-end: escalate to Reflector
```

**Tool selection hierarchy (confidence-based):**
```
HIGH confidence (>80%) → Specialized attack tool directly
MEDIUM confidence (50-80%) → Deploy parallel agents for exploration
LOW confidence (<50%) → More recon, try alternatives first
```

---

### 🔍 Reflector (Audit Brain)

**Responsibility:** Task review, failure attribution, quality control, termination

**Core behaviors:**
- L1-L4 failure pattern analysis (prevent repeated mistakes)
- Extract attack intelligence and build knowledge accumulation
- Judge goal achievement vs. task entrapment
- Validate that findings are real (not false positives)
- Detect when the agent is "rubber-stamping" vs. genuinely testing

**Failure attribution levels:**
```
L1 — Tool error (wrong arguments, timeout, missing dependency)
L2 — Technique error (correct tool, wrong approach for this target)
L3 — Strategy error (correct technique, wrong order/context)
L4 — Understanding error (wrong model of the target entirely)
```

**Termination criteria:**
- Goal achieved (all HIR-gated actions resolved, findings documented)
- Budget exhausted (token/time/cost limit reached)
- Task entrapped (cycled through same dead end 3+ times)
- Scope boundary reached (would need to go out of scope to continue)

---

## The Causal Graph: Evidence-Hypothesis-Validation

Never attack based on assumption. Every hypothesis must have explicit prior evidence.

### Graph Structure
```
Evidence Node: {type, source, confidence, artifact_path}
    ↓
Hypothesis Node: {claim, confidence, evidence_refs}
    ↓
Test Node: {tool, parameters, expected_result}
    ↓
Result Node: {outcome: CONFIRMED|REJECTED, evidence_artifact}
```

### Confidence Propagation Rules
```
Initial scan finding → confidence: 0.5
+ Second tool confirms → confidence: 0.8
+ Third tool confirms → confidence: 0.95
+ Manual PoC works → confidence: 1.0 (CONFIRMED)

Only findings at confidence ≥ 0.8 enter the report
Only findings at confidence = 1.0 get PoC attached
```

### Hallucination Prevention
- If no tool output supports a hypothesis → confidence stays at 0
- "I think this might be vulnerable" without evidence → REJECTED
- Tool output must be stored as an artifact before a finding is logged
- CVE must match service version exactly or be manually verified

---

## Dynamic Task Graph Operations

```
ADD_NODE(id, type, target, technique, dependencies, priority)
  → Adds a new test to the attack plan

UPDATE_NODE(id, status, confidence, artifact)
  → Updates a test result

DEPRECATE_NODE(id, reason)
  → Marks a path as a dead end (with reason)

PARALLELIZE(node_ids)
  → Schedules independent nodes for concurrent execution

INJECT_SUBTASK(parent_id, new_node)
  → When a finding opens a new attack surface mid-execution
```

---

## ReAct Pattern (Reason → Act → Observe)

Each step in the execution loop follows:

```
REASON:
  "The nmap scan showed Apache 2.4.49 on port 80. CVE-2021-41773 is a path traversal / RCE vulnerability for exactly this version. Confidence: 0.9 (version match). Next action: test path traversal."

ACT:
  curl -s --path-as-is "http://target/cgi-bin/.%2e/.%2e/etc/passwd"

OBSERVE:
  Response: "root:x:0:0:root:/root:/bin/bash\n..."
  → Path traversal CONFIRMED. Confidence: 1.0.
  → Escalate to RCE test. HIR pause required.

UPDATE:
  findings.json += {id: "CVE-2021-41773", severity: "CRITICAL", evidence: "evidence/apache-path-traversal.txt"}
```

---

## Meta-Cognitive Prompts (Use These During Planning)

When stuck or unsure, ask:
1. **"What do I know for certain?"** — Confirmed findings only
2. **"What do I suspect but haven't proven?"** — Hypotheses with evidence
3. **"What haven't I tested yet?"** — Coverage gaps
4. **"What would a skilled human attacker try next?"** — Reasoning from attacker mindset
5. **"Am I going deep or rubber-stamping?"** — Self-audit
6. **"What's the highest-impact path from my current position?"** — Priority reset

---

## Context Window Management

For long engagements, compress context without losing critical state:

```
PRESERVE (never compress):
  - findings.json (all confirmed findings)
  - current hypothesis stack
  - credentials discovered
  - attack graph (current state)
  - open HIR events

COMPRESS (summarize):
  - Raw tool output (keep findings, discard verbose logs)
  - Failed probe attempts (keep error type, discard full output)
  - Repeated scan results (keep diff, discard duplicates)

OFFLOAD (to external storage):
  - Full scan artifacts (nmap XML, nuclei JSONL)
  - Screenshot files
  - Full HTTP request/response logs
```
