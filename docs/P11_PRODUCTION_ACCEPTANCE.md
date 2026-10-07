# P1.1 Newsletter Production 验收

日期：2026-10-07

## 结论

```
P11_CODE = PASS_MAIN
P11_PR = PASS_MERGED_34
P11_CI = PASS_RUN_92
P11_STAGING_MIGRATION = PASS
P11_STAGING_EDGE = PASS
P11_STAGING_FAIL_CLOSED_E2E = PASS
P11_PRODUCTION_MIGRATION = PASS
P11_PRODUCTION_EDGE = PASS
P11_PRODUCTION_FAIL_CLOSED_E2E = PASS
P11_PUBLIC_STATIC = PASS
P11_REAL_EMAIL_SEND = CLOSED_BY_DESIGN
P11_FINAL = PASS_PRELAUNCH_FREE_FIRST
```

## GitHub

- PR #34: merged
- squash commit: `f8cbb1862cdb108c375005c346c34c08cf1c53c7`
- CI: JianShi CI run #92 = success
- static snapshot commit observed: `6a0b826a061871eccb668a2bc0684125238d37b8`

## Database

Production migration:

- `0042_newsletter_launch_gate`
- Supabase version: `20261007055701`

The launch gate requires all of:

- `sender_domain_verified`
- `confirmation_e2e_pass`
- `daily_digest_e2e_pass`
- `unsubscribe_e2e_pass`
- `bounce_complaint_handling_pass`
- `security_review_pass`

and `newsletter_provider_ready_v01() = true`.

Credentials alone cannot open real outbound email.

## Production Edge Functions

- newsletter-subscribe: v4, sha256 `9d4435ce51599f3b4b9fd16f252417900c4bb5859f8882b8656f12b77f3903b8`
- newsletter-dispatch-confirmations: v2, sha256 `1d01cc6b4f9cb561fa01083cde5ce94287500934b4dc59b2a0f1d556937b0ad3`
- newsletter-daily: v2, sha256 `7a40b086228c96540a8fb252e81443915e0a34a7f6c31d8d32122bcdc7b39644`

## Production fail-closed evidence

At acceptance time:

```
provider_ready = false
launch_ready = false
sender_domain_verified = false
confirmation_e2e_pass = false
daily_digest_e2e_pass = false
unsubscribe_e2e_pass = false
bounce_complaint_handling_pass = false
security_review_pass = false
```

Runtime metrics:

```
WAITLIST = 2
PENDING_CONFIRMATION = 0
ACTIVE = 0
UNSUBSCRIBED = 0
DAILY_ROWS_TODAY = 0
DAILY_QUEUED_TODAY = 0
```

Direct Production worker invocations returned HTTP 200 with:

```json
{"ok":true,"launch_ready":false,"queued":0,"message":"NEWSLETTER_LAUNCH_GATE_CLOSED"}
```

for both confirmation dispatch and daily sender.

Therefore no real email was queued.

## Public site acceptance

`https://jianshi-bua.pages.dev/search.js` contains `CONFIRMATION_QUEUED` in the successful-state reset list, proving the merged frontend asset reached the public Cloudflare Pages deployment.

## Frozen policy

- `DOMAIN_PURCHASE = DEFERRED`
- `RESEND_PLAN = FREE_FIRST`
- `PUBLIC_NEWSLETTER_SEND = CLOSED`
- public signup may continue to record WAITLIST intent
- real sending can only be enabled after a verified sender domain plus the complete launch-gate E2E checklist.
