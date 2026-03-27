# Buddybug Pre-Launch Setup

This pre-launch mode turns the Next.js app into a locked-down landing-page system.

## Environment variables

Set these in local `.env.local` and in Vercel:

```bash
NEXT_PUBLIC_PRELAUNCH_MODE=true
NEXT_PUBLIC_APP_URL=https://your-domain.example
DATABASE_URL=postgres://...
DIRECT_URL=postgres://...
RESEND_API_KEY=re_...
EMAIL_FROM=Buddybug <stories@updates.buddybug.app>
SUPPORT_EMAIL=support@buddybug.app
CRON_SECRET=choose-a-long-random-secret
STORY_TOKEN_TTL_DAYS=365
```

## Local development

1. Install dependencies:

```bash
npm install
```

2. Generate the Prisma client:

```bash
npm run prisma:generate
```

3. Apply the schema to your Postgres database:

```bash
npm run prisma:push
```

4. Seed the sample bedtime stories:

```bash
npm run db:seed
```

5. Start the Next.js app:

```bash
npm run dev
```

## Production deployment on Vercel

1. Point Vercel at the `buddybug_frontend` project root.
2. Add all environment variables listed above.
3. Use a Postgres database from Supabase or Neon.
4. Set the build command to the default Next.js build.
5. Ensure `NEXT_PUBLIC_PRELAUNCH_MODE=true` in production so the middleware locks down every non-prelaunch route.
6. Configure a verified sending domain in Resend so `EMAIL_FROM` can send successfully.
7. The included `vercel.json` schedules the weekly story cron for Monday at 18:00 UTC.

## Operational notes

- Signup is rate-limited in the database to reduce bot abuse.
- Every story delivery stores a unique token and a delivery record so the same story is not sent twice to the same subscriber.
- Weekly cron runs are protected by `CRON_SECRET`.
- Unsubscribe links operate through a token rather than exposing the subscriber email address.
- Launch-day personalised gifts can be queued later using the `PersonalizedGift` table that is already in the schema.
