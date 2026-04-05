from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.database import get_session
from app.middleware.rate_limit import rate_limiter
from app.main import app
import app.config as app_config
import app.services.classic_adaptation_service as classic_adaptation_service
import app.services.illustration_generation_service as illustration_generation_service
import app.services.illustration_generator as illustration_generator
import app.services.story_generation_service as story_generation_service
import app.services.story_idea_llm as story_idea_llm
import app.services.story_writer as story_writer_service
import app.services.tts_adapter as tts_adapter
from app.services import workflow_service
from app.utils.seed_beta_cohorts import seed_beta_cohorts
from app.utils.seed_characters import seed_characters
from app.utils.seed_content_lanes import seed_content_lanes
from app.utils.seed_achievements import seed_achievements
from app.utils.seed_housekeeping_policies import seed_housekeeping_policies
from app.utils.seed_public_status_components import seed_public_status_components
from app.utils.seed_voices import seed_voices
from tests.utils import create_demo_pipeline, create_test_user, make_auth_headers


@pytest.fixture()
def session(tmp_path: Path) -> Session:
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed_characters(session)
        seed_achievements(session)
        seed_beta_cohorts(session)
        seed_content_lanes(session)
        seed_voices(session)
        seed_housekeeping_policies(session)
        seed_public_status_components(session)
        yield session

    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def reset_rate_limiter_state():
    rate_limiter._events.clear()
    yield
    rate_limiter._events.clear()


@pytest.fixture(autouse=True)
def force_test_generation_modes(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(app_config, "STORY_GENERATION_API_KEY", "")
    monkeypatch.setattr(app_config, "STORY_GENERATION_MODEL", "")
    monkeypatch.setattr(app_config, "STORY_GENERATION_REQUIRE_LIVE", False)
    monkeypatch.setattr(app_config, "STORY_IDEA_GENERATION_USE_LLM", False)
    monkeypatch.setattr(app_config, "ILLUSTRATION_GENERATION_PROVIDER", "mock")
    monkeypatch.setattr(app_config, "ILLUSTRATION_GENERATION_API_KEY", "")
    monkeypatch.setattr(app_config, "ILLUSTRATION_GENERATION_MODEL", "")
    monkeypatch.setattr(app_config, "NARRATION_TTS_PROVIDER", "mock")
    monkeypatch.setattr(app_config, "NARRATION_TTS_REQUIRE_LIVE", False)
    monkeypatch.setattr(app_config, "ELEVENLABS_API_KEY", "")
    monkeypatch.setattr(app_config, "ELEVENLABS_VOICE_IDS_BY_KEY", {})
    monkeypatch.setattr(app_config, "ELEVENLABS_VOICE_SETTINGS_BY_KEY", {})

    monkeypatch.setattr(illustration_generation_service, "ILLUSTRATION_GENERATION_API_KEY", "")
    monkeypatch.setattr(illustration_generation_service, "ILLUSTRATION_GENERATION_MODEL", "")
    monkeypatch.setattr(illustration_generator, "ILLUSTRATION_GENERATION_PROVIDER", "mock")
    monkeypatch.setattr(classic_adaptation_service, "STORY_GENERATION_API_KEY", "")
    monkeypatch.setattr(classic_adaptation_service, "STORY_GENERATION_MODEL", "")
    monkeypatch.setattr(story_generation_service, "STORY_GENERATION_API_KEY", "")
    monkeypatch.setattr(story_generation_service, "STORY_GENERATION_MODEL", "")
    monkeypatch.setattr(story_idea_llm, "STORY_GENERATION_API_KEY", "")
    monkeypatch.setattr(story_idea_llm, "STORY_GENERATION_MODEL", "")
    monkeypatch.setattr(story_idea_llm, "STORY_IDEA_GENERATION_USE_LLM", False)
    monkeypatch.setattr(story_writer_service, "STORY_GENERATION_API_KEY", "")
    monkeypatch.setattr(story_writer_service, "STORY_GENERATION_MODEL", "")
    monkeypatch.setattr(story_writer_service, "STORY_GENERATION_REQUIRE_LIVE", False)
    monkeypatch.setattr(tts_adapter, "NARRATION_TTS_PROVIDER", "mock")
    monkeypatch.setattr(tts_adapter, "NARRATION_TTS_REQUIRE_LIVE", False)
    monkeypatch.setattr(tts_adapter, "ELEVENLABS_API_KEY", "")
    monkeypatch.setattr(tts_adapter, "ELEVENLABS_VOICE_IDS_BY_KEY", {})
    monkeypatch.setattr(tts_adapter, "ELEVENLABS_VOICE_SETTINGS_BY_KEY", {})
    yield


@pytest.fixture()
def client(session: Session) -> TestClient:
    def override_get_session():
        yield session

    @asynccontextmanager
    async def noop_lifespan(_: FastAPI):
        yield

    original_lifespan = app.router.lifespan_context
    original_workflow_engine = workflow_service.engine
    app.router.lifespan_context = noop_lifespan
    app.dependency_overrides[get_session] = override_get_session
    workflow_service.engine = session.get_bind()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
    workflow_service.engine = original_workflow_engine


@pytest.fixture()
def admin_user(session: Session):
    return create_test_user(
        session,
        email="admin@test.local",
        password="Admin123!",
        display_name="Admin Test",
        is_admin=True,
        subscription_tier="premium",
        subscription_status="active",
    )


@pytest.fixture()
def normal_user(session: Session):
    return create_test_user(
        session,
        email="user@test.local",
        password="User12345!",
        display_name="User Test",
        subscription_tier="free",
        subscription_status="none",
    )


@pytest.fixture()
def premium_user(session: Session):
    return create_test_user(
        session,
        email="premium@test.local",
        password="Premium123!",
        display_name="Premium Test",
        subscription_tier="premium",
        subscription_status="active",
    )


@pytest.fixture()
def editor_user(session: Session):
    return create_test_user(
        session,
        email="editor@test.local",
        password="Editor123!",
        display_name="Editor Test",
        is_editor=True,
        subscription_tier="premium",
        subscription_status="active",
    )


@pytest.fixture()
def educator_user(session: Session):
    return create_test_user(
        session,
        email="educator@test.local",
        password="Educator123!",
        display_name="Educator Test",
        is_educator=True,
        subscription_tier="premium",
        subscription_status="active",
    )


@pytest.fixture()
def admin_token_headers(admin_user):
    return make_auth_headers(admin_user)


@pytest.fixture()
def user_token_headers(normal_user):
    return make_auth_headers(normal_user)


@pytest.fixture()
def premium_token_headers(premium_user):
    return make_auth_headers(premium_user)


@pytest.fixture()
def editor_token_headers(editor_user):
    return make_auth_headers(editor_user)


@pytest.fixture()
def educator_token_headers(educator_user):
    return make_auth_headers(educator_user)


@pytest.fixture()
def demo_published_book(session: Session):
    return create_demo_pipeline(session, with_audio=False)["book"]
