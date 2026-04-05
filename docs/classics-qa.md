# Buddybug Classics QA

This document covers the first-pass test and QA workflow for the internal Buddybug Classics pipeline using two controlled fixture stories:

- `Goldilocks and the Three Bears`
- `Little Red Riding Hood`

## Scope

The goal of this QA pass is to verify that:

- a public-domain classic can be manually imported
- classics remain internal-only until explicitly published
- a Buddybug-enhanced draft can be generated safely
- the classic is not materially over-rewritten
- scene/page planning feeds the illustration pipeline correctly
- illustration generation and approval behave correctly
- approved classics can be published into the live library with `is_classic=true`
- unpublished imports and drafts never appear in public reader responses

## Controlled fixtures

Reusable test fixture helper:

- `tests/fixtures_classics.py`

Key helpers:

- `build_goldilocks_classic_payload()`
- `build_little_red_classic_payload()`
- `create_goldilocks_classic_source(session, current_user=...)`
- `create_little_red_classic_source(session, current_user=...)`

Fixture properties:

- title: `Goldilocks and the Three Bears`
- source text: short public-domain-safe internal fixture text
- source reference: `https://example.org/public-domain/goldilocks-test-fixture`
- `public_domain_verified = true`
- initial `import_status = imported`

Little Red fixture properties:

- title: `Little Red Riding Hood`
- source text: short public-domain-safe internal fixture text
- source reference: `https://example.org/public-domain/little-red-riding-hood-test-fixture`
- `public_domain_verified = true`
- initial `import_status = imported`

## Automated coverage

Primary workflow tests:

- `tests/test_classics_workflow.py`
- `tests/test_classic_adaptation_prompts.py`

Covered automatically:

- classics routes require editor/admin access
- admin/editor can import a classic source with required fields
- missing required import fields are rejected
- duplicate classic titles are rejected
- both controlled classic fixtures can be imported and adapted
- imported classics stay hidden from public reader queries
- adaptation draft creation works and returns structured fields
- preview books created during drafting remain unpublished and hidden
- validation rejects empty adapted text
- validation rejects meta-response output
- validation rejects missing cameo summary
- validation rejects clearly over-expanded rewrites and too many Buddybug named characters
- scene seed notes are generated and stored
- classic illustration prompts receive the classic-scene preservation enhancer
- illustration generation creates illustration records for classic pages
- illustration failures do not publish anything
- publish before approval is blocked
- illustration generation without a valid draft is blocked
- approved classics publish successfully
- published classics appear in `/reader/books`
- published classics appear in `/reader/books?is_classic=true`
- non-classic library entries remain visible and unaffected
- internal-only fields do not leak into public reader responses

## Mocked vs real services

Automated tests run in mocked mode by default via `tests/conftest.py`.

During tests:

- story LLM generation is disabled
- illustration generation uses mock generation
- narration generation uses mock generation

This is intentional. The automated QA suite verifies workflow safety, status changes, response shapes, and visibility rules without depending on external API uptime or billing state.

Manual QA can use real services if you want to verify actual live adaptation or illustration quality.

## Running the tests

From the repo root:

```bash
python -m pytest tests/test_classics_workflow.py tests/test_classic_adaptation_prompts.py
```

If you also want the frontend type check:

```bash
cd buddybug_frontend
npm run typecheck
```

## Manual QA checklist

Use these actual routes locally:

1. Sign in as an editor or admin user.
2. Open the classics import page at `/admin/classics`.
3. Import Goldilocks using the fixture values from `tests/fixtures_classics.py`.
4. Confirm the imported classic appears on `/admin/classics` with status `imported`.
5. Open the classic detail page at `/admin/classics/[sourceId]`.
6. Before adapting, open `/library` in another tab and confirm Goldilocks does not appear.
7. Click `Create Buddybug Draft`.
8. Confirm the draft view now shows:
   `adapted_title`
   adapted text
   adaptation intensity
   validation status
   cameo insertion notes as readable review items
   adaptation notes as readable review items
   validation warnings as reviewer-friendly notices
   scene seed notes as readable cards
9. Confirm the source status is now `drafted`.
10. Try opening the preview book from the draft context and confirm it is not visible through public reader routes yet.
11. Click `Generate illustrations`.
12. Confirm page illustrations are created and tied to the draft pages.
13. Review the classic detail page and confirm the prompt/scene planning still reflects iconic Goldilocks beats rather than a full Buddybug rewrite.
14. Approve the illustrations through the existing illustration review flow if needed.
15. Click `Approve draft`.
16. Click `Publish to library`.
17. Open `/library` and confirm Goldilocks now appears as a published classic.
18. Confirm the classic appears in the full library listing.
19. Confirm the classic appears when filtering for classics.
20. Confirm any other unpublished classic imports or drafts are still absent from `/library` and `/reader/books`.
21. Repeat the same flow with `Little Red Riding Hood` to confirm the pipeline behaves safely on a different classic structure.

## Known limitations of this first QA pass

- The automated suite verifies structural and safety rules, not deep literary judgment.
- The changed-ending detection is intentionally lightweight and heuristic.
- Manual QA is still required to assess whether cameo placement feels editorially tasteful.
- Manual QA is still required for live LLM output quality and live illustration quality.
- The review UI is clearer now, but deeper editorial comparison still depends on human review rather than an automated literary diff.

## Recommended first batch process

Before importing many classics:

1. Run the automated tests above.
2. Manually complete the Goldilocks workflow once locally.
3. Manually complete the Little Red Riding Hood workflow once locally.
4. Only then begin larger batch imports.
