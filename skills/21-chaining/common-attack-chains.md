---
name: Common Attack Chains
category: chaining
version: "1.0"
author: "PwnedBytes0x1"
description: "Examples of common and effective vulnerability chains"
tags:
  - examples
  - chaining
  - exploit
---

# Common Attack Chains

This manual provides a catalog of well-known vulnerability chains and how they work.

## 1. SSRF → Cloud Metadata → RCE
The classic cloud exploitation chain.
- **Bug 1 (SSRF)**: The ability to make the server fetch an internal URL.
- **Chain**: Target the cloud provider's metadata endpoint (e.g., `169.254.169.254`).
- **Result**: Extract IAM credentials/Access Keys.
- **Bug 2 (Privileged Access)**: Use the keys to access S3 buckets or execute commands on EC2 instances.

## 2. Open Redirect → SSRF Bypass
Using a trusted redirector to bypass SSRF filters.
- **Bug 1 (SSRF)**: An endpoint that fetches URLs but has a domain whitelist.
- **Bug 2 (Open Redirect)**: A legitimate endpoint on a whitelisted domain that redirects to any URL.
- **Chain**: Provide the SSRF endpoint with the Open Redirect URL pointing to an internal IP.
- **Result**: The SSRF filter sees the whitelisted domain, but the internal request follows the redirect to the target.

## 3. IDOR → Information Disclosure → Account Takeover
Using IDOR to gather the data needed for a more serious attack.
- **Bug 1 (IDOR)**: Accessing another user's profile to see their email and hidden "security question" answer.
- **Bug 2 (Weak Password Reset)**: A password reset flow that only requires an email and a security question.
- **Chain**: Use the data from the IDOR to reset the target's password.
- **Result**: Full Account Takeover (ATO).

## 4. XSS → CSRF (Bypass)
Using XSS to execute actions on behalf of a user, even with CSRF protection.
- **Bug 1 (XSS)**: Injecting a script into the user's browser.
- **Chain**: The script can read the CSRF token from the page (as it's in the same origin) and then make a POST request with that token.
- **Result**: Perform sensitive actions (change email, delete account) while bypassing all CSRF protections.

## 5. File Upload (Innocuous) → Path Traversal → RCE
Turning a limited file upload into a shell.
- **Bug 1 (File Upload)**: Allows uploading images only, but doesn't check the filename properly.
- **Bug 2 (Path Traversal)**: The filename can contain `../` sequences.
- **Chain**: Upload an "image" with a `.php` or `.jsp` extension and use path traversal to place it in a web-accessible directory (e.g., `../../var/www/html/shell.php`).
- **Result**: Remote Code Execution (RCE).

## 6. CRLF Injection → XSS or Cache Poisoning
Using newline injection to manipulate HTTP responses.
- **Bug 1 (CRLF)**: Injecting `\r\n` into a response header.
- **Chain**: Inject a second set of headers and a body containing a script.
- **Result**: The browser interprets the injected body as the response, leading to XSS or poisoning the CDN cache for other users.

## Chaining Matrix

| Source Bug | Potential Sink/Target Bug | Impact Escalation |
|------------|---------------------------|-------------------|
| SSRF | Internal Admin Panel | Unauthorized Access |
| Information Leak | Brute Force | Successful Login |
| Local File Read | Hardcoded Secrets | Full System Compromise |
| Subdomain Takeover | CSRF (via cookie) | Account Takeover |
