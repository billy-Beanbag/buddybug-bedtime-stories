## Buddybug Deployment Foundation

Buddybug now includes a production-ready foundation for FastAPI + Next.js deployment with Alembic migrations, Docker images, PostgreSQL support, demo seeding, and CI validation.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop or compatible Docker runtime
- PowerShell on Windows for the examples below

## Environment Files

Backend example:

- Copy `.env.example` to `.env`

Frontend example:

- Copy `buddybug_frontend/.env.local.example` to `buddybug_frontend/.env.local`

Important variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- Stripe settings when billing is enabled
- storage settings when moving beyond local mock assets
- story generation settings when enabling live model-written stories:
  - `STORY_GENERATION_API_KEY`
  - `STORY_GENERATION_MODEL`
  - `STORY_GENERATION_BASE_URL`
  - `STORY_GENERATION_TIMEOUT_SECONDS`
  - `STORY_GENERATION_CANDIDATE_COUNT`
  - `STORY_GENERATION_DEBUG`
  - `STORY_GENERATION_REQUIRE_LIVE`

## Backend Local Run

```powershell
cd "C:\Users\User\Documents\BuddyBug"
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Useful endpoints:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Frontend Local Run

```powershell
cd "C:\Users\User\Documents\BuddyBug\buddybug_frontend"
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

## Alembic Commands

Apply migrations:

```powershell
python -m alembic upgrade head
```

Create a new migration after model changes:

```powershell
python -m alembic revision --autogenerate -m "describe change"
```

Roll back one revision:

```powershell
python -m alembic downgrade -1
```

## Reset And Seed Demo Data

Reset the local database and re-apply migrations:

```powershell
python scripts/reset_db.py
```

Seed a full demo dataset:

```powershell
python scripts/seed_demo.py
```

This creates:

- canonical characters
- narration voices
- demo Spanish and French book translation records for the seeded book
- demo admin, premium, and free users
- story ideas
- one approved draft
- one page plan with approved mock illustrations
- one published book
- reading progress and feedback data
- approved audio when a seeded voice is available

Demo credentials:

- Admin: `admin@buddybug.local` / `Admin123!`
- Premium: `premium@buddybug.local` / `Premium123!`
- Free: `free@buddybug.local` / `Free123!`

## Internationalization And Multi-Market Foundation

Buddybug now includes a lightweight multilingual foundation for:

- UI locales: `en`, `es`, `fr`
- book/page translation records via `booktranslation` and `bookpagetranslation`
- explicit English fallback when a requested translation is missing
- language-aware reader audio filtering based on narration voice language

How fallback works:

- English remains the default canonical language
- `GET /reader/books/{book_id}?language=es` returns translated title/page text when published Spanish translations exist
- missing translations fall back to the canonical English/original book content without bypassing preview or premium access rules

How to test locally:

- run `python scripts/reset_db.py`
- run `python scripts/seed_demo.py`
- call `GET /reader/languages`
- call `GET /reader/books/{book_id}?language=es`
- create or edit translations through the admin endpoints under `/admin/i18n/*`

## Autonomous Workflow Jobs

Buddybug now includes a lightweight database-backed workflow job layer for safe automation.

Supported job types:

- `generate_story_ideas`
- `generate_story_draft`
- `generate_illustration_plan`
- `generate_page_illustrations`
- `assemble_book`
- `full_story_pipeline`

Safety defaults:

- jobs can generate ideas and drafts asynchronously
- `full_story_pipeline` stops at "draft generated and awaiting human review" unless an already approved draft exists
- jobs do not auto-publish by default
- human review remains required for draft approval

Useful local endpoints:

- `POST /workflows/generate-ideas`
- `POST /workflows/generate-draft`
- `POST /workflows/full-pipeline`
- `GET /workflows/jobs`
- `GET /admin/workflows/queue`
- `POST /admin/workflows/run-queued?limit=10`

## Content Safety And Quality Guardrails

Buddybug now includes deterministic internal quality checks for generated drafts and story page plans.

## Buddybug Story Engine

Buddybug now generates story structure before it writes prose.

What this means:

- story ideas are hook-first instead of vague atmosphere-first
- bedtime mode prefers calm, plot-led hooks with soft endings
- standard mode allows warmer, cheekier, lightly mischievous beats without becoming chaotic
- story plans include opening, problem, middle event, resolution, and illustration beats
- illustration planning can follow the same story beats for better scene consistency
- story generation can use a live OpenAI-compatible model endpoint when configured
- weak generated candidates are scored, ranked, and can now be marked `needs_revision` instead of quietly appearing review-ready

Creative rule:

- calm bedtime stories should still be real stories, not only atmosphere

In practice:

- the Story Engine filters hook types by mode
- it assigns characters according to their creative roles, like Daphne for playful catalysts and Verity for gentle resolution
- the writer consumes the structured brief and can request multiple full-story candidates from a live model
- candidate validation checks score repetition, setup clarity, reveal quality, and ending strength before the best draft is selected
- if no live model is configured, Buddybug falls back to the local legacy writer and marks those drafts `needs_revision` so they do not masquerade as strong review-ready output

Live story generation setup:

1. Copy `.env.example` to `.env` if you have not already.
2. Set `STORY_GENERATION_API_KEY` to your provider key.
3. Set `STORY_GENERATION_MODEL` to the model name you want Buddybug to use.
4. Optionally change `STORY_GENERATION_BASE_URL` if you are using an OpenAI-compatible provider instead of the default OpenAI URL.
5. For the first live end-to-end test, use `STORY_GENERATION_CANDIDATE_COUNT=1`.
6. After the first successful run, raise it later if you want stronger candidate ranking.
7. For a first live end-to-end test, set `STORY_GENERATION_REQUIRE_LIVE=true` so Buddybug does not silently fall back to the legacy writer.
8. For one temporary debug run, set `STORY_GENERATION_DEBUG=true` and then turn it back off after the test.

Important:

- without `STORY_GENERATION_API_KEY` and `STORY_GENERATION_MODEL`, the app will stay on the fallback path
- the fallback path now intentionally flags drafts as `needs_revision`
- that is expected behavior until live story generation is configured

What they do:

- run structured bedtime-safety, age-appropriateness, character-consistency, style-consistency, and structure-quality checks
- store results in the `qualitycheck` table for draft and page-plan targets
- regenerate fresh results on rerun so reviewers always see the latest check set
- flag warnings and failures for human review without blocking the required approval workflow

Important notes:

- these checks are deterministic internal guardrails, not external moderation or ML classification
- workflow draft-generation and illustration-plan jobs now trigger quality checks automatically
- human review is still required before illustration approval or publication

Useful local endpoints:

- `POST /quality/story-drafts/run`
- `POST /quality/story-pages/run`
- `GET /quality/story_draft/{draft_id}`
- `GET /quality/story_pages/{story_draft_id}`
- `GET /admin/quality/warnings`

## Automation Scheduler And Policy Layer

Buddybug now includes database-backed automation schedules that can enqueue recurring workflow jobs without removing review safeguards.

Supported schedule modes:

- `interval` schedules are fully supported and run immediately after creation, then from `last_run_at + interval_minutes`
- `cron` schedules use standard 5-field cron expressions via `croniter`

Safe policy behavior:

- schedules only create workflow jobs after policy validation
- policy can block disallowed job types entirely
- `allow_auto_publish = false` forces `publish_immediately = false`
- `stop_at_review_gate = true` keeps recurring full-pipeline runs from moving beyond review-gated steps

Useful local endpoints:

- `POST /automation/schedules`
- `GET /automation/due`
- `POST /automation/run-due?limit=10`
- `POST /automation/schedules/{schedule_id}/run`

Important:

- review and publication remain gated by policy by default
- there is no always-on in-process scheduler loop yet
- you can call `POST /automation/run-due` from a hosted cron or admin action to trigger due schedules safely

## Product Analytics And Experimentation Foundation

Buddybug now includes a lightweight first-party analytics layer and deterministic experiment assignment foundation.

Core events:

- `app_opened`
- `library_viewed`
- `book_opened`
- `book_page_viewed`
- `book_completed`
- `audio_started`
- `recommendation_clicked`
- `preview_wall_hit`
- `feedback_submitted`
- `checkout_started`
- `checkout_completed`
- `language_changed`

How tracking works:

- the frontend sends lightweight non-blocking events to `POST /analytics/track`
- authenticated requests automatically attach `user_id`
- guest tracking uses `X-Reader-Identifier`
- key server-side flows also create events for checkout creation/completion, feedback submission, and reading completion

Experiments:

- `POST /analytics/experiments/assign` assigns deterministic variants using a stable user or reader identity
- sticky assignments are persisted so the same user/guest receives the same variant later

This is an internal first-party analytics foundation only:

- no third-party SDK is required
- no external BI warehouse is required
- admin summaries are available under `/admin/analytics/*`

## Multi-Age-Band Foundation

Buddybug now supports two content lanes:

- `bedtime_3_7`
- `story_adventures_3_7`

Why `content_lane_key` exists:

- `age_band` remains useful for filtering and display
- `content_lane_key` is the clearer generation and quality selector for future expansion

Current lane differences:

- `bedtime_3_7` keeps the existing calm, dreamy, bedtime-safe Storylight behavior
- `story_adventures_3_7` allows richer plots and slightly more complex language while still forbidding graphic violence, horror, and inappropriate themes

This is a foundation-first release:

- the 3-7 lane continues working as before
- the 8-12 lane is ready for idea/draft generation and lane-aware quality checks
- available 8-12 content may remain limited until more stories are created

## Family Accounts And Child Profiles

Buddybug now supports a lightweight family foundation where one authenticated parent account can manage multiple child profiles.

What child profiles store:

- display name, age band, preferred language, and resolved content lane
- child-scoped reading progress, feedback, analytics context, and a simple derived reading profile

How selection works:

- the frontend can select one active child profile for the current reading session
- when selected, library, reader progress, feedback, recommendations, and analytics prefer that child's age band and language
- if no child profile is selected, account-level behavior still works as a backward-compatible fallback

Important scope note:

- this stage does not yet add deep parental controls, legal/COPPA flows, or complex household permissions

## Saved Library And Offline Foundation

Buddybug now separates saved-library behavior from offline download entitlement:

- authenticated users can save books to a personal library, optionally scoped to a selected child profile
- saved books remain useful as online bookmarks even for free users
- full offline download packages are currently limited to premium or admin access

Current download behavior:

- the backend generates a simple web-friendly `json_bundle` package with localized metadata, ordered pages, image URLs, and available audio metadata
- the frontend can request the package and open the returned package URL in the browser
- native offline sync, local encrypted storage, and richer caching are later stages

## Narrated Stories

Buddybug now supports a first narrated-story foundation built around voices, narration versions, and page-level audio segments.

What is included:

- active narration voices can be listed per language, with optional premium voice gating
- admins can generate mock narration for a published or ready book using the TTS adapter layer
- each generated narration stores one audio segment per page so the reader can follow narration page by page

How it fits the platform:

- the reader can fetch narration, switch voices, and auto-advance pages as narration finishes
- offline book packages now include narration metadata and segment URLs when a matching narration exists
- the current TTS layer is intentionally provider-abstracted so future integrations like Polly, Azure, ElevenLabs, or OpenAI TTS can be added without rewriting reader or workflow code

## Parental Controls And Bedtime Mode

Buddybug now supports a first parental-controls layer built around account-level defaults plus optional child overrides.

How it works:

- parent settings define safe defaults for bedtime mode, autoplay, quiet mode, premium voice access, and maximum age-band access
- child overrides can inherit those defaults or selectively override them for one child profile
- resolved controls are computed from the authenticated parent account plus the currently selected child profile

What the platform now respects:

- library and recommendation flows filter or deprioritize content outside the resolved age-band and bedtime settings
- the reader blocks access to stories outside allowed controls and surfaces bedtime mode in the UI
- narration playback respects autoplay restrictions, and premium voices can be hidden when disallowed

Scope note:

- stronger parental locks, PIN-style gates, and device-level screen-time controls are later stages

## Notifications And Daily Story Delivery

Buddybug now includes a first notifications foundation focused on in-app delivery and daily story suggestions.

What is included:

- each user has stored notification preferences for in-app reminders, email placeholders, bedtime reminders, new story alerts, and quiet-hours metadata
- in-app notification events can be listed, marked read, and created manually for testing
- a daily story suggestion can be generated for the account or a selected child profile

How daily story selection works:

- it reuses existing recommendation and parental-controls foundations
- child profile, language, age band, bedtime mode, and parental restrictions are all respected
- bedtime-safe content is preferred where practical, and no suggestion is returned if nothing suitable is available

Scope note:

- real push vendors, production email delivery, and larger campaign automation are later stages

## Creator And Publisher Tools Foundation

Buddybug now includes a first internal editorial workflow for trusted admin and editor users.

What is included:

- lightweight editor role support alongside admin access
- editorial projects for manual, AI-generated, or mixed publishing work
- manual story draft and page editing without relying on the AI idea pipeline
- editorial asset tracking for cover and page image overrides

Preview and publish flow:

- editors can build unpublished preview books from manual drafts and pages
- active editorial cover and page assets override visuals during preview and publish
- ready editorial projects can be published through the existing `Book` and `BookPage` flow

Scope note:

- public creator onboarding, marketplaces, and revenue-sharing workflows are later stages

## Search And Discovery Foundation

Buddybug now includes a first discovery layer for browsing a growing catalog.

What is included:

- per-book discovery metadata for searchable title, summary, normalized text, tags, and bedtime-safety cues
- public discovery search with structured filters for age band, language, content lane, characters, tone, featured books, and bedtime-safe browsing
- curated collections for featured lanes such as calming bedtime stories and older-reader adventures

Filtering behavior:

- discovery only returns publicly published books on the public endpoints
- child profile and parental-control context can be applied so search and collections stay aligned with family safety settings
- bedtime mode can bias results toward calmer, bedtime-safe stories

Scope note:

- external search infrastructure, fuzzy matching, and semantic ranking are later stages

## Public Marketing Site And Conversion Funnel Foundation

Buddybug now includes a public-facing marketing layer alongside the existing app.

What is included:

- public pages for home, features, pricing, how it works, for parents, and FAQ
- shared marketing header/footer and reusable CTA, pricing, feature, testimonial, and FAQ components
- launch-friendly CTA routing into register, login, discovery, library, or profile/billing depending on auth state

Where content lives:

- marketing copy, pricing tiers, FAQs, and testimonials are centralized in `buddybug_frontend/lib/marketing-content.ts`

How it connects to the app:

- public pages explain Buddybug and route visitors into `/register`, `/login`, `/discover`, `/library`, or `/profile`
- the existing authenticated reader and admin routes remain separate from the public marketing experience

## Customer Support And Feedback Operations Foundation

Buddybug now includes a first support operations layer for real user issues and product feedback.

What is included:

- support ticket categories for general support, billing issues, bug reports, content concerns, feature requests, and parental-controls questions
- user support flow for submitting tickets from the app/site and viewing owned tickets when authenticated
- internal editor/admin triage flow for queue filtering, status and priority updates, assignment, internal notes, resolving, and closing

Scope note:

- live chat, SLA automation, and external helpdesk integrations can come later

## KPI Dashboard And Executive Reporting Foundation

Buddybug now includes an internal reporting dashboard for practical SaaS and product-health monitoring.

What it shows:

- KPI overview for users, active families, child profile usage, premium conversion, published books, saves, downloads, and open support load
- engagement metrics driven by first-party analytics events such as opens, completions, replays, narration starts/completions, and daily story usage
- subscription signals, top content performance, language/age-band/content-lane breakdowns, and support resolution health

How it works:

- reporting is powered directly from existing operational models and analytics events including `User`, `ChildProfile`, `AnalyticsEvent`, `Book`, `UserLibraryItem`, and `SupportTicket`
- endpoints support simple time filters using `days` or explicit `start_date` / `end_date`

Scope note:

- this is an internal operational dashboard, not a full BI warehouse or external reporting stack

## Release Management And Feature Flags Foundation

Buddybug now includes a practical first feature-flag layer for staging releases more safely.

What feature flags are for:

- gradually rolling out unfinished or risky features without redeploying code
- targeting by environment, subscription tier, language, age band, role, country, explicit user IDs, and internal-only staff access
- controlling simple percentage rollouts with deterministic user or guest bucketing

How it works:

- feature flag definitions are stored in the backend and managed at `/admin/feature-flags`
- the frontend fetches a safe evaluated bundle from `GET /feature-flags/bundle` for the current auth, child-profile, and locale context
- missing or failed bundle fetches default to `false` in the client so the app remains usable

Scope note:

- this is a lightweight operational release-management foundation, not a full external flag platform or complex targeting DSL

## Privacy, Consent, And Data Retention Foundation

Buddybug now includes a first privacy foundation for parent accounts and child-profile-aware data operations.

What it covers:

- versioned tracking for terms of service and privacy policy acceptance
- stored privacy preferences for marketing, product updates, analytics personalization, and recommendation personalization
- user-created data export or deletion requests, with optional child-profile scope
- admin processing for JSON data exports without automatic destructive deletion

How it works:

- legal acceptance history is stored in `LegalAcceptance`
- current privacy settings are stored in `PrivacyPreference`
- export and deletion workflow records are stored in `DataRequest`
- the frontend uses `/privacy/me` plus related endpoints for a simple parent-facing Privacy & Data page

Scope note:

- this is the first operational privacy foundation only, not full COPPA/GDPR automation, identity verification, or legal workflow orchestration

## Referral And Gift Subscription Foundation

Buddybug now includes a lightweight growth foundation for parent referrals and shareable premium gifts.

What it covers:

- each authenticated user can get one personal referral code and track attributed signups plus later premium conversions
- registration accepts an optional referral code so attribution is stored at signup time
- authenticated users can create shareable gift subscription codes and recipients can redeem them after signup or login

How it works:

- referral ownership and usage are stored in `ReferralCode`
- attributed signups and premium conversions are stored in `ReferralAttribution`
- gift creation and redemption state are stored in `GiftSubscription`
- gift redemption grants local premium access by updating the existing subscription fields on the redeemed account

Scope note:

- this is the first gifting and referral foundation only, not a full affiliate system, payout engine, tax workflow, or promotions stack

## Mobile PWA And Offline Sync Foundation

Buddybug now includes a first browser-based mobile app layer with installability and lightweight offline reading support.

What it covers:

- the frontend is installable as a Progressive Web App with a manifest, icons, theme metadata, and a lightweight service worker
- premium families can save generated story packages onto the current browser device for offline reading later
- the reader falls back to a cached offline package when the network is unavailable
- selected actions such as reading progress and offline library markers can queue locally and flush after reconnect

Important limitations:

- "saved" and "available offline" are different states: a story can be saved in the online library without its package being cached on the current device
- browser offline support is device- and browser-specific; a story saved offline on one device is not automatically copied to another
- audio offline playback is best-effort and depends on whether the related assets were cached in the browser
- this is the first PWA foundation only, not a native app, DRM system, or complex sync/conflict engine

## App Store And Packaging Readiness Foundation

Buddybug now includes a packaging-readiness layer that keeps the PWA healthy while preparing the app shell for future wrapper-based distribution.

What it covers:

- centralized app runtime metadata in `buddybug_frontend/lib/app-config.ts`
- a cleaner mobile app shell with a reusable top bar, safe-area-friendly layout, and settings-first navigation
- a unified `/settings` hub for account, family, privacy, notifications, downloads, and about/support flows
- placeholder platform detection and public asset cleanup to make future Capacitor-style packaging easier

How to think about it:

- the current PWA remains the active product surface today
- a future packaged app can reuse this shell, settings structure, runtime config, and asset organization
- this stage does not add native iOS/Android code yet; it simply reduces the amount of restructuring needed later

## Onboarding And First-Run Experience Foundation

Buddybug now includes a resumable first-run onboarding flow that helps new families reach their first useful story session faster without blocking the rest of the product.

What it covers:

- a lightweight per-user onboarding state with resumable progress, skip-for-now support, and recommended next-route logic
- a mobile-friendly onboarding flow covering welcome, optional child setup, age band and language preferences, bedtime mode guidance, and first-story handoff
- gentle resume prompts on home and profile surfaces so setup can continue later without forcing redirects after skip or completion
- first-story activation hooks so opening a story during onboarding can mark the flow complete and move the user into normal library usage

How to think about it:

- onboarding is meant to reduce first-session friction, not gate access to the app
- child setup is encouraged but optional, and families can change language, age band, bedtime mode, and parental controls later
- the flow is intentionally simple today so it can support activation and retention improvements without becoming a heavy experiment system

## Re-engagement And Win-Back Foundation

Buddybug now includes a first re-engagement layer that helps quietly classify family activity and surface helpful return-to-reading prompts inside the app.

What it covers:

- derived engagement state categories such as `new_but_inactive`, `dormant_7d`, `dormant_30d`, `lapsed_premium`, `unfinished_story_user`, and `saved_but_unread_user`
- in-app reminder suggestions for continuing unfinished stories, revisiting saved stories, returning through a daily pick, restoring premium, and finishing family setup
- dismissible reminder cards on key authenticated surfaces so the product can nudge families without becoming spammy

How to think about it:

- this is a product-layer readiness step for retention, not a full lifecycle marketing platform
- suggestions are generated from existing reading, saved-library, child-profile, and subscription signals
- the same state and suggestion records can support future notification or campaign automation later without requiring that complexity today

## Seasonal Campaigns And Themed Content Foundation

Buddybug now includes a lightweight seasonal campaigns layer so the app can surface time-bound themed story moments without hardcoding one-off holidays into the product forever.

What it covers:

- admin-manageable seasonal campaigns with start and end windows, optional language and age-band targeting, homepage badge and CTA metadata, and ordered campaign books
- public campaign endpoints for active campaign banners and themed campaign detail pages
- homepage and discovery surfaces that can prioritize active themed content ahead of generic featured shelves when relevant

How to think about it:

- campaigns are a curated discovery layer, not a full CMS or promotions engine
- they still respect published-state rules, age bands, language context, and parental filtering
- the structure is intentionally simple so Buddybug can feel more alive throughout the year while staying easy to manage

## A/B Messaging And Paywall Optimization Foundation

Buddybug now includes a lightweight message experimentation layer so key conversion surfaces can vary copy without destabilizing the core product flow.

What it covers:

- sticky message variants for homepage CTA copy, preview-wall upsell messaging, pricing-page emphasis, and premium upgrade card copy
- a backend bundle endpoint that resolves safe default copy when no experiment context is available
- consistent exposure and click tracking for message variants, preview-wall upgrades, and pricing CTA interactions

How to think about it:

- this is a focused messaging layer on top of the existing experimentation foundation, not a full experimentation platform
- variants only adjust wording on a few high-impact surfaces rather than branching large parts of the UI
- the system is designed to make copy tests low-risk, observable, and easy to extend later

## Educator And Classroom Readiness Foundation

Buddybug now includes an initial educator layer so trusted teacher-style users can organize classroom-friendly reading sets without mixing those workflows directly into the family bedtime experience.

What it covers:

- an `is_educator` user role and educator-only API dependency for classroom-set management
- educator-managed classroom reading sets with ordered books, age-band context, and language targeting
- a lightweight educator workspace in the frontend for creating sets, editing details, and assigning published books

Current scope:

- this is a classroom-readiness foundation, not a full school admin suite
- there is no roster import, SSO, district licensing, or complex classroom permissions yet
- educator collections are intentionally separate from public family discovery for now, while remaining compatible with the shared content catalog

## Partnerships And Promo Access Foundation

Buddybug now includes a lightweight promo access layer for early partnerships, pilots, and community launches.

What it covers:

- admin-managed promo or partner access codes with date windows, redemption limits, and access types
- authenticated redemption flows that can safely grant temporary premium-style access using the existing subscription fields
- redemption history for both users and internal admins, plus audit and analytics hooks for launches and testing

Current scope:

- this is not a full enterprise contracts, invoicing, or entitlement-stacking system
- the first version focuses on clean temporary access grants and internal tracking for small partnership launches
- promo flows stay intentionally simple so Buddybug can support pilots and campaigns without destabilizing normal billing behavior

## Organization Accounts And Team Management Foundation

Buddybug now includes a first-pass organization layer for small internal teams and future B2B-style collaboration.

What it covers:

- organization records plus lightweight organization memberships with simple roles like owner, admin, editor, analyst, and support
- a single primary organization per user for now, with membership rows as the source of truth
- internal organization management UI for creating an org, adding members by user ID, and adjusting team roles

Current scope:

- this is not a full enterprise identity, SSO, contracts, or invoicing system
- permissions stay intentionally lightweight so shared editorial, support, and reporting workflows can evolve later without adding heavy complexity now
- the structure is designed to prepare Buddybug for cleaner team collaboration than a single shared admin account

## Customer Success And Account Health Foundation

Buddybug now includes a lightweight account health layer for internal success monitoring and prioritization.

What it covers:

- deterministic account health snapshots built from activity, child-profile setup, saved-library usage, support load, subscription state, and dormancy
- simple health bands: `healthy`, `watch`, `at_risk`, and `churned`
- admin-facing rebuild and list views for spotting thriving accounts, watchlist users, and potential churn risk

Current scope:

- this is not a CRM or ML scoring system
- the first version is intentionally rules-based and transparent so the team can understand why a score was assigned
- the model is designed to support future success workflows without adding heavyweight lifecycle automation yet

## Content Versioning And Rollback Foundation

Buddybug now keeps lightweight version snapshots for editorial story drafts and story pages so manual and AI-assisted content work can be changed more safely.

What it covers:

- automatic snapshot history for manual editorial edits, review edits, and rollback operations on `StoryDraft` and `StoryPage`
- editor-facing version history panels for draft and page content, with one-click rollback to an earlier snapshot
- monotonic version numbering so teams can trace content changes without introducing a full Git-style workflow

Current scope:

- this is not a full diffing or branching system
- the first version focuses on protecting draft/page content changes rather than versioning every content table in the platform
- rollback restores saved content fields only, keeping the workflow practical and predictable for editors and reviewers

## API Keys And External Integrations Foundation

Buddybug now supports a first-pass external integrations layer with scoped API keys for trusted server-to-server use.

What it covers:

- admin-issued API keys with a visible public prefix, a one-time raw secret reveal, and hashed storage at rest
- narrow scopes such as `reporting.read` and `books.read` enforced on dedicated read-only integration endpoints
- audit logging for API key lifecycle actions and integration usage so external access remains traceable

Current scope:

- this is not an OAuth provider, integrations marketplace, or broad partner API surface
- the first version intentionally exposes only a couple of safe read-only endpoints under `/integrations`
- API keys currently authenticate through `Authorization: Bearer bbk_live_...` and are intended for trusted backend-to-backend automations only

## Localization Operations And Translation Workflow Foundation

Buddybug now includes a lightweight translation operations layer so multilingual rollout work can be tracked intentionally instead of being handled ad hoc.

What it covers:

- translation tasks per `book/language` pair with simple states like `not_started`, `in_progress`, `in_review`, `completed`, and `blocked`
- admin/editor views for listing tasks, updating assignment and notes, and spotting missing translation opportunities for published books
- lightweight completeness checks against existing `BookTranslation` and `BookPageTranslation` records so finished translation coverage can automatically mark tasks complete

Current scope:

- this is not a full translation management system or external vendor integration
- the first version focuses on internal operational tracking rather than replacing the existing multilingual runtime delivery layer
- task assignment remains intentionally lightweight, using internal user IDs and simple notes to coordinate work

## Moderation Review Queue And Sensitive Content Escalation Foundation

Buddybug now includes a practical moderation queue so parent-reported content concerns and severe quality failures can be escalated into one internal review workflow.

What it covers:

- moderation cases with linked targets and sources for books, drafts, pages, support tickets, and quality checks
- editor/admin moderation views for queue triage, case detail review, assignment, manual escalation, resolution, and dismissal
- conservative automatic escalation from `content_concern` support tickets and failed quality-check runs so sensitive content review work is centralized without flooding the queue

Current scope:

- this is not a full trust-and-safety platform, policy engine, or external moderation integration
- the first version intentionally focuses on internal case tracking and sensitive-content escalation rather than broad automated enforcement
- auto-created cases are conservative and deduplicated so repeated quality runs or follow-up review work do not create noisy duplicate open cases

## Illustration Consistency Toolkit Foundation

Buddybug now includes a lightweight visual reference toolkit so editors can reuse approved character and style references as the illustration library grows.

What it covers:

- reusable visual reference assets for character sheets, style references, cover references, and scene references
- targetable references for `character`, `content_lane`, `editorial_project`, `book`, and `story_draft` records
- internal admin tools for listing, filtering, editing, and deleting references, plus lightweight editorial visibility for project- and draft-linked assets

Current scope:

- this is not an image-embedding search system, automated visual matching engine, or external asset DAM integration
- the first version focuses on structured reference storage and reuse rather than automatic style enforcement
- references stay intentionally simple: image URL, target linkage, language, active status, and reusable prompt notes for illustration planning

## Audit Timeline And Entity Activity Feed Foundation

Buddybug now includes a lightweight unified activity feed so internal staff can review what changed on key records without hunting through separate admin pages.

What it covers:

- per-entity activity feeds built around existing audit logs for records like editorial projects, story drafts, support tickets, and organizations
- selective blending of related operational events such as support ticket notes, moderation case links, and user-owned workflow/support activity
- one reusable admin timeline component used across a few high-value internal detail pages

Current scope:

- this is not a full event-sourcing or system-wide correlation engine
- the first version intentionally reuses existing audit and operational tables instead of rewriting Buddybug's logging architecture
- correlation stays lightweight and explicit so the feed remains understandable and production-friendly

## Changelog And Internal Release Notes Foundation

Buddybug now includes a lightweight changelog layer so internal teams can document releases cleanly and prepare simple user-facing "what's new" communication over time.

What it covers:

- changelog entries with version labels, summaries, optional details, audience, lifecycle status, and lightweight comma-separated area and feature-flag tags
- admin/editor tooling for creating, editing, publishing, archiving, and filtering release notes
- an optional public `what's new` surface backed only by published `user_facing` entries

Current scope:

- this is not a full docs CMS, release packaging workflow, or advanced markdown publishing system
- the first version keeps details rendering intentionally simple and focused on readable operational notes
- tagging is lightweight and string-based so launch areas and related feature flags can be tracked without adding heavyweight release management complexity

## Production Incident Management And Ops Runbooks Foundation

Buddybug now includes a lightweight internal incident operations layer so admins can track production issues, mitigation updates, and reusable recovery guides in one place.

What it covers:

- incident records with severity, status, affected area, assignment, customer impact, mitigation timestamps, and root-cause notes
- timeline updates for investigation progress, mitigation work, resolution notes, and postmortem-ready breadcrumbs
- lightweight runbook records for recurring operational scenarios, with simple area-based filtering and soft deactivation

Current scope:

- this is not a PagerDuty, Statuspage, or external on-call integration replacement
- the first version focuses on internal admin workflows, manual updates, and clean operational structure rather than automated escalation policies
- incident-to-runbook linkage stays intentionally lightweight by using affected area filtering in the admin console instead of building a full workflow engine

## Data Backfills And Maintenance Jobs Foundation

Buddybug now includes an internal maintenance jobs layer so admins can run bounded rebuilds and repair tasks without guessing directly in the database.

What it covers:

- repeatable maintenance job records with status, scope, timing, result payloads, and failure details
- first-pass supported jobs for discovery metadata rebuilds, account health rebuilds, reengagement rebuilds, content-lane backfills, download package repair, and a few adjacent internal rebuild types
- admin-only execution and audit logging so one-off repair work stays visible and controlled

Current scope:

- this is not a replacement for schema migrations, and it should not be used as a generic scripting console
- the first version intentionally runs only known supported maintenance handlers rather than arbitrary SQL or free-form code
- job execution is designed for internal operational maintenance and migration-adjacent recalculation, not distributed ETL or heavy background orchestration

## Housekeeping And Data Cleanup Policies Foundation

Buddybug now includes a dry-run-first housekeeping layer so admins can review cleanup pressure and retention candidates across selected operational tables before any low-risk cleanup action happens.

What it covers:

- housekeeping policy definitions with target table, action type, retention window, enabled state, and dry-run-only safeguards
- housekeeping run history with candidate counts, affected counts, result payloads, and failure details
- safe first targets for notification events, dismissed reengagement suggestions, maintenance jobs, and workflow jobs

Current scope:

- this is not a destructive deletion console and it does not touch critical user, billing, legal, subscription, child, or content records
- dry-run remains the default posture, and unsupported destructive actions are downgraded to reporting when the target is not safely mutable
- this foundation is intended for internal operational cleanup visibility and controlled low-risk maintenance, not archival warehousing or retention enforcement for critical tables

## Beta Cohorts And Early Access Program Foundation

Buddybug now includes a simple beta cohorts layer so admins can group selected users into early-access programs before unfinished features roll out broadly.

What it covers:

- beta cohort records with stable keys, lightweight notes, and optional linked feature flag keys
- per-user cohort memberships with active/inactive state, admin assignment, and operational history
- optional feature flag targeting through `target_beta_cohorts`, so a flag can require membership in one or more active cohorts in addition to its other targeting rules

Current scope:

- this is internal admin tooling for controlled previews, not a public waitlist, community platform, or full invite marketing system
- cohort assignment is intentionally simple and admin-driven in the first version, while leaving room for later invite-based enrollment
- the existing feature flag system remains the main release control layer, with beta cohorts acting as a narrow eligibility filter when needed

## Internal Search Console And Admin Command Palette Foundation

Buddybug now includes an internal search console and command palette foundation so staff can jump across key operational entities without digging through every admin section manually.

What it covers:

- a unified internal search API that groups lightweight matches across users, child profiles, books, story drafts, editorial projects, support tickets, incidents, campaigns, feature flags, and maintenance jobs
- a safe first command palette surface for route-based quick actions like opening the right admin workspace or copying an entity identifier
- a standalone `/admin/search` console plus an admin navigation trigger for faster internal movement

Current scope:

- this is an internal-only operational tool and it does not introduce broad full-text indexing or a dangerous universal admin console
- search uses simple bounded SQL matching with small per-group caps rather than external search infrastructure
- quick actions stay non-destructive in the first version, focusing on navigation and lightweight copy helpers instead of billing, deletion, or irreversible operations

## Public Status Page And Customer-Facing Service Health Foundation

Buddybug now includes a simple public status layer so families and partners can see current customer-facing service health, active incident notices, and scheduled maintenance without exposing internal-only incident detail.

What it covers:

- a public `/status` page with an overall service state, a small set of customer-safe components, and curated active/upcoming notices
- admin tooling for updating public component status and publishing customer-facing incident, maintenance, or informational notices
- optional explicit linking from a public notice to an internal incident record without automatic publication of internal summaries, root cause notes, or operational updates

Current scope:

- this is not a full external status-platform replacement and it intentionally keeps the component model small and customer-friendly
- public notices are explicit and curated by admins rather than auto-synced from internal incidents
- the public layer is designed to communicate customer impact and maintenance timing clearly while keeping sensitive internal debugging detail private

## Revenue Recovery And Failed Billing Follow-up Foundation

Buddybug now includes a first billing recovery layer for tracking failed premium renewals, surfacing calm in-app recovery prompts, and giving internal teams a practical recovery queue without replacing Stripe retry behavior.

What it covers:

- billing recovery cases and recovery events tied to affected users when Stripe-backed premium billing enters a problematic state such as `past_due`
- a user-facing recovery prompt under `/billing-recovery/me` that can drive families back to the existing billing portal and profile billing flow
- admin visibility under `/admin/billing-recovery/*` for reviewing open and historical cases, internal notes, and recorded recovery events

Important scope notes:

- Stripe remains the source of truth for paid subscription state and retries
- this foundation is not a full dunning platform and does not yet include external email/vendor automation
- gift and promo premium access should not create failed billing recovery cases by default because those flows are not treated as paid renewal failures

## Subscriber Lifecycle Timeline And Unified Account Journey Foundation

Buddybug now includes a first lifecycle timeline layer so internal teams can inspect one family account as a coherent journey instead of piecing together onboarding, support, billing, and engagement activity across multiple tools.

What it covers:

- lifecycle milestones derived from existing product systems such as account creation, onboarding, child profiles, reading progress, referrals, gifts, promo access, support tickets, billing recovery, and engagement state
- an admin lifecycle timeline under `/admin/lifecycle/users/{user_id}` with a lightweight summary, ordered milestones, and a manual rebuild action
- deterministic milestone upserts keyed by source table, source id, and milestone type so rebuilds stay low-noise

Important scope notes:

- this is a practical internal account-journey foundation, not a full CRM or orchestration engine
- the timeline is derived from current Buddybug tables and events where practical instead of duplicating every event system
- the main use cases are support troubleshooting, customer success context, and future lifecycle automation readiness

## Family Sharing And Read-Along Session Foundation

Buddybug now includes a first private read-along layer so one family account can create a shared story session, reopen it on another device, and keep a common page position in sync without introducing real-time socket infrastructure yet.

What it covers:

- authenticated families can create private read-along sessions for a book, optionally in a child-profile context, and receive a short join code
- only the same Buddybug account can join for now, keeping access private while still supporting simple parent-and-child multi-device continuation
- reader clients can poll shared state, update the current shared page, and end sessions without replacing the normal individual reading progress model

Important scope notes:

- read-along is online-only in this foundation and is intentionally separate from offline sync behavior
- sync is polling-based for now, which keeps the implementation practical while leaving room for richer future real-time collaboration
- there are no public share links, guest joins, or cross-account permissions in this first version

## Achievements And Family Motivation Foundation

Buddybug now includes a first calm achievement layer so families can notice gentle reading milestones, child-aware progress moments, and streak-style encouragement without pushing competitive or noisy gamification.

What it covers:

- seeded achievement definitions for early reading milestones such as first story completed, saved-story starts, narrated-story use, family library growth, and a simple seven-day streak
- earned achievement storage tied to the parent account with child-profile context where available, plus streak snapshots for account and child views
- a family-friendly `/achievements` page with earned badges, current and longest streaks, and a soft next-milestone hint

Important scope notes:

- this is a calm encouragement layer, not a leaderboard, points economy, or manipulative reward loop
- child-profile context is preferred when available, while the parent account can still review overall progress
- the foundation is designed to support future certificates or celebration moments without overbuilding the first version

## Parent Digest And Weekly Family Summary Foundation

Buddybug now includes a first parent-facing weekly digest layer so families can review a calm in-app summary of reading activity, child-friendly progress snapshots, achievements, narration use, and gentle next-step suggestions.

What it covers:

- persisted weekly family digests with optional child summary rows for active child profiles that had meaningful reading activity
- an in-app `/family-digest` page plus compact summary cards for key parent surfaces
- reusable digest payloads designed to support future weekly email delivery without building the email automation layer yet

Important scope notes:

- this is a warm summary layer, not detailed surveillance or a pressure-based scorecard
- child summaries stay high-level, positive, and parent-friendly rather than exposing every action in detail
- delivery is in-app first, with the stored digest shape intentionally kept clean for future notification or email reuse

## Smart Reading Plans And Routine Builder Foundation

Buddybug now includes a first reading-plan layer so parents can create flexible routines for the whole family or a specific child, then use those plans to guide upcoming sessions and calmer story suggestions.

What it covers:

- reusable reading plans for bedtime, narrated nights, language practice, family reading, or custom routines
- child-specific or family-wide plan scope with simple preferences for age band, language, content lane, narration, and target weekdays
- plan-aware story suggestions plus lightweight links into daily story suggestions and family digest context

Important scope notes:

- this is a soft routine builder, not a rigid calendar or productivity tracker
- plans are designed to guide gentle habits rather than enforce strict completion rules
- the foundation is meant to support future bedtime automation, educator routines, and longer habit tools without overbuilding the first version

## Personalized Bedtime Packs And Multi-Story Session Foundation

Buddybug now includes a first bedtime-pack layer so families can move from a single story to a calm multi-story evening session with a short, tailored sequence for a child or the whole family.

What it covers:

- generated bedtime packs with 2 to 4 ordered stories for a family account or child profile
- bedtime-safe sequencing that strongly prefers calm bedtime content, respects parental controls, and can gently bias toward narration when requested
- lightweight integration with reading plans and daily story suggestions so existing routines can feed a stronger tonight's-session experience

Important scope notes:

- this is a calm session builder, not a complex playlist or autoplay engine
- bedtime packs are meant to guide the evening gently rather than force a rigid reading order
- the foundation is designed to support future autoplay, printable routines, and premium bedtime surfaces without overbuilding the first version

## Child Preferences And Comfort Profile Foundation

Buddybug now includes a first child comfort profile layer so parents can keep story selection gentler and more personally suitable without turning preferences into rigid profiling.

What it covers:

- one parent-editable comfort profile per child profile with favorite characters, moods, story types, avoid-style tags, language preference, narration preference, and bedtime notes
- soft guidance for recommendations, reading plans, and bedtime packs so Buddybug can lean calmer, shorter, narrated, or more familiar when it helps
- a dedicated child comfort editing page with simple chip-style selections and calm, family-friendly language

Important scope notes:

- comfort preferences are lightweight content signals, not sensitive medical or psychological records
- avoid tags are used as soft steering where practical, not brittle hard blocks across the whole catalog
- bedtime notes stay parent-entered and reviewable rather than being inferred by AI

## AI Quality Review System

Buddybug now includes a first automated story quality and illustration consistency review layer so generated content can be checked quickly before it moves deeper into the pipeline.

What it covers:

- deterministic story review scoring for length, tone, age-band fit, narrative coherence, and character consistency
- illustration review scoring for style consistency, canonical character cues, palette calmness, and bedtime-friendly visual signals
- automatic flagging into an admin review queue when a story or illustration drops below the threshold or shows higher-severity brand or safety concerns

Important scope notes:

- this is a fast heuristic review layer, not a heavy ML moderation pipeline
- canonical character protection focuses on Buddybug universe consistency for names and expected visual cues rather than computer vision
- flagged items are routed for human review, but automated review does not block the broader generation foundation entirely

## Docker Run

Start the full stack with PostgreSQL, backend, and frontend:

```powershell
docker compose up --build
```

Default local ports:

- Postgres: `5432`
- Backend: `8000`
- Frontend: `3000`

The backend container runs `alembic upgrade head` automatically before starting Uvicorn via `docker/backend-entrypoint.sh`.

## Tests And Validation

Backend tests:

```powershell
pytest
```

Frontend validation:

```powershell
cd buddybug_frontend
npm run typecheck
npm run build
```

The pytest suite uses an isolated SQLite database and does not rely on your local dev database.

## CI

GitHub Actions is configured in `.github/workflows/ci.yml` to:

- install backend dependencies
- run backend startup/import validation
- run pytest
- install frontend dependencies
- run frontend typecheck
- run frontend production build

## Observability And Operational Safety

Buddybug now includes a lightweight production-safety layer:

- structured key=value logs via `app/logging_config.py`
- per-request `X-Request-ID` propagation
- machine-friendly `GET /health` and `GET /ready`
- admin-facing audit logs at `GET /admin/audit`
- in-memory rate limiting for sensitive auth and billing endpointsWhere to look in development:- backend logs print to stdout
- every response includes `X-Request-ID`
- error responses include `request_id` and `error_code`Notes:- the in-app rate limiting is a single-instance safety layer only
- production deployments should still add edge/proxy rate limiting
- audit logging is best-effort and should not block the main workflow if it fails## High-Level Deployment Notes- SQLite remains available for simple local development and isolated tests.
- PostgreSQL is the intended hosted database path through `DATABASE_URL`.
- Alembic is now the schema source of truth for deployed environments.
- Asset URL generation goes through `app/services/storage_service.py` so local storage can later be swapped for S3-compatible storage without rewriting downstream services.
