from sqlmodel import Session, select

from app.models import StoryPage
from app.services.classic_adaptation_validation import VALIDATION_REJECTED, validate_classic_adaptation_output
from app.services.classic_prompt_templates import (
    ClassicAdaptationStructuredResponse,
    ClassicCameoInsertionSummaryItem,
    build_classic_adaptation_system_prompt,
    build_classic_adaptation_user_prompt,
)
from app.services.classics_service import create_classic_adaptation, create_classic_source
from tests.fixtures_classics import GOLDILOCKS_TEST_SOURCE_TEXT


def _goldilocks_source_text() -> str:
    return GOLDILOCKS_TEST_SOURCE_TEXT


def test_classic_adaptation_prompts_include_strict_preservation_rules(session: Session, editor_user):
    source_text = _goldilocks_source_text()
    classic_source = create_classic_source(
        session,
        current_user=editor_user,
        title="Goldilocks and the Three Bears",
        source_text=source_text,
        source_url="https://example.org/goldilocks",
        public_domain_verified=True,
        source_author="Traditional",
        source_origin_notes="Public-domain mock sample",
    )
    system_prompt = build_classic_adaptation_system_prompt()
    user_prompt = build_classic_adaptation_user_prompt(
        session,
        classic_source=classic_source,
        adaptation_intensity="light",
    )

    assert "Do not change the ending." in system_prompt
    assert "Add less rather than more." in system_prompt
    assert "Do not improve the story by rewriting it; preserve it." in system_prompt
    assert "Adaptation intensity: light" in user_prompt
    assert '"sceneSeedNotes": [' in user_prompt
    assert "Usually only 1 to 3 Buddybug cameo presences" in user_prompt


def test_classic_adaptation_validation_rejects_meta_rewrite_patterns():
    adapted = ClassicAdaptationStructuredResponse(
        adaptedTitle="Goldilocks but Buddybug Explains It",
        adaptedText=(
            "Here is your adapted version: Title: Goldilocks. "
            "Buddybug, Verity, Daphne, Dolly, Twinklet, Whisperwing, and Glowmoth all arrived to explain the story."
        ),
        cameoInsertionsSummary=[
            ClassicCameoInsertionSummaryItem(
                insertionLabel="opening rewrite",
                approximateLocation="everywhere",
                characters=["Buddybug", "Verity", "Daphne", "Dolly"],
                reason="rewrote the whole thing",
                plotPreservationNote="not really preserved",
            )
        ],
        adaptationNotes=["Large rewrite performed"],
        sceneSeedNotes=[],
    )

    result = validate_classic_adaptation_output(
        source_text=_goldilocks_source_text(),
        adapted=adapted,
    )

    assert result.status == VALIDATION_REJECTED
    assert any("meta-response" in error for error in result.errors)


def test_classic_adaptation_validation_rejects_empty_adapted_text():
    adapted = ClassicAdaptationStructuredResponse(
        adaptedTitle="Goldilocks and the Three Bears",
        adaptedText="",
        cameoInsertionsSummary=[
            ClassicCameoInsertionSummaryItem(
                insertionLabel="opening woodland transition",
                approximateLocation="opening",
                characters=["Buddybug"],
                reason="Tiny witness moment",
                plotPreservationNote="Original plot preserved.",
            )
        ],
        adaptationNotes=["Original plot preserved"],
        sceneSeedNotes=[],
    )

    result = validate_classic_adaptation_output(source_text=_goldilocks_source_text(), adapted=adapted)

    assert result.status == VALIDATION_REJECTED
    assert "Adapted text is empty." in result.errors


def test_classic_adaptation_validation_rejects_missing_cameo_summary():
    adapted = ClassicAdaptationStructuredResponse(
        adaptedTitle="Goldilocks and the Three Bears",
        adaptedText=_goldilocks_source_text(),
        cameoInsertionsSummary=[],
        adaptationNotes=["Original plot preserved"],
        sceneSeedNotes=[],
    )

    result = validate_classic_adaptation_output(source_text=_goldilocks_source_text(), adapted=adapted)

    assert result.status == VALIDATION_REJECTED
    assert "No cameo insertion summary items were returned." in result.errors


def test_classic_adaptation_validation_flags_large_rewrite_and_too_many_characters():
    adapted = ClassicAdaptationStructuredResponse(
        adaptedTitle="Goldilocks and the Three Bears",
        adaptedText=(
            (_goldilocks_source_text() + "\n\n") * 3
            + "Buddybug, Verity, Daphne, Dolly, Twinklet, Whisperwing, and Glowmoth all stayed for a long new subplot."
        ),
        cameoInsertionsSummary=[
            ClassicCameoInsertionSummaryItem(
                insertionLabel="major rewrite",
                approximateLocation="entire story",
                characters=["Buddybug", "Verity", "Daphne", "Dolly", "Twinklet"],
                reason="Expands many scenes",
                plotPreservationNote="Original plot preserved in broad outline.",
            )
        ],
        adaptationNotes=["Expanded draft"],
        sceneSeedNotes=[],
    )

    result = validate_classic_adaptation_output(source_text=_goldilocks_source_text(), adapted=adapted)

    assert result.status == VALIDATION_REJECTED
    assert any("dramatically longer" in error for error in result.errors)
    assert any("Too many Buddybug characters" in error for error in result.errors)


def test_create_classic_adaptation_stores_validation_and_classic_prompt_enhancer(session: Session, editor_user):
    classic_source = create_classic_source(
        session,
        current_user=editor_user,
        title="Goldilocks and the Three Bears",
        source_text=_goldilocks_source_text(),
        source_url="https://example.org/goldilocks",
        public_domain_verified=True,
        source_author="Traditional",
        source_origin_notes="Public-domain mock sample",
    )

    classic_draft = create_classic_adaptation(
        session,
        current_user=editor_user,
        classic_source=classic_source,
        age_band="3-7",
        content_lane_key="bedtime_3_7",
        language="en",
        adaptation_intensity="light",
        min_pages=5,
        max_pages=6,
    )

    pages = list(
        session.exec(
            select(StoryPage)
            .where(StoryPage.story_draft_id == classic_draft.story_draft_id)
            .order_by(StoryPage.page_number)
        ).all()
    )

    assert classic_draft.adaptation_intensity == "light"
    assert classic_draft.validation_status in {"accepted", "accepted_with_warnings"}
    assert classic_draft.scene_seed_notes_json is not None
    assert pages
    assert "Classic story illustration mode:" in pages[0].illustration_prompt
    assert "do not add one visually" in pages[0].illustration_prompt
