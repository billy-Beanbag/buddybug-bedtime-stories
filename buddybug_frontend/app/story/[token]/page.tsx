import Link from "next/link";
import Image from "next/image";

import { APP_URL } from "@/lib/prelaunch/config";
import { parseStoryPages } from "@/lib/prelaunch/story-content";
import { getStoryDeliveryByToken, markStoryDeliveryOpened } from "@/lib/prelaunch/service";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type StoryReaderPageProps = {
  params: Promise<{ token: string }>;
};

function InvalidStoryState({ expired = false }: { expired?: boolean }) {
  return (
    <section className="mx-auto max-w-3xl rounded-[2rem] border border-white/70 bg-white/90 p-8 text-center shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">Buddybug</p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-950">
        {expired ? "This story link has gone to sleep" : "We couldn't open this story link"}
      </h1>
      <p className="mt-4 text-sm leading-7 text-slate-600">
        The link may be invalid, expired, or already replaced. If you joined Buddybug recently, please open the newest
        story email in your inbox.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex rounded-full bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-[0_14px_30px_rgba(79,70,229,0.28)]"
      >
        Back to Buddybug
      </Link>
    </section>
  );
}

export default async function StoryReaderPage({ params }: StoryReaderPageProps) {
  const { token } = await params;
  const delivery = await getStoryDeliveryByToken(token);

  if (!delivery || !delivery.story.contentHtml) {
    return <InvalidStoryState />;
  }

  if (delivery.expiresAt && delivery.expiresAt.getTime() < Date.now()) {
    return <InvalidStoryState expired />;
  }

  const storyPages = parseStoryPages(delivery.story.pagesJson);

  await markStoryDeliveryOpened(delivery.id);

  return (
    <div className="mx-auto max-w-3xl">
      <section className="rounded-[2rem] border border-white/70 bg-white/92 p-6 shadow-[0_22px_60px_rgba(79,70,229,0.12)] sm:p-8">
        <div className="border-b border-indigo-100 pb-5">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-indigo-500">Buddybug bedtime story</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl">{delivery.story.title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            A private Buddybug story link for {delivery.subscriber.childFirstName}. Keep this email if you want to read the
            story again later while the link remains active.
          </p>
        </div>

        {delivery.story.coverImageUrl ? (
          <div className="mt-8 overflow-hidden rounded-[1.75rem] border border-indigo-100 bg-white shadow-sm">
            <Image
              src={delivery.story.coverImageUrl}
              alt={`${delivery.story.title} cover illustration`}
              width={1200}
              height={900}
              className="h-auto w-full object-cover"
              unoptimized
            />
          </div>
        ) : null}

        {storyPages.length ? (
          <div className="mt-8 space-y-8">
            {storyPages.map((page) => (
              <article key={page.pageNumber} className="overflow-hidden rounded-[1.75rem] border border-indigo-100 bg-white shadow-sm">
                {page.imageUrl ? (
                  <Image
                    src={page.imageUrl}
                    alt={page.imageAlt || `${delivery.story.title} page ${page.pageNumber} illustration`}
                    width={1200}
                    height={900}
                    className="h-auto w-full object-cover"
                    unoptimized
                  />
                ) : null}
                <div className="p-5 sm:p-6">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-500">Page {page.pageNumber}</p>
                  {page.heading ? <h2 className="mt-2 text-2xl font-semibold text-slate-950">{page.heading}</h2> : null}
                  <p className="mt-3 text-base leading-8 text-slate-700 sm:text-lg">{page.text}</p>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <article
            className="bb-story-html mt-8"
            // Story HTML is server-authored seed/editorial content, not subscriber input.
            dangerouslySetInnerHTML={{ __html: delivery.story.contentHtml }}
          />
        )}

        <div className="mt-10 rounded-[1.75rem] border border-indigo-100 bg-indigo-50/70 p-5 text-sm leading-7 text-slate-700">
          <p className="font-semibold text-slate-950">Why this page is private</p>
          <p className="mt-2">
            Buddybug pre-launch stories are shared only through secure email links. There is no public story library or
            public account area during pre-launch.
          </p>
          <p className="mt-3">
            If you would rather stop receiving stories, you can unsubscribe from the link in any Buddybug email.
          </p>
          <p className="mt-3 text-slate-500">Shared from {APP_URL}</p>
        </div>
      </section>
    </div>
  );
}
