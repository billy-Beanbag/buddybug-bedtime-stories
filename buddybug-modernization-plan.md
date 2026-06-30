# BuddyBug Modernization Plan

## Scope

This document proposes a modernization plan for the BuddyBug repository based on the architectural review completed on June 30, 2026.

This is a planning artifact only. It does not make or describe code changes already applied. The goal is to break the work into implementation-ready tracks with clear sequencing, file impact, relative effort, and iOS relevance.

---

## Planning Assumptions

- **Risk level** refers to implementation and regression risk.
- **Estimated effort** is technical scope, not calendar time.
  - **S** = localized change in 1-3 areas
  - **M** = cross-cutting but bounded
  - **L** = multi-area refactor or new subsystem

---

## Recommended Sequencing

Recommended execution order:

1. **Immediate security fixes**
2. **Production reliability fixes**
3. **Documentation/context files for future AI agents**
4. **Frontend maintainability fixes**
5. **iOS-readiness fixes**

### Why this order

BuddyBug should not move toward an iOS app until the platform is safer and more operationally reliable. Otherwise, the iOS effort will inherit browser-era shortcuts in auth, runtime durability, and offline assumptions, making the mobile work slower and more brittle.

---

## 1. Immediate Security Fixes

### 1.1 Remove or strictly gate dev-only auth/debug behavior

- **Why it matters:** The current code exposes local-development conveniences inside runtime code paths, including demo admin creation and login diagnostics. This is the highest-risk class of issue because it can accidentally survive into production.
- **Exact files likely involved:**
  - `app/main.py`
  - `app/routers/system.py`
  - `app/services/user_service.py`
  - `app/utils/dev_seed.py`
  - `tests/conftest.py`
  - `README.md`
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/remove-dev-auth-backdoors-0efa`

### 1.2 Add production config validation and fail-fast auth hardening

- **Why it matters:** BuddyBug can currently boot with insecure defaults or permissive combinations like default secrets, debug behavior, long JWT TTLs, and broad CORS patterns. The app should refuse to start when production settings are unsafe.
- **Exact files likely involved:**
  - `app/config.py`
  - `app/main.py`
  - `app/utils/auth.py`
  - `app/routers/users.py`
  - `.env.example`
  - `render.yaml`
  - `DEPLOYMENT.md`
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/harden-prod-config-validation-0efa`

### 1.3 Replace browser-local JWT storage with a secure session strategy

- **Why it matters:** `localStorage` token storage is a poor fit for a product with admin surfaces and family data. It also creates the wrong foundation for native or wrapped mobile clients.
- **Exact files likely involved:**
  - `buddybug_frontend/lib/auth.ts`
  - `buddybug_frontend/context/AuthContext.tsx`
  - `buddybug_frontend/lib/api.ts`
  - `app/utils/auth.py`
  - `app/routers/users.py`
  - `app/utils/dependencies.py`
  - `app/services/user_service.py`
- **Risk level:** High
- **Estimated effort:** L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/secure-session-architecture-0efa`

### 1.4 Harden pre-launch staff access and secret handling

- **Why it matters:** The pre-launch bypass currently uses query-string secrets and raw secret-value cookies. That is fragile and leaks too easily via logs, browser history, and referrers.
- **Exact files likely involved:**
  - `buddybug_frontend/app/access/route.ts`
  - `buddybug_frontend/lib/prelaunch/config.ts`
  - `buddybug_frontend/lib/security/index.ts`
  - `buddybug_frontend/proxy.ts`
  - `buddybug_frontend/PRELAUNCH_SETUP.md`
- **Risk level:** Medium
- **Estimated effort:** S-M
- **Should it be done before the iOS app?** Preferably yes
- **Suggested branch name:** `cursor/harden-prelaunch-access-0efa`

---

## 2. Production Reliability Fixes

### 2.1 Replace `BackgroundTasks` workflow execution with a worker-backed job system

- **Why it matters:** The code already models jobs in the database, but execution is still tied to API processes. That risks job loss on deploy or restart and makes scaling content generation unreliable.
- **Exact files likely involved:**
  - `app/services/workflow_service.py`
  - `app/services/automation_service.py`
  - `app/models/workflow_job.py`
  - `app/routers/workflows.py`
  - `app/routers/automation.py`
  - `docker-compose.yml`
  - `render.yaml`
  - likely new worker entrypoints under `app/` or `scripts/`
- **Risk level:** High
- **Estimated effort:** L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/workerize-workflow-jobs-0efa`

### 2.2 Implement durable production asset storage

- **Why it matters:** Story assets, illustrations, audio, and offline package artifacts are core product outputs. The current local-disk-first model is not durable enough, and S3 support is incomplete.
- **Exact files likely involved:**
  - `app/services/storage_service.py`
  - `app/services/illustration_generation_service.py`
  - `app/services/narration_service.py`
  - `app/services/audio_service.py`
  - `app/services/book_builder.py`
  - `.env.example`
  - `render.yaml`
  - `DEPLOYMENT.md`
- **Risk level:** Medium
- **Estimated effort:** M-L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/implement-durable-asset-storage-0efa`

### 2.3 Replace single-process rate limiting with a shared backing store

- **Why it matters:** In-memory rate limiting will break down or become inconsistent across multiple instances. It is also too easy to undermine with weak proxy/IP handling.
- **Exact files likely involved:**
  - `app/middleware/rate_limit.py`
  - `app/config.py`
  - `app/routers/users.py`
  - `app/routers/billing.py`
  - `requirements.txt`
  - `.env.example`
  - `DEPLOYMENT.md`
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/distributed-rate-limiting-0efa`

### 2.4 Make Postgres + Alembic the canonical path and reduce SQLite schema patching

- **Why it matters:** The SQLite compatibility layer is convenient, but it means schema truth lives partly in migrations and partly in runtime code. That increases drift risk and weakens confidence in deploy behavior.
- **Exact files likely involved:**
  - `app/database.py`
  - `tests/conftest.py`
  - `docker-compose.yml`
  - `.env.example`
  - `README.md`
  - `DEPLOYMENT.md`
- **Risk level:** Medium-High
- **Estimated effort:** M-L
- **Should it be done before the iOS app?** Preferably yes
- **Suggested branch name:** `cursor/postgres-first-schema-path-0efa`

---

## 3. Frontend Maintainability Fixes

### 3.1 Generate frontend API types from the backend contract

- **Why it matters:** `buddybug_frontend/lib/types.ts` is too large and too manually maintained. It will drift further as the API evolves and becomes even more painful once mobile clients appear.
- **Exact files likely involved:**
  - `buddybug_frontend/lib/types.ts`
  - `buddybug_frontend/package.json`
  - `.github/workflows/ci.yml`
  - likely new generation scripts under `buddybug_frontend/`
  - possibly `app/main.py` if OpenAPI metadata needs cleanup
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/generate-frontend-api-types-0efa`

### 3.2 Introduce a shared frontend data-fetching/cache layer

- **Why it matters:** The current `useEffect`-heavy pattern does not scale well. A shared async state layer would reduce duplicate requests, normalize errors and loading, and make the reader/admin screens easier to tame.
- **Exact files likely involved:**
  - `buddybug_frontend/package.json`
  - `buddybug_frontend/app/layout.tsx`
  - `buddybug_frontend/lib/api.ts`
  - `buddybug_frontend/context/AuthContext.tsx`
  - `buddybug_frontend/app/library/page.tsx`
  - `buddybug_frontend/app/reader/[bookId]/page.tsx`
  - `buddybug_frontend/app/admin/workflow/page.tsx`
- **Risk level:** Medium
- **Estimated effort:** L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/add-frontend-data-layer-0efa`

### 3.3 Refactor the reader page into focused hooks/components

- **Why it matters:** The reader experience is likely the future iOS app’s core screen. Right now it is too large and mixes rendering, offline logic, analytics, premium gating, and playback concerns.
- **Exact files likely involved:**
  - `buddybug_frontend/app/reader/[bookId]/page.tsx`
  - likely new files under `buddybug_frontend/components/reader/`
  - likely new files under `buddybug_frontend/lib/reader/` or `buddybug_frontend/hooks/`
- **Risk level:** Medium
- **Estimated effort:** M-L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/refactor-reader-page-0efa`

### 3.4 Add a frontend test and lint baseline

- **Why it matters:** The frontend currently relies on typecheck and build only. That is too thin for a UI this large, especially before mobile packaging or native-client work.
- **Exact files likely involved:**
  - `buddybug_frontend/package.json`
  - `buddybug_frontend/tsconfig.json`
  - `buddybug_frontend/tsconfig.typecheck.json`
  - likely new `eslint.config.*`
  - likely new `vitest.config.*` and/or `playwright.config.*`
  - new test files under `buddybug_frontend/components/` and `buddybug_frontend/app/`
- **Risk level:** Low-Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Preferably yes
- **Suggested branch name:** `cursor/add-frontend-test-baseline-0efa`

---

## 4. iOS-Readiness Fixes

### 4.1 Define the mobile platform contract explicitly

- **Why it matters:** The code already hints at wrapped-app support via `isWrappedApp()`, but there is no strong contract for what changes between web, installed PWA, wrapper, and future native shell.
- **Exact files likely involved:**
  - `buddybug_frontend/lib/platform.ts`
  - `buddybug_frontend/lib/app-config.ts`
  - `buddybug_frontend/app/layout.tsx`
  - `buddybug_frontend/components/AboutAppCard.tsx`
  - `buddybug_frontend/public/manifest.json`
  - likely new `docs/mobile/ios-architecture.md`
- **Risk level:** Low-Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/define-mobile-platform-contract-0efa`

### 4.2 Decouple offline/download features from service-worker-only assumptions

- **Why it matters:** The current offline stack is browser-native: service worker, caches, IndexedDB, and navigator online/offline. A native iOS app or wrapper will need the same feature set behind platform adapters, not browser-only primitives.
- **Exact files likely involved:**
  - `buddybug_frontend/public/sw.js`
  - `buddybug_frontend/context/ConnectivityContext.tsx`
  - `buddybug_frontend/lib/offline-storage.ts`
  - `buddybug_frontend/lib/offline-sync.ts`
  - `buddybug_frontend/lib/library.ts`
  - `buddybug_frontend/app/reader/[bookId]/page.tsx`
- **Risk level:** High
- **Estimated effort:** L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/platformize-offline-storage-0efa`

### 4.3 Add app-facing configuration for deep links, build channel, and wrapped/native behavior

- **Why it matters:** iOS delivery will need a clean configuration surface for links, environment, versioning, feature flags, and app-shell differences. Right now those assumptions are scattered.
- **Exact files likely involved:**
  - `buddybug_frontend/lib/app-config.ts`
  - `buddybug_frontend/lib/platform.ts`
  - `buddybug_frontend/app/layout.tsx`
  - `buddybug_frontend/public/manifest.json`
  - `buddybug_frontend/vercel.json`
  - `buddybug_frontend/.env.local.example`
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/add-mobile-config-and-links-0efa`

### 4.4 Prepare reader, library, and narration flows for native playback/download semantics

- **Why it matters:** An iOS app will need predictable download packaging, background audio behavior, interruption handling, and simpler contracts for book/audio retrieval than a browser page usually does.
- **Exact files likely involved:**
  - `app/routers/reader.py`
  - `app/routers/library.py`
  - `app/routers/narration.py`
  - `app/services/reader_service.py`
  - `app/services/library_service.py`
  - `app/services/narration_service.py`
  - `buddybug_frontend/app/reader/[bookId]/page.tsx`
  - `buddybug_frontend/lib/offline-storage.ts`
- **Risk level:** High
- **Estimated effort:** M-L
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/prepare-native-reader-and-audio-0efa`

### 4.5 Tighten privacy/account-management flows for App Store readiness

- **Why it matters:** BuddyBug is family/child-adjacent software. Before iOS, privacy/export/delete flows should be obvious, testable, and reachable from the product UI.
- **Exact files likely involved:**
  - `app/routers/privacy.py`
  - `app/services/privacy_service.py`
  - `buddybug_frontend/app/settings/`
  - `buddybug_frontend/app/profile/page.tsx`
  - `buddybug_frontend/app/layout.tsx`
  - `DEPLOYMENT.md`
- **Risk level:** Medium
- **Estimated effort:** M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/harden-app-store-privacy-flows-0efa`

---

## 5. Documentation and Context Files for Future AI Agents

### 5.1 Create a canonical architecture map

- **Why it matters:** Future agents should not have to rediscover the same domain boundaries, key files, and subsystem responsibilities every time.
- **Exact files likely involved:**
  - new `docs/architecture/system-overview.md`
  - new `docs/architecture/backend-domain-map.md`
  - new `docs/architecture/frontend-surface-map.md`
  - `buddybug-architectural-review.md`
- **Risk level:** Low
- **Estimated effort:** S-M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/add-architecture-context-docs-0efa`

### 5.2 Create a deployment/environment source-of-truth doc

- **Why it matters:** The current operational context is split across multiple docs and env examples. AI agents and human contributors need one place that explains which environment variables matter in which mode.
- **Exact files likely involved:**
  - new `docs/operations/environment-matrix.md`
  - `DEPLOYMENT.md`
  - `buddybug_frontend/PRELAUNCH_SETUP.md`
  - `.env.example`
  - `buddybug_frontend/.env.local.example`
  - `render.yaml`
- **Risk level:** Low
- **Estimated effort:** S-M
- **Should it be done before the iOS app?** Yes
- **Suggested branch name:** `cursor/add-env-deployment-context-0efa`

### 5.3 Add an AI-agent working guide and domain glossary

- **Why it matters:** This repo has a legacy backend folder, dual DB stacks, pre-launch mode, generated-vs-manual contract issues, and a very broad domain surface. A short guide would prevent many low-value mistakes.
- **Exact files likely involved:**
  - new `AGENTS.md` or new `docs/agents/working-agreements.md`
  - new `docs/agents/domain-glossary.md`
  - `README.md`
- **Risk level:** Low
- **Estimated effort:** S
- **Should it be done before the iOS app?** Preferably yes
- **Suggested branch name:** `cursor/add-agent-working-guide-0efa`

---

## Recommended First Five Cursor Implementation Tasks

These are the first five tasks to prioritize because they are high-value, reasonably separable, and create a safer base for everything that follows.

### 1. Remove/gate dev auth backdoors

**Suggested prompt:**

> On branch `cursor/remove-dev-auth-backdoors-0efa`, remove or strictly environment-gate all dev-only auth/debug behavior from the BuddyBug repo. Focus on `/dev/seed-admin`, `/login-check`, demo admin startup seeding, and the debug/demo credential bypass in `app/services/user_service.py`. Preserve legitimate local developer workflows by moving them behind explicit dev-only scripts or environment-gated code paths. Update or add focused tests where needed, and update any docs that reference the old behavior. Commit, push, and update the PR.

### 2. Add production config validation and secure startup defaults

**Suggested prompt:**

> On branch `cursor/harden-prod-config-validation-0efa`, implement production config validation for BuddyBug so the backend fails fast on insecure settings. Focus on `app/config.py`, `app/main.py`, `app/utils/auth.py`, and related auth startup paths. Ensure production cannot run with default secrets, overly permissive debug settings, or obviously unsafe auth defaults. Update `.env.example`, `render.yaml`, and `DEPLOYMENT.md` to match the new requirements. Add focused tests for validation behavior if practical. Commit, push, and update the PR.

### 3. Harden pre-launch access secret handling

**Suggested prompt:**

> On branch `cursor/harden-prelaunch-access-0efa`, secure the BuddyBug pre-launch staff access flow. Remove query-string-secret and raw-secret-cookie weaknesses in `buddybug_frontend/app/access/route.ts`, `buddybug_frontend/lib/prelaunch/config.ts`, `buddybug_frontend/lib/security/index.ts`, and `buddybug_frontend/proxy.ts`. Use timing-safe secret comparison, avoid storing the raw secret as the cookie value, and preserve the intended staff bypass behavior. Update `buddybug_frontend/PRELAUNCH_SETUP.md` accordingly. Commit, push, and update the PR.

### 4. Replace in-memory rate limiting with a shared, production-safe design

**Suggested prompt:**

> On branch `cursor/distributed-rate-limiting-0efa`, replace BuddyBug’s single-process in-memory rate limiting with a shared production-safe approach. Focus on `app/middleware/rate_limit.py`, `app/config.py`, `app/routers/users.py`, and `app/routers/billing.py`. Improve client IP handling for trusted proxy setups, preserve the current endpoint behavior where appropriate, and document any new environment variables or infrastructure requirements in `.env.example` and `DEPLOYMENT.md`. Add focused tests if feasible. Commit, push, and update the PR.

### 5. Generate frontend API types from the backend contract

**Suggested prompt:**

> On branch `cursor/generate-frontend-api-types-0efa`, replace or reduce the hand-maintained API contract surface in `buddybug_frontend/lib/types.ts` by generating frontend API types from the FastAPI/OpenAPI contract. Wire the generation into frontend tooling and CI, update any imports/usages needed for the initial migration, and document the workflow for future contributors. Touch `buddybug_frontend/package.json`, `.github/workflows/ci.yml`, and any supporting scripts/config needed. Keep the first pass practical rather than perfect. Commit, push, and update the PR.

---

## Final Recommendation

If only one thing happens before the iOS effort begins, it should be this:

1. eliminate dev-only security shortcuts
2. harden production configuration and auth defaults
3. make background workflows and storage durable
4. stabilize the frontend contract and state model
5. only then start platform-specific iOS adaptation

This order gives BuddyBug the best chance of turning its current monolith into a reliable product platform rather than simply wrapping the current web app and carrying forward avoidable risk.
