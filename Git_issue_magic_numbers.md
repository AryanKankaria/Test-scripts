Issue Title
Hardcoded configuration constants should be centralized in a single config file

Body
Summary
Several files across the codebase contain hardcoded numeric and string constants that represent policy/configuration decisions — rate limits, timeouts, costs, thresholds, etc. These should be centralized in a single config module or .env defaults so that changing a value means editing one place, not hunting across files. Some values are also duplicated across files with inconsistencies.

1. Rate Limiting — Inconsistent values across files
routes/login.js and routes/password.js define overlapping rate-limit settings independently:

login.js:11 — MAX_LOGIN_ATTEMPTS = 10
login.js:13 — COOLDOWN_MINUTES = 1 min initial lockout after max attempts
login.js:14 — COOLDOWN_INCREMENT_MINUTES = 2 min added per subsequent failure
login.js:74,77 — Progressive delay: base 1000ms, cap 30000ms
password.js:10-11 — Rate limit window: 60000ms, max requests: 10
new-user-verification.js:9 — MAX_OTP_ATTEMPTS = 5
new-user-verification.js:10 — OTP_LOCKOUT_MINUTES = 30
new-user-verification.js:26,29 — Progressive delay base/cap: identical values to login.js, copy-pasted
2. Session TTL — Different defaults in different files
SESSION_TTL_HOURS is read from process.env in multiple places but falls back to different values:

routes/login.js:9 — defaults to 0.25 hours (15 min)
middleware/auth.js:4 — defaults to 0.25 hours (15 min)
routes/signing.js:357 — defaults to 3 hours
3. Signing Costs — Duplicated across 3 files
SIGNING_COST_AADHAAR (25.00) and SIGNING_COST_NON_AADHAAR / SIGNING_COST_PER_VIRTUAL_FIELD (15.00) are each defined independently in:

routes/signing.js:19-20
routes/envelopes.js:12-13
routes/bulk-send-create.js:12-13
A price change requires editing all three files.

4. OTP TTL — Same default repeated across files
OTP_TTL_MINUTES defaults to 10 in routes/login.js:374, routes/new-user-verification.js, and routes/users.js:12 — each independently.

5. Cryptography / Key Rotation
All in utils/crypto.js:

crypto.js:20 — KEY_LIFETIME_MS = 2 hours
crypto.js:21 — CACHE_TTL_MS = 5 minutes
crypto.js:22 — GRACE_PERIOD_MS = 4 hours
crypto.js:34 — RSA modulusLength = 4096
6. Database Connection Pool
All in db.js:

db.js:59 — pool max = 20 connections
db.js:60 — idleTimeoutMillis = 30000
db.js:61 — connectionTimeoutMillis = 2000
7. File Size Limits
routes/documents.js:15 — max upload size = 50 MB
routes/documents.js:321,410 — FILE_SIZE_THRESHOLD = 5 MB
routes/users.js:434 — MAX_SIZE = 2.7 MB
routes/envelopes.js:161 — MAX_CSV_SIZE = 1 MB
routes/envelopes.js:181 — MAX_LINES = 1001 rows
utils/pdfProcessor.js:44 — max PDF size = 50 MB
utils/pdfProcessor.js:56 — max PDF pages = 100
8. API Timeouts
routes/password.js:63 — HIBP API timeout = 3000ms
routes/test-network.js:15,62 — connectivity check timeout = 5000ms
utils/googleMapsLocation.js:48,151 — Google Maps API timeout = 10000ms
utils/partnerGraphQL.js:33 — Partner API max retries = 3
utils/partnerGraphQL.js:50 — Partner API timeout = 15000ms
utils/partnerGraphQL.js:160 — Partner API second timeout = 30000ms
utils/partnerGraphQL.js:207 — file upload timeout = 60000ms
utils/indisignS3.js:40 — S3 upload timeout = 60000ms
utils/indisignS3.js:104,176,313 — S3 operation timeout = 15000ms
utils/indisignS3.js:118 — S3 large file timeout = 120000ms
utils/indisignS3.js:272 — S3 operation timeout = 30000ms
utils/indisignS3.js:212 — presigned URL expiry = 3600s
utils/indisignS3.js:169 — alternative presigned URL expiry = 300s
9. Signing / Expiry Durations
routes/signing.js:25 — signing link expiry = 24 hours
routes/signing.js:978,2145,2578 — AADHAAR_SESSION_TIMEOUT = 15 minutes, defined three times in the same file
routes/signing.js:3953 — grace period = 10 minutes
routes/envelopes.js:317 — reminder_interval_days = 30 (conflicts with the 7 on lines 410 and 622)
10. Email Templates — Expiry durations as hardcoded strings
Expiry durations are written as plain strings inside email copy in utils/emailService.js (lines 96, 100, 248, 258, 346, 362, 498, 513) and are not derived from the same constants used in the actual logic — so they can silently go out of sync if a timeout is changed.

Proposed Fix
Create a config/index.js (or config.js) that exports all of the above as named exports, reads from process.env where appropriate, and is imported wherever these values are needed. This ensures one place to change any value, consistency across files, and no silent drift between email copy and actual expiry logic.

Labels: refactor, technical-debt, security
Priority: Medium