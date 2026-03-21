from pydantic import BaseModel, Field


class StoryOutline(BaseModel):
    opening_hook: str
    problem: str
    event: str
    resolution: str
    gentle_ending: str


class IllustrationScene(BaseModel):
    key: str
    label: str
    text: str
    focus_characters: list[str] = Field(default_factory=list)
    location_hint: str | None = None
    action: str | None = None
    emotion: str | None = None
    must_show: list[str] = Field(default_factory=list)
    must_not_show: list[str] = Field(default_factory=list)
    continuity_notes: list[str] = Field(default_factory=list)


class StoryBeatCard(BaseModel):
    ordinary_world: str
    inciting_moment: str
    problem_escalation: str
    comic_or_surprising_reveal: str
    turning_point: str
    resolution_action: str
    final_emotional_beat: str
    illustration_beats: list[str] = Field(default_factory=list)


class StoryBrief(BaseModel):
    mode: str
    target_age_band: str
    hook_type: str
    tone: str
    theme: str
    setting: str
    bedtime_feeling: str
    humour_level: str
    tension_ceiling: str
    target_word_count: int
    main_characters: list[str] = Field(default_factory=list)
    supporting_characters: list[str] = Field(default_factory=list)
    series_key: str | None = None
    series_title: str | None = None
    generation_rules: list[str] = Field(default_factory=list)
    style_reference_titles: list[str] = Field(default_factory=list)
    style_reference_examples: list[str] = Field(default_factory=list)
    beat_card: StoryBeatCard


class StoryValidationIssue(BaseModel):
    code: str
    message: str
    severity: str
    deduction: int


class StoryValidationResult(BaseModel):
    score: int
    review_required: bool
    selected_source: str
    selected_prompt: str | None = None
    candidate_count: int = 0
    used_fallback: bool = False
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[StoryValidationIssue] = Field(default_factory=list)


class StoryMetadata(BaseModel):
    mode: str
    hook_type: str
    series_key: str | None = None
    series_title: str | None = None
    tone: str
    target_age_band: str
    setting: str
    theme: str
    bedtime_feeling: str
    main_characters: list[str] = Field(default_factory=list)
    supporting_characters: list[str] = Field(default_factory=list)
    style_reference_titles: list[str] = Field(default_factory=list)
    style_reference_examples: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class StoryPipelineResult(BaseModel):
    story_brief: StoryBrief
    story_validation: StoryValidationResult
    story_outline: StoryOutline
    final_story_text: str
    illustration_scenes: list[IllustrationScene] = Field(default_factory=list)
    story_metadata: StoryMetadata
    generated_story: str
    rewritten_story: str
