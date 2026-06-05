---
name: Chaining Methodology
category: chaining
version: "1.0"
author: "PwnedBytes0x1"
description: "When and how to test for vulnerability chaining"
tags:
  - methodology
  - chaining
  - escalation
---

# Vulnerability Chaining Methodology

Chaining is the art of combining multiple vulnerabilities to achieve a higher impact than any single vulnerability could on its own.

## 1. When to Test for Chaining

You should consider chaining whenever you encounter the following scenarios:

### A. The "So What?" Bug
When you find a bug that has minimal impact on its own (e.g., self-XSS, path disclosure, or low-privilege info leak), ask yourself: "What can I do with this information/access?"

### B. The "Incomplete" Exploit
When you have a vulnerability that is blocked by a security control (e.g., a WAF blocking specific characters in an injection, or a CSRF token protecting a sensitive action).

### C. The "Entry Point" Discovery
When you discover an internal service or endpoint that is not directly reachable but could be accessed through another vulnerability (like SSRF).

## 2. How to Identify Chaining Opportunities

Follow these steps to find potential chains:

### Step 1: Mapping Inputs and Outputs
Trace where the data from one vulnerability goes. If a vulnerability allows you to control a value that is later used in another part of the application, that's a potential chain.

### Step 2: Identifying Gaps in Security Controls
Look for areas where one vulnerability can bypass a protection meant for another. For example:
- Can an Open Redirect bypass a domain whitelist for SSRF?
- Can a Path Traversal bypass a filter for local file inclusion?

### Step 3: Privilege Escalation
Think about how a low-privilege vulnerability can grant you the access needed for a high-privilege vulnerability.

## 3. Systematic Chaining Framework

| Stage | Action |
|-------|--------|
| **Identify** | Find "Low" or "Medium" severity bugs. |
| **Pivot** | Determine if the bug provides new information (IPs, paths, tokens). |
| **Combine** | Use the new info/access to reach a previously unreachable "Sink". |
| **Escalate** | Demonstrate the combined impact (e.g., RCE, Data Exfiltration). |

## 4. Indicators of Chaining Potential

- **Sensitive Information in Responses**: Passwords, internal IPs, or session tokens.
- **Unusual Header Reflections**: Headers like `X-Forwarded-For` being reflected in logs or pages.
- **URL Parameters that Fetch Remote Content**: Potential for SSRF or Open Redirect.
- **File Upload Functionality**: Potential for RCE or stored XSS.
