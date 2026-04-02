# Buddybug Deployment Guide

Deploy Buddybug to the internet using **GitHub**, **Vercel** (frontend), **Render** (backend + database), and **Stripe** (payments).

---

## Prerequisites

- [x] GitHub account
- [x] Vercel account
- [x] Render account
- [x] Stripe account (test mode for sandbox)

---

## Step 1: Push to GitHub

1. **Create a new repository** on [GitHub](https://github.com/new)
   - Name it e.g. `BuddyBug` or `buddybug`
   - Choose Public
   - Do **not** initialize with README (you already have code)

2. **Push your code**:
   ```powershell
   cd C:\Users\User\Documents\BuddyBug
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git add .
   git commit -m "Prepare for deployment"
   git push -u origin main
   ```

3. If you already have a remote, update and push:
   ```powershell
   git remote -v
   git add .
   git commit -m "Add deployment config"
   git push origin main
   ```

---

## Step 2: Deploy Backend on Render

1. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**

2. Connect your GitHub account and select your BuddyBug repository

3. Render will detect `render.yaml` and create:
   - **PostgreSQL database** (buddybug-db)
   - **Web service** (buddybug-api) from the Dockerfile

4. Click **Apply** to create the resources

5. **Wait for the first deploy** – it may fail until env vars are set. That's OK.

6. **Add Environment Variables** (Settings → Environment for buddybug-api):
   | Variable | Value |
   |----------|-------|
   | `CORS_ALLOW_ORIGINS` | `https://your-app.vercel.app` *(see Step 3 – add after Vercel deploy)* |
   | `CORS_ALLOW_ORIGIN_REGEX` | *(optional)* `^https://.*\.vercel\.app$` — matches all Vercel preview + production URLs on `*.vercel.app` |
   | `STORY_GENERATION_API_KEY` | your live model provider key |
   | `STORY_GENERATION_MODEL` | e.g. `gpt-4.1` |
   | `STORY_GENERATION_BASE_URL` | `https://api.openai.com/v1` |
   | `STORY_GENERATION_TIMEOUT_SECONDS` | `45` |
   | `STORY_IDEA_GENERATION_USE_LLM` | `true` |
   | `ILLUSTRATION_GENERATION_PROVIDER` | `openai` |
   | `ILLUSTRATION_GENERATION_API_KEY` | your live image provider key |
   | `ILLUSTRATION_GENERATION_MODEL` | `gpt-image-1` |
   | `ILLUSTRATION_GENERATION_BASE_URL` | `https://api.openai.com/v1` |
   | `ILLUSTRATION_GENERATION_TIMEOUT_SECONDS` | `90` |
   | `ILLUSTRATION_GENERATION_DEBUG` | `false` *(set `true` only while debugging provider calls)* |
   | `STRIPE_SECRET_KEY` | `sk_test_...` from [Stripe Dashboard → Developers → API keys](https://dashboard.stripe.com/test/apikeys) |
   | `STRIPE_WEBHOOK_SECRET` | *(add after Step 4)* |
   | `STRIPE_PRICE_ID_PREMIUM_MONTHLY` | `price_...` from Stripe Products/Prices |
   | `STRIPE_SUCCESS_URL` | `https://your-app.vercel.app/profile?billing=success` |
   | `STRIPE_CANCEL_URL` | `https://your-app.vercel.app/profile?billing=cancel` |
   | `STORAGE_PUBLIC_BASE_URL` | `https://buddybug-api.onrender.com` *(your Render service URL)* |
   | `STORAGE_LOCAL_BASE_PATH` | mount path of your Render persistent disk, e.g. `/var/data` |

7. For `CORS_ALLOW_ORIGINS`, include all origins that will call the API:
   - Production: `https://your-app.vercel.app` (no trailing slash; do not wrap in quotes)
   - Preview deploys: either list each `https://…vercel.app` URL, **or** set `CORS_ALLOW_ORIGIN_REGEX` to `^https://.*\.vercel\.app$` (covers previews and production on Vercel).
   - **Environment groups:** variables in a group apply only after you **link** the group on **`buddybug-api` → Environment → Linked Environment Groups**, or copy the same keys onto the service directly.

8. **Trigger a manual redeploy** after setting variables

   For story ideas specifically: if `STORY_GENERATION_API_KEY` or `STORY_GENERATION_MODEL` is missing on Render, `/story-ideas/generate` will silently fall back to curated ideas even though local AI generation works.

   For illustrations specifically: if `ILLUSTRATION_GENERATION_PROVIDER` is left as `mock`, or if the image API key/model are missing, the app will keep generating placeholders instead of live AI artwork.

9. **Attach persistent storage for generated images** on paid Render plans

   Live illustrations are currently stored on the backend filesystem. For production, attach a persistent disk in Render and set `STORAGE_LOCAL_BASE_PATH` to that mount path so generated images survive restarts and redeploys.

   Without a persistent disk, generated artwork may disappear after a deploy or instance replacement even if the database rows still exist.

10. **Copy your backend URL** – e.g. `https://buddybug-api.onrender.com`

---

## Step 3: Deploy Frontend on Vercel

1. Go to [Vercel](https://vercel.com) → **Add New** → **Project**

2. Import your GitHub repository

3. **Configure the project**:
   - **Root Directory**: `buddybug_frontend` (important – this is a monorepo)
   - **Framework Preset**: Next.js (auto-detected)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: (leave default)

4. **Environment Variables**:
   | Name | Value |
   |------|-------|
   | `NEXT_PUBLIC_API_BASE_URL` | `https://buddybug-api.onrender.com` *(your Render backend URL)* |

5. Click **Deploy**

6. **Copy your frontend URL** – e.g. `https://buddybug-xxx.vercel.app`

7. **Update Render** – add your Vercel URL to `CORS_ALLOW_ORIGINS` in the Render service env vars:
   ```
   https://buddybug-xxx.vercel.app
   ```
   Then redeploy the Render service.

---

## Step 4: Stripe Webhook (for payments)

1. In [Stripe Dashboard](https://dashboard.stripe.com) → **Developers** → **Webhooks** → **Add endpoint**

2. **Endpoint URL**: `https://YOUR-RENDER-SERVICE.onrender.com/billing/webhook`

3. **Events to send**: Select `checkout.session.completed`, `customer.subscription.*`, or whatever your billing router expects

4. Copy the **Signing secret** (`whsec_...`)

5. Add to Render: `STRIPE_WEBHOOK_SECRET` = `whsec_...`

6. Redeploy the Render service

---

## Step 5: Seed Demo Data (optional)

After the first deploy, the database is empty. To seed demo users and content:

1. **Option A – Run locally against production DB** (temporary):
   - Set `DATABASE_URL` to your Render PostgreSQL connection string (from Render Dashboard → buddybug-db → Connect)
   - Run: `python scripts/seed_demo.py`
   - Or: `python scripts/fix_dev_setup.py` for admin user only

2. **Option B – Add a one-time deploy script** (advanced): Create a Render cron job or script that runs the seed once.

3. **Option C – Use the app** to sign up and create content through the UI.

---

## Step 6: Verify Auto-Deploy

- **Vercel**: Pushes to `main` (or your production branch) auto-deploy the frontend
- **Render**: Pushes to `main` auto-deploy the backend (if enabled in Dashboard)

Push a small change and confirm both redeploy.

---

## Summary Checklist

- [ ] Code pushed to GitHub
- [ ] Render Blueprint deployed (PostgreSQL + backend)
- [ ] Render env vars set (CORS, Stripe, STORAGE_PUBLIC_BASE_URL)
- [ ] Vercel project created with Root Directory = `buddybug_frontend`
- [ ] Vercel env var `NEXT_PUBLIC_API_BASE_URL` = Render backend URL
- [ ] `CORS_ALLOW_ORIGINS` on Render includes Vercel URL
- [ ] Stripe webhook configured and `STRIPE_WEBHOOK_SECRET` set
- [ ] Demo data seeded (optional)
- [ ] Test login and basic flows

---

## Notes

- **Render free tier**: Service sleeps after ~15 min inactivity; first request may take 30–60 seconds to wake.
- **Storage**: Local storage on Render is ephemeral. For persistent uploads, configure S3 (see `.env.example`).
- **Stripe test mode**: Use `pk_test_...` and `sk_test_...` for sandbox. Switch to live keys for production.
