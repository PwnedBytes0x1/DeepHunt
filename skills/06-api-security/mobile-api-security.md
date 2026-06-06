---
name: Mobile API Security Testing
category: api-security
version: "1.0"
author: "DeepHunt"
description: "Mobile application API security testing techniques"
tags:
  - mobile
  - android
  - ios
  - api-security
  - reverse-engineering
---

# Mobile API Security Testing

## Overview

Mobile apps interact with APIs differently than web apps. This skill covers mobile-specific API vulnerabilities and testing techniques.

## Setting Up Testing Environment

### Android

```bash
# Install certificate for HTTPS interception
# Method 1: Magisk + Move Certificates
# Method 2: Charles Proxy certificate
# Method 3: Burp Suite Mobile extension

# Configure proxy
export HTTP_PROXY="http://127.0.0.1:8080"
export HTTPS_PROXY="http://127.0.0.1:8080"

# Check network settings
settings get global http_proxy
```

### iOS

```bash
# Install Burp certificate
# Safari > Settings > Certificates > Install

# Proxy configuration
# Settings > Wi-Fi > Proxy
```

## API Interception

### Common Endpoints

```bash
# Look for API patterns
/api/v1/
/api/v2/
/api/v3/
/rest/
/graphql
/mobile/
/app/
/json/

# Version patterns
/api/1.0/
/api/2.0/
/v1/
/v2/
```

### Request Analysis

```bash
# Check headers
X-Platform: Android
X-App-Version: 1.2.3
X-Device-ID: abc123
X-Build-Type: release
Authorization: Bearer <token>

# Check for hardcoded credentials
curl -s "https://api.target.com/" | grep -i "api_key\|password\|secret"
```

## Authentication Bypass

### 1. Token Manipulation

```bash
# Test if token validation is client-side
# Use another user's token
curl -H "Authorization: Bearer USER_A_TOKEN" \
  "https://api.target.com/users/USER_B_ID"

# Test token reuse across devices
# Get token on Android, use on iOS
```

### 2. Device ID Spoofing

```bash
# Change device ID
curl -H "X-Device-ID: ATTACKER_DEVICE_ID" ...

# Test if server trusts device ID for auth
```

### 3. Version Downgrade

```bash
# Try to downgrade API version
curl -H "X-App-Version: 0.0.1" ...

# Older versions may have more vulnerabilities
```

## Insecure Data Storage

### Check for Hardcoded Secrets

```bash
# Decompile APK
apktool d app.apk -o output

# Search for secrets
grep -r "api_key\|password\|secret\|token" output/
grep -r "base64" output/
grep -r "Authorization" output/

# Check for hardcoded endpoints
grep -r "http://\|https://" output/ | grep -v "google\|android"
```

### SSL Pinning Bypass

```bash
# Using Objection
objection run
android sslpinning disable

# Using Frida
frida -U -f com.target.app -l sslpinning-bypass.js

# Manual certificate installation
# Copy Burp cert to /system/etc/security/cacerts/
```

## API Vulnerabilities

### 1. Weak Rate Limiting

```bash
# Test rate limits
for i in {1..1000}; do
  curl -s "https://api.target.com/endpoint" > /dev/null
done

# Bypass with device ID rotation
for device in device1 device2 device3; do
  curl -H "X-Device-ID: $device" ...
done
```

### 2. Insufficient Payload Validation

```bash
# Try injection via mobile-specific fields
curl -X POST "https://api.target.com/update-profile" \
  -d "device_id=test'; DROP TABLE users;--"
  -d "phone_number=1234567890'; malicious();--"
```

### 3. Backup Vulnerability

```bash
# Check if app allows backups
cat AndroidManifest.xml | grep "android:allowBackup"

# Extract backup
adb backup -apk -f backup.ab com.target.app
android backup parse backup.ab

# Check for sensitive data in backup
```

## Deep Link Testing

### Android Deep Links

```bash
# Check for deep link handlers
# In AndroidManifest.xml:
# <intent-filter>
#   <data android:scheme="https" android:host="target.com"/>
# </intent-filter>

# Test deep links
adb shell am start -a android.intent.action.VIEW \
  -d "https://target.com/app/path"

# Test parameter injection
adb shell am start -a android.intent.action.VIEW \
  -d "https://target.com/app/path?param=value"
```

### OAuth Callback

```bash
# Test OAuth callback handling
# Install malicious app with same package name
# Redirect OAuth to attacker's app

# Test custom URL schemes
myapp://callback?token=xxx
```

## Binary Analysis

### APK Analysis

```bash
# Decompile
apktool d app.apk -o decompiled

# Static analysis
find decompiled/ -name "*.java" -o -name "*.smali"

# Check for native libraries
ls -la lib/
objdump -d lib/arm64-v8a/libnative.so | grep system
```

### iOS Binary

```bash
# Extract IPA
unzip app.ipa

# Analyze binary
otool -L TargetBinary
strings TargetBinary | grep -i "api\|key\|secret"

# Class dump
class-dump-z TargetBinary
```

## Mobile-Specific Payloads

### Intent Injection

```bash
# Inject via Intent extras
adb shell am start -a android.intent.action.VIEW \
  -d "https://target.com/" \
  -e "extra_param" "'; malicious();//"
```

### Clipboard Injection

```bash
# If app reads from clipboard
echo "malicious_data" | xclip -selection clipboard

# When app reads clipboard, inject payload
```

### NFC/Bluetooth Exploitation

```bash
# Check for NFC endpoints
# If app reads NFC tags, check for injection
nfc-list
nfc-mfclassic r a A.mdump 1.mfd
```

## Secure Communication Checklist

- [ ] Verify HTTPS/TLS pinning
- [ ] Check certificate validation
- [ ] Test for plaintext traffic
- [ ] Verify API authentication
- [ ] Check for hardcoded secrets
- [ ] Test backup functionality
- [ ] Verify deep link security
- [ ] Test binary obfuscation