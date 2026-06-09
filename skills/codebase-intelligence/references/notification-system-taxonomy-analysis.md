# Notification System Taxonomy Analysis

## When to Use

When analyzing a notification/message-center system to understand its category taxonomy, sub-type mapping, tab filtering, and row-level rendering — especially before proposing UI changes or new notification types.

## Analysis Checklist

### 1. Type Definitions
- Find the `Notification` type/interface — identify `category` (drives tabs/groups) and `transactionType` or equivalent sub-field (drives row-level labels)
- Note whether sub-type is optional (some categories may not have sub-types)
- Check i18n translation keys for human-readable labels

### 2. Category → Tab Mapping
- List all category values and map them to UI tabs
- Verify: does every category have a tab? Are some categories hidden from tabs?
- Check if tabs show unread counts per category

### 3. Normalization / Inference Logic
- Find the service that normalizes raw backend notifications into the frontend type
- Identify inference logic (regex on title/body to infer sub-type from keywords)
- Map the flow: raw API → normalizeCategory → normalizeNotification → store

### 4. Row-Level Rendering
- Check if transactionType (or equivalent) is rendered as a visual tag/badge
- **Color differentiation pitfall**: if all sub-types share the same color class (e.g. all green `bg-success-soft`), users cannot visually distinguish them — flag this as a UX gap
- Check if icon/avatar varies by sub-type

### 5. Impact Routing
- Some systems route notifications to trigger store refreshes (wallet, transactions, card, wealth)
- Map: notification category/sub-type → which stores get refreshed
- This reveals the system's "what does this notification actually affect" semantics

## Common Findings Pattern

```
Category (Tab)    →  Sub-type (Row Label)   →  Store Impact
─────────────────────────────────────────────────────────────
trade             →  deposit/withdrawal/...  →  wallet + transactions + (card|wealth)
card              →  (none)                  →  card
wealth            →  (none)                  →  wealth
security          →  (none)                  →  (none)
system            →  (none)                  →  (none)
```

## UVISA Reference

See `uvisa-notification-system.md` in this directory for the concrete UVISA implementation: type fields, category taxonomy, inference regexes, tab structure, i18n keys, and impact router mapping.
