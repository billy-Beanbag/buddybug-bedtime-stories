from __future__ import annotations

from datetime import timedelta

from sqlmodel import Session, select

from app.models import Book, SeasonalCampaign, SeasonalCampaignItem
from app.services.review_service import utc_now

CANONICAL_SEASONAL_CAMPAIGNS = [
    {
        "key": "spring_storylight",
        "title": "Spring Storylight",
        "description": "Fresh seasonal reads for bright, gentle family story moments.",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
        "homepage_badge_text": "Seasonal picks",
        "homepage_cta_label": "Explore spring stories",
        "homepage_cta_route": "/campaigns/spring_storylight",
        "banner_style_key": "spring_glow",
    },
    {
        "key": "cozy_bedtime_favorites",
        "title": "Cozy Bedtime Favorites",
        "description": "A soft collection of calming favorites for easy evening reading.",
        "language": "en",
        "age_band": "3-7",
        "content_lane_key": "bedtime_3_7",
        "homepage_badge_text": "Tonight's theme",
        "homepage_cta_label": "Open cozy favorites",
        "homepage_cta_route": "/campaigns/cozy_bedtime_favorites",
        "banner_style_key": "cozy_night",
    },
]


def seed_seasonal_campaigns(session: Session) -> None:
    """Insert a small set of idempotent starter campaigns."""
    now = utc_now()
    published_books = list(
        session.exec(
            select(Book)
            .where(Book.published.is_(True), Book.publication_status == "published")
            .order_by(Book.updated_at.desc(), Book.id.desc())
        ).all()
    )

    for offset, payload in enumerate(CANONICAL_SEASONAL_CAMPAIGNS):
        campaign = session.exec(select(SeasonalCampaign).where(SeasonalCampaign.key == payload["key"])).first()
        if campaign is None:
            campaign = SeasonalCampaign(
                key=str(payload["key"]),
                title=str(payload["title"]),
                description=payload["description"],
                start_at=now - timedelta(days=30 + offset),
                end_at=now + timedelta(days=365),
                is_active=True,
                language=payload["language"],
                age_band=payload["age_band"],
                content_lane_key=payload["content_lane_key"],
                homepage_badge_text=payload["homepage_badge_text"],
                homepage_cta_label=payload["homepage_cta_label"],
                homepage_cta_route=payload["homepage_cta_route"],
                banner_style_key=payload["banner_style_key"],
            )
            session.add(campaign)
            session.commit()
            session.refresh(campaign)

        matching_books = [
            book
            for book in published_books
            if (campaign.language is None or book.language == campaign.language)
            and (campaign.age_band is None or book.age_band == campaign.age_band)
            and (campaign.content_lane_key is None or book.content_lane_key == campaign.content_lane_key)
        ][:4]

        for position, book in enumerate(matching_books, start=1):
            existing_item = session.exec(
                select(SeasonalCampaignItem).where(
                    SeasonalCampaignItem.campaign_id == campaign.id,
                    SeasonalCampaignItem.book_id == book.id,
                )
            ).first()
            if existing_item is None:
                session.add(
                    SeasonalCampaignItem(
                        campaign_id=campaign.id,
                        book_id=book.id,
                        position=position,
                    )
                )
    session.commit()
