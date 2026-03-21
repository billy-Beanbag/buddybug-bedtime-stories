from pydantic import BaseModel, Field


class StoryHook(BaseModel):
    key: str
    description: str
    typical_tone: str
    bedtime_mode_allowed: bool
    standard_mode_allowed: bool
    example_plot_directions: list[str] = Field(default_factory=list)


class StoryBeat(BaseModel):
    key: str
    label: str
    text: str


class StoryPromptContext(BaseModel):
    mode: str
    target_tone: str
    target_pacing: str
    hook_first_instruction: str
    anti_poetic_overload_instruction: str
    structure_instruction: str
    guidance: str


class StoryPlan(BaseModel):
    mode: str
    title: str
    premise: str
    hook_key: str
    hook_description: str
    setting: str
    theme: str
    bedtime_feeling: str
    main_characters: list[str] = Field(default_factory=list)
    supporting_characters: list[str] = Field(default_factory=list)
    opening_beat: str
    problem_beat: str
    event_beat: str
    resolution_beat: str
    ending_tone: str
    playful_tone: bool = False
    bedtime_suitability: bool = False
    illustration_beats: list[StoryBeat] = Field(default_factory=list)
    prompt_context: StoryPromptContext
