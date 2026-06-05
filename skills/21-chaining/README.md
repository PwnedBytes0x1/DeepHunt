# 21. Chaining Methodology & Attack Chains

Field manuals for vulnerability chaining. Chaining transforms low-impact bugs into high-impact exploits by combining multiple vulnerabilities.

| File | Topic | Focus |
|------|-------|-------|
| [chaining-methodology.md](./chaining-methodology.md) | Chaining Methodology | When and how to look for chains |
| [common-attack-chains.md](./common-attack-chains.md) | Common Attack Chains | Examples of successful bug combinations |

## The Power of 1 + 1 = 5

In bug bounty and penetration testing, a single bug might be "Low" severity. However, when chained with another "Low" or "Medium" bug, the result is often a "High" or "Critical" vulnerability.

### Core Principles
1. **Source to Sink**: Trace user input from one vulnerability (the source) to the execution point of another (the sink).
2. **Context Switching**: Use one bug to change the context (e.g., from an unauthenticated user to an authenticated one).
3. **Data Exfiltration**: Combine a blind vulnerability with an out-of-band (OOB) technique.
4. **Impact Escalation**: Turn information disclosure into an active attack.
