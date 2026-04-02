export interface User {
  id: number;
  email: string;
  display_name: string | null;
  country: string | null;
  language: string;
  is_active: boolean;
  is_admin: boolean;
  is_editor: boolean;
  is_educator: boolean;
  organization_id: number | null;
  subscription_tier: string;
  subscription_status: string;
  subscription_expires_at: string | null;
  trial_ends_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReaderBookSummary {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  language: string;
  published: boolean;
  publication_status: string;
  page_count: number;
  audio_available?: boolean;
}

export interface ClassroomSetRead {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  age_band: string | null;
  language: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClassroomSetItemRead {
  id: number;
  classroom_set_id: number;
  book_id: number;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface ClassroomSetDetailResponse {
  classroom_set: ClassroomSetRead;
  set_items: ClassroomSetItemRead[];
  items: DiscoverySearchResult[];
}

export interface OrganizationRead {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMembershipRead {
  id: number;
  organization_id: number;
  user_id: number;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrganizationDetailResponse {
  organization: OrganizationRead;
  memberships: OrganizationMembershipRead[];
}

export interface AccountHealthSnapshotRead {
  id: number;
  user_id: number;
  health_score: number;
  health_band: string;
  active_children_count: number;
  stories_opened_30d: number;
  stories_completed_30d: number;
  saved_books_count: number;
  support_tickets_open_count: number;
  premium_status: string | null;
  dormant_days: number | null;
  snapshot_reasoning: string | null;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface AccountHealthSnapshotResponse {
  snapshot: AccountHealthSnapshotRead;
  user_email: string;
  user_display_name: string | null;
}

export interface AccountHealthSummaryResponse {
  items: AccountHealthSnapshotResponse[];
  total: number;
}

export interface ReaderPageRead {
  id: number;
  book_id: number;
  source_story_page_id?: number | null;
  page_number: number;
  text_content: string;
  image_url: string | null;
  layout_type: string;
}

export interface ReaderBookDetail {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  language: string;
  published: boolean;
  publication_status: string;
  pages: ReaderPageRead[];
}

export interface LocalizedReaderBookDetail {
  book_id: number;
  language: string;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  published: boolean;
  publication_status: string;
  pages: ReaderPageRead[];
  story_draft_id?: number | null;
  page_mapping?: Record<number, number> | null;
}

export interface ContinueReadingResponse {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  current_page_number: number;
  completed: boolean;
  last_opened_at: string;
}

export interface ReadingProgressRead {
  id: number;
  reader_identifier: string;
  book_id: number;
  child_profile_id?: number | null;
  current_page_number: number;
  completed: boolean;
  last_opened_at: string;
  created_at: string;
  updated_at: string;
}

export interface ReaderAudioSummary {
  id: number;
  book_id: number;
  voice_id: number;
  voice_key: string;
  voice_display_name: string;
  language: string;
  audio_url: string;
  duration_seconds: number | null;
  is_active: boolean;
  approval_status: string;
}

export interface NarrationVoiceRead {
  id: number;
  key: string;
  display_name: string;
  language: string;
  style: string | null;
  description: string | null;
  is_premium: boolean;
}

export interface NarrationSegmentRead {
  id: number;
  narration_id: number;
  page_number: number;
  audio_url: string;
  duration_seconds: number | null;
}

export interface BookNarrationRead {
  id: number;
  book_id: number;
  language: string;
  narration_voice_id: number;
  duration_seconds: number | null;
  is_active: boolean;
}

export interface ReaderNarrationResponse {
  narration: BookNarrationRead;
  segments: NarrationSegmentRead[];
  voice: NarrationVoiceRead;
}

export interface AvailableVoicesResponse {
  voices: NarrationVoiceRead[];
}

export interface UserStoryFeedbackRead {
  id: number;
  user_id: number;
  book_id: number;
  child_profile_id?: number | null;
  liked: boolean | null;
  rating: number | null;
  completed: boolean;
  replayed: boolean;
  preferred_character: string | null;
  preferred_style: string | null;
  preferred_tone: string | null;
  feedback_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserStoryProfileRead {
  id: number;
  user_id: number;
  favorite_characters: string | null;
  preferred_tones: string | null;
  preferred_lengths: string | null;
  preferred_settings: string | null;
  preferred_styles: string | null;
  total_books_rated: number;
  total_books_completed: number;
  total_books_replayed: number;
  last_profile_refresh_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackSummaryResponse {
  feedback: UserStoryFeedbackRead;
  profile: UserStoryProfileRead;
}

export interface SubscriptionStatusRead {
  user_id: number;
  subscription_tier: string;
  subscription_status: string;
  subscription_expires_at: string | null;
  trial_ends_at: string | null;
  has_premium_access: boolean;
  is_trial_active: boolean;
  is_subscription_active: boolean;
}

export interface ReaderAccessResponse {
  book_id: number;
  can_read_full_book: boolean;
  can_use_audio: boolean;
  preview_page_limit: number;
  reason: string;
}

export interface UserLibraryItemRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  book_id: number;
  status: string;
  saved_for_offline: boolean;
  last_opened_at: string | null;
  downloaded_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SavedLibraryResponse {
  items: UserLibraryItemRead[];
}

export interface BookDownloadPackageRead {
  id: number;
  book_id: number;
  language: string;
  package_version: number;
  package_url: string;
  package_format: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReaderDownloadAccessResponse {
  book_id: number;
  can_download_full_book: boolean;
  package_available: boolean;
  package_url: string | null;
  reason: string;
}

export interface OfflineNarrationSegment {
  page_number: number;
  audio_url: string;
  duration_seconds: number | null;
}

export interface OfflineNarrationPayload {
  narration_id: number;
  voice_key: string;
  voice_display_name: string;
  language: string;
  duration_seconds: number | null;
  segments: OfflineNarrationSegment[];
}

export interface OfflineLegacyAudioItem {
  id: number;
  voice_id: number;
  audio_url: string;
  duration_seconds: number | null;
  version_number: number;
}

export interface OfflineBookPackagePayload {
  book: {
    book_id: number;
    title: string;
    cover_image_url: string | null;
    age_band: string;
    content_lane_key?: string | null;
    language: string;
    published: boolean;
    publication_status: string;
  };
  pages: ReaderPageRead[];
  legacy_audio: OfflineLegacyAudioItem[];
  audio: OfflineNarrationPayload | null;
  language: string;
  package_version: number;
}

export interface OfflineBookPackageRecord {
  key: string;
  book_id: number;
  language: string;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  package_version: number;
  package_url: string;
  saved_at: string;
  updated_at: string;
  payload: OfflineBookPackagePayload;
}

export type OfflineSyncActionType = "reading_progress" | "library_opened" | "library_offline_state";

export interface OfflineSyncActionRecord {
  id?: number;
  type: OfflineSyncActionType;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}

export interface BillingPortalResponse {
  portal_url: string;
}

export interface BillingStatusResponse {
  user_id: number;
  subscription_tier: string;
  subscription_status: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  subscription_expires_at: string | null;
  trial_ends_at: string | null;
  has_premium_access: boolean;
}

export interface BillingRecoveryCaseRead {
  id: number;
  user_id: number;
  source_type: string;
  external_reference: string | null;
  recovery_status: string;
  billing_status_snapshot: string | null;
  subscription_tier_snapshot: string | null;
  title: string;
  summary: string;
  first_detected_at: string;
  last_detected_at: string;
  resolved_at: string | null;
  expires_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillingRecoveryEventRead {
  id: number;
  recovery_case_id: number;
  event_type: string;
  summary: string;
  created_at: string;
}

export interface BillingRecoveryCaseDetailResponse {
  case: BillingRecoveryCaseRead;
  events: BillingRecoveryEventRead[];
}

export interface BillingRecoveryPromptResponse {
  has_open_recovery: boolean;
  case: BillingRecoveryCaseRead | null;
  action_label: string | null;
  action_route: string | null;
  message: string | null;
}

export interface LifecycleMilestoneRead {
  id: number;
  user_id: number;
  milestone_type: string;
  occurred_at: string;
  title: string;
  summary: string | null;
  source_table: string | null;
  source_id: string | null;
  metadata_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface LifecycleTimelineResponse {
  user_id: number;
  milestones: LifecycleMilestoneRead[];
}

export interface LifecycleSummaryResponse {
  user_id: number;
  first_seen_at: string | null;
  latest_activity_at: string | null;
  has_completed_onboarding: boolean;
  has_child_profiles: boolean;
  has_premium_history: boolean;
  current_subscription_status: string | null;
  support_ticket_count: number;
  open_billing_recovery: boolean;
  lifecycle_stage: string | null;
}

export interface LifecycleRebuildResponse {
  user_id: number;
  created_count: number;
  milestones: LifecycleMilestoneRead[];
}

export interface AchievementDefinitionRead {
  id: number;
  key: string;
  title: string;
  description: string;
  icon_key: string | null;
  target_scope: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EarnedAchievementRead {
  id: number;
  achievement_definition_id: number;
  user_id: number;
  child_profile_id: number | null;
  earned_at: string;
  source_table: string | null;
  source_id: string | null;
  created_at: string;
  updated_at: string;
  achievement_key: string | null;
  title: string | null;
  description: string | null;
  icon_key: string | null;
  target_scope: string | null;
}

export interface ReadingStreakSnapshotRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  current_streak_days: number;
  longest_streak_days: number;
  last_read_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface AchievementDashboardResponse {
  earned_achievements: EarnedAchievementRead[];
  current_streak: number;
  longest_streak: number;
  next_suggested_milestone: string | null;
}

export interface FamilyDigestRead {
  id: number;
  user_id: number;
  digest_type: string;
  period_start: string;
  period_end: string;
  title: string;
  summary_json: string;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface FamilyDigestChildSummaryRead {
  id: number;
  family_digest_id: number;
  child_profile_id: number;
  stories_opened: number;
  stories_completed: number;
  narration_uses: number;
  achievements_earned: number;
  current_streak_days: number;
  summary_text: string | null;
  created_at: string;
  updated_at: string;
}

export interface FamilyDigestDetailResponse {
  digest: FamilyDigestRead;
  child_summaries: FamilyDigestChildSummaryRead[];
}

export interface FamilyDigestGenerateResponse {
  digest: FamilyDigestRead;
  child_summaries: FamilyDigestChildSummaryRead[];
  generated_now: boolean;
}

export interface FamilyDigestSummaryCardResponse {
  title: string;
  highlight_text: string;
  period_start: string;
  period_end: string;
  child_count: number;
  stories_completed: number;
  achievements_earned: number;
}

export interface ReadingPlanRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  title: string;
  description: string | null;
  status: string;
  plan_type: string;
  preferred_age_band: string | null;
  preferred_language: string | null;
  preferred_content_lane_key: string | null;
  prefer_narration: boolean;
  sessions_per_week: number;
  target_days_csv: string | null;
  bedtime_mode_preferred: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReadingPlanSessionRead {
  id: number;
  reading_plan_id: number;
  scheduled_date: string;
  suggested_book_id: number | null;
  completed: boolean;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadingPlanDetailResponse {
  plan: ReadingPlanRead;
  upcoming_sessions: ReadingPlanSessionRead[];
}

export interface ReadingPlanSuggestionResponse {
  plan: ReadingPlanRead;
  suggested_books: DiscoverySearchResult[];
}

export interface BedtimePackRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  title: string;
  description: string | null;
  status: string;
  pack_type: string;
  language: string | null;
  age_band: string | null;
  content_lane_key: string | null;
  prefer_narration: boolean;
  generated_reason: string | null;
  active_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface BedtimePackItemRead {
  id: number;
  bedtime_pack_id: number;
  book_id: number;
  position: number;
  recommended_narration: boolean;
  completion_status: string;
  created_at: string;
  updated_at: string;
}

export interface BedtimePackDetailResponse {
  pack: BedtimePackRead;
  items: BedtimePackItemRead[];
}

export interface BedtimePackGenerateResponse {
  pack: BedtimePackRead;
  items: BedtimePackItemRead[];
  generated_now: boolean;
}

export interface ReadAlongSessionRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  book_id: number;
  join_code: string;
  status: string;
  current_page_number: number;
  playback_state: string;
  language: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
  ended_at: string | null;
}

export interface ReadAlongParticipantRead {
  id: number;
  session_id: number;
  user_id: number;
  child_profile_id: number | null;
  role: string;
  joined_at: string;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadAlongDetailResponse {
  session: ReadAlongSessionRead;
  participants: ReadAlongParticipantRead[];
}

export interface ReadAlongJoinResponse {
  session: ReadAlongSessionRead;
  participant: ReadAlongParticipantRead;
}

export interface AnalyticsTrackRequest {
  event_name: string;
  book_id?: number;
  child_profile_id?: number;
  session_id?: string;
  language?: string;
  country?: string;
  experiment_key?: string;
  experiment_variant?: string;
  metadata?: Record<string, unknown>;
}

export interface AnalyticsEventRead {
  id: number;
  event_name: string;
  user_id: number | null;
  child_profile_id: number | null;
  reader_identifier: string | null;
  book_id: number | null;
  session_id: string | null;
  language: string | null;
  country: string | null;
  experiment_key: string | null;
  experiment_variant: string | null;
  metadata_json: string | null;
  occurred_at: string;
  created_at: string;
}

export interface MessageExperimentSurfaceCopy {
  experiment_key: string;
  variant: string;
  eyebrow?: string;
  headline?: string;
  description?: string;
  primary_cta_label?: string;
  secondary_cta_label?: string;
  pricing_cta_label?: string;
  guest_primary_label?: string;
  guest_secondary_label?: string;
  cta_headline?: string;
  cta_description?: string;
  title?: string;
  cta_label?: string;
}

export interface MessageExperimentBundleResponse {
  homepage_cta: MessageExperimentSurfaceCopy;
  preview_wall: MessageExperimentSurfaceCopy;
  pricing_page: MessageExperimentSurfaceCopy;
  upgrade_card: MessageExperimentSurfaceCopy;
}

export interface AnalyticsSummaryResponse {
  total_events: number;
  unique_users: number;
  unique_readers: number;
  top_books: AdminAnalyticsBookStat[];
  top_event_counts: Record<string, number>;
}

export interface AdminAnalyticsBookStat {
  book_id: number;
  title: string;
  opens: number;
  completions: number;
  replays: number;
  audio_starts: number;
  recommendation_clicks: number;
  total: number;
}

export interface AnalyticsFunnelResponse {
  library_viewed: number;
  book_opened: number;
  preview_wall_hit: number;
  checkout_started: number;
  checkout_completed: number;
}

export interface ExperimentVariantResponse {
  experiment_key: string;
  variant: string;
  assigned: boolean;
}

export interface BookTranslationRead {
  id: number;
  book_id: number;
  language: string;
  title: string;
  description: string | null;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface BookPageTranslationRead {
  id: number;
  book_page_id: number;
  language: string;
  text_content: string;
  created_at: string;
  updated_at: string;
}

export interface SupportedLanguagesResponse {
  supported_ui_languages: string[];
  supported_content_languages: string[];
  default_language: string;
}

export interface RecommendedBookScore {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  language: string;
  published: boolean;
  publication_status: string;
  score: number;
  reasons: string[];
}

export interface RecommendationsResponse {
  items: RecommendedBookScore[];
}

export interface BookDiscoveryMetadataRead {
  id: number;
  book_id: number;
  searchable_title: string;
  searchable_summary: string | null;
  searchable_text: string | null;
  age_band: string;
  language: string;
  content_lane_key: string | null;
  tone_tags: string | null;
  theme_tags: string | null;
  character_tags: string | null;
  setting_tags: string | null;
  style_tags: string | null;
  bedtime_safe: boolean;
  adventure_level: string | null;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface BookCollectionRead {
  id: number;
  key: string;
  title: string;
  description: string | null;
  language: string | null;
  age_band: string | null;
  content_lane_key: string | null;
  is_public: boolean;
  is_featured: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SeasonalCampaignRead {
  id: number;
  key: string;
  title: string;
  description: string | null;
  start_at: string;
  end_at: string;
  is_active: boolean;
  language: string | null;
  age_band: string | null;
  content_lane_key: string | null;
  homepage_badge_text: string | null;
  homepage_cta_label: string | null;
  homepage_cta_route: string | null;
  banner_style_key: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SeasonalCampaignItemRead {
  id: number;
  campaign_id: number;
  book_id: number;
  position: number;
  created_at: string;
  updated_at: string;
}

export interface DiscoverySearchResult {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  language: string;
  content_lane_key: string | null;
  published: boolean;
  publication_status: string;
  score: number | null;
  reasons: string[] | null;
}

export interface DiscoverySearchResponse {
  total: number;
  items: DiscoverySearchResult[];
}

export interface CollectionDetailResponse {
  collection: BookCollectionRead;
  items: DiscoverySearchResult[];
}

export interface SeasonalCampaignDetailResponse {
  campaign: SeasonalCampaignRead;
  items: DiscoverySearchResult[];
}

export interface ContentLaneRead {
  id: number;
  key: string;
  display_name: string;
  age_band: string;
  description: string | null;
  tone_rules: string;
  writing_rules: string;
  illustration_rules: string | null;
  quality_rules: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgeBandSupportResponse {
  supported_age_bands: string[];
  supported_content_lanes: ContentLaneRead[];
}

export interface ChildProfileRead {
  id: number;
  user_id: number;
  display_name: string;
  birth_year: number | null;
  age_band: string;
  language: string;
  content_lane_key: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StorySuggestionRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  promoted_story_idea_id: number | null;
  title: string | null;
  brief: string;
  desired_outcome: string | null;
  inspiration_notes: string | null;
  avoid_notes: string | null;
  age_band: string;
  language: string;
  allow_reference_use: boolean;
  status: string;
  approved_as_reference: boolean;
  editorial_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface StorySuggestionListResponse {
  items: StorySuggestionRead[];
}

export interface StorySuggestionAdminRead extends StorySuggestionRead {
  user_email: string | null;
  user_display_name: string | null;
  child_profile_name: string | null;
  promoted_story_idea_title: string | null;
}

export interface StorySuggestionAdminListResponse {
  items: StorySuggestionAdminRead[];
}

export interface ChildComfortProfileRead {
  id: number;
  child_profile_id: number;
  favorite_characters_csv: string | null;
  favorite_moods_csv: string | null;
  favorite_story_types_csv: string | null;
  avoid_tags_csv: string | null;
  preferred_language: string | null;
  prefer_narration: boolean;
  prefer_shorter_stories: boolean;
  extra_calm_mode: boolean;
  bedtime_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ParentalControlSettingsRead {
  id: number;
  user_id: number;
  bedtime_mode_default: boolean;
  allow_audio_autoplay: boolean;
  allow_8_12_content: boolean;
  allow_premium_voice_content: boolean;
  hide_adventure_content_at_bedtime: boolean;
  max_allowed_age_band: string;
  quiet_mode_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChildControlOverrideRead {
  id: number;
  child_profile_id: number;
  bedtime_mode_enabled: boolean | null;
  allow_audio_autoplay: boolean | null;
  allow_8_12_content: boolean | null;
  allow_premium_voice_content: boolean | null;
  quiet_mode_enabled: boolean | null;
  max_allowed_age_band: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResolvedParentalControlsResponse {
  user_id: number;
  child_profile_id: number | null;
  bedtime_mode_enabled: boolean;
  allow_audio_autoplay: boolean;
  allow_8_12_content: boolean;
  allow_premium_voice_content: boolean;
  hide_adventure_content_at_bedtime: boolean;
  max_allowed_age_band: string;
  quiet_mode_enabled: boolean;
}

export interface NotificationPreferenceRead {
  id: number;
  user_id: number;
  enable_in_app: boolean;
  enable_email_placeholder: boolean;
  enable_bedtime_reminders: boolean;
  enable_new_story_alerts: boolean;
  enable_weekly_digest: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  timezone: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationEventRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  notification_type: string;
  delivery_channel: string;
  title: string;
  body: string;
  metadata_json: string | null;
  is_read: boolean;
  delivered: boolean;
  scheduled_for: string | null;
  delivered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DailyStorySuggestionRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  book_id: number;
  suggestion_date: string;
  reason: string | null;
  created_at: string;
}

export interface DailyStoryBookSummary {
  book_id: number;
  title: string;
  cover_image_url: string | null;
  age_band: string;
  content_lane_key?: string | null;
  language: string;
  published: boolean;
  publication_status: string;
}

export interface DailyStorySuggestionResponse {
  suggestion: DailyStorySuggestionRead | null;
  book: DailyStoryBookSummary | null;
}

export interface SupportTicketRead {
  id: number;
  user_id: number | null;
  child_profile_id: number | null;
  email: string | null;
  category: string;
  subject: string;
  message: string;
  related_book_id: number | null;
  status: string;
  priority: string;
  assigned_to_user_id: number | null;
  source: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface SupportTicketNoteRead {
  id: number;
  ticket_id: number;
  author_user_id: number | null;
  note_type: string;
  body: string;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupportTicketDetailResponse {
  ticket: SupportTicketRead;
  notes: SupportTicketNoteRead[];
}

export interface SupportTicketListResponse {
  items: SupportTicketRead[];
}

export interface ModerationCaseRead {
  id: number;
  case_type: string;
  target_type: string;
  target_id: number | null;
  source_type: string;
  source_id: number | null;
  severity: string;
  status: string;
  summary: string;
  notes: string | null;
  assigned_to_user_id: number | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface ModerationCaseDetailResponse {
  case: ModerationCaseRead;
  target_summary: string | null;
  source_summary: string | null;
}

export interface IncidentRecordRead {
  id: number;
  title: string;
  summary: string;
  severity: string;
  status: string;
  affected_area: string;
  feature_flag_key: string | null;
  assigned_to_user_id: number | null;
  started_at: string;
  detected_at: string | null;
  mitigated_at: string | null;
  resolved_at: string | null;
  customer_impact_summary: string | null;
  root_cause_summary: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentUpdateRead {
  id: number;
  incident_id: number;
  author_user_id: number | null;
  update_type: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentDetailResponse {
  incident: IncidentRecordRead;
  updates: IncidentUpdateRead[];
}

export interface IncidentSummaryResponse {
  open_incidents: number;
  sev_1_open: number;
  sev_2_open: number;
  incidents_resolved_30d: number;
}

export interface RunbookEntryRead {
  id: number;
  key: string;
  title: string;
  area: string;
  summary: string;
  steps_markdown: string;
  is_active: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface HousekeepingPolicyRead {
  id: number;
  key: string;
  name: string;
  target_table: string;
  action_type: string;
  retention_days: number;
  enabled: boolean;
  dry_run_only: boolean;
  notes: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface HousekeepingRunRead {
  id: number;
  policy_id: number;
  status: string;
  dry_run: boolean;
  candidate_count: number;
  affected_count: number;
  result_json: string | null;
  error_message: string | null;
  created_by_user_id: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface HousekeepingRunResponse {
  run: HousekeepingRunRead;
}

export interface HousekeepingSummaryResponse {
  policies: HousekeepingPolicyRead[];
  recent_runs: HousekeepingRunRead[];
}

export interface MaintenanceJobRead {
  id: number;
  key: string;
  title: string;
  description: string | null;
  job_type: string;
  status: string;
  target_scope: string | null;
  parameters_json: string | null;
  result_json: string | null;
  error_message: string | null;
  created_by_user_id: number | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceJobRunResponse {
  job: MaintenanceJobRead;
}

export interface ActivityFeedItem {
  timestamp: string;
  event_type: string;
  entity_type: string;
  entity_id: string | null;
  summary: string;
  actor_user_id: number | null;
  actor_email: string | null;
  source_table: string;
  metadata_json: string | null;
}

export interface ActivityFeedResponse {
  items: ActivityFeedItem[];
}

export interface ChangelogEntryRead {
  id: number;
  version_label: string;
  title: string;
  summary: string;
  details_markdown: string | null;
  audience: string;
  status: string;
  area_tags: string | null;
  feature_flag_keys: string | null;
  published_at: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface VisualReferenceAssetRead {
  id: number;
  name: string;
  reference_type: string;
  target_type: string | null;
  target_id: number | null;
  image_url: string;
  prompt_notes: string | null;
  language: string | null;
  is_active: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface VisualReferenceImportResponse {
  created: number;
  updated: number;
  scanned: number;
  created_tables: boolean;
}

export interface IllustrationPromptPackageRead {
  story_page_id: number;
  provider: string;
  provider_model: string | null;
  provider_base_url: string | null;
  provider_timeout_seconds: number | null;
  generation_ready: boolean;
  live_generation_available: boolean;
  debug_enabled: boolean;
  prompt_used: string;
  positive_prompt: string;
  negative_prompt: string;
  page_text: string;
  scene_summary: string;
  location: string;
  mood: string;
  characters_present: string;
  reference_assets: VisualReferenceAssetRead[];
  reference_summary: string;
}

export interface KPIOverviewResponse {
  total_users: number;
  active_users_30d: number;
  total_child_profiles: number;
  active_child_profiles_30d: number;
  total_premium_users: number;
  premium_conversion_rate: number;
  total_published_books: number;
  total_saved_library_items: number;
  total_downloads: number;
  total_support_tickets_open: number;
  generated_at: string;
}

export interface EngagementMetricsResponse {
  book_opens_30d: number;
  book_completions_30d: number;
  book_replays_30d: number;
  narration_starts_30d: number;
  narration_completions_30d: number;
  daily_story_views_30d: number;
  avg_completion_rate_30d: number;
}

export interface SubscriptionMetricsResponse {
  free_users: number;
  premium_users: number;
  trialing_users: number;
  canceled_users: number;
  active_conversion_rate: number;
  checkout_started_30d: number;
  checkout_completed_30d: number;
}

export interface ContentPerformanceItem {
  book_id: number;
  title: string;
  language: string;
  age_band: string;
  content_lane_key: string | null;
  opens: number;
  completions: number;
  replays: number;
  downloads: number;
  narration_starts: number;
}

export interface ContentPerformanceResponse {
  items: ContentPerformanceItem[];
}

export interface SegmentBreakdownItem {
  key: string;
  count: number;
}

export interface SegmentBreakdownResponse {
  items: SegmentBreakdownItem[];
}

export interface SupportMetricsResponse {
  open_tickets: number;
  in_progress_tickets: number;
  resolved_30d: number;
  avg_resolution_hours: number | null;
}

export interface LegalAcceptanceRead {
  id: number;
  user_id: number;
  document_type: string;
  document_version: string;
  accepted_at: string;
  source: string;
  created_at: string;
}

export interface PrivacyPreferenceRead {
  id: number;
  user_id: number;
  marketing_email_opt_in: boolean;
  product_updates_opt_in: boolean;
  analytics_personalization_opt_in: boolean;
  allow_recommendation_personalization: boolean;
  created_at: string;
  updated_at: string;
}

export interface DataRequestRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  request_type: string;
  status: string;
  reason: string | null;
  requested_at: string;
  completed_at: string | null;
  output_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrivacyDashboardResponse {
  latest_terms_acceptance: LegalAcceptanceRead | null;
  latest_privacy_acceptance: LegalAcceptanceRead | null;
  privacy_preference: PrivacyPreferenceRead | null;
  active_data_requests: DataRequestRead[];
}

export interface ReferralCodeRead {
  id: number;
  user_id: number;
  code: string;
  is_active: boolean;
  total_uses: number;
  created_at: string;
  updated_at: string;
}

export interface ReferralAttributionRead {
  id: number;
  referrer_user_id: number;
  referred_user_id: number;
  referral_code_id: number;
  signup_attributed_at: string;
  premium_converted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface GiftSubscriptionRead {
  id: number;
  purchaser_user_id: number;
  recipient_user_id: number | null;
  code: string;
  duration_days: number;
  status: string;
  purchased_at: string;
  redeemed_at: string | null;
  expires_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface GiftSubscriptionRedeemResponse {
  gift: GiftSubscriptionRead;
  subscription_status: string;
  subscription_tier: string;
  expires_at: string | null;
}

export interface PromoAccessCodeRead {
  id: number;
  key: string;
  name: string;
  code: string;
  partner_name: string | null;
  access_type: string;
  subscription_tier_granted: string | null;
  duration_days: number | null;
  max_redemptions: number | null;
  redemption_count: number;
  starts_at: string | null;
  ends_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PromoAccessRedemptionRead {
  id: number;
  promo_access_code_id: number;
  user_id: number;
  redeemed_at: string;
  expires_at: string | null;
  created_at: string;
}

export interface PromoAccessRedeemResponse {
  code: PromoAccessCodeRead;
  redemption: PromoAccessRedemptionRead;
  subscription_status: string;
  subscription_tier: string;
  expires_at: string | null;
}

export interface ReferralSummaryResponse {
  referral_code: ReferralCodeRead | null;
  total_referrals: number;
  premium_conversions: number;
}

export interface FeatureFlagRead {
  id: number;
  key: string;
  name: string;
  description: string | null;
  enabled: boolean;
  rollout_percentage: number;
  environments: string | null;
  target_subscription_tiers: string | null;
  target_languages: string | null;
  target_age_bands: string | null;
  target_roles: string | null;
  target_user_ids: string | null;
  target_countries: string | null;
  target_beta_cohorts: string | null;
  is_internal_only: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface FeatureFlagEvaluationResponse {
  key: string;
  enabled: boolean;
  reason: string;
}

export interface FeatureFlagBundleResponse {
  flags: Record<string, boolean>;
}

export interface OnboardingStateRead {
  id: number;
  user_id: number;
  current_step: string;
  completed: boolean;
  skipped: boolean;
  child_profile_created: boolean;
  preferred_age_band: string | null;
  preferred_language: string | null;
  bedtime_mode_reviewed: boolean;
  first_story_opened: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OnboardingStartResponse {
  state: OnboardingStateRead;
  recommended_next_route: string;
}

export interface TranslationTaskRead {
  id: number;
  book_id: number;
  language: string;
  status: string;
  assigned_to_user_id: number | null;
  source_version_label: string | null;
  notes: string | null;
  due_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TranslationTaskDetailResponse {
  task: TranslationTaskRead | null;
  book_id: number;
  book_title: string;
  age_band: string;
  source_language: string;
  target_language: string;
  has_book_translation: boolean;
  translated_page_count: number;
  total_page_count: number;
  missing_page_count: number;
  is_translation_complete: boolean;
  is_translation_published: boolean;
}

export interface UserEngagementStateRead {
  id: number;
  user_id: number;
  state_key: string;
  last_active_at: string | null;
  last_story_opened_at: string | null;
  last_story_completed_at: string | null;
  last_subscription_active_at: string | null;
  active_child_profiles_count: number;
  unread_saved_books_count: number;
  unfinished_books_count: number;
  preview_only_books_count: number;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface BetaCohortRead {
  id: number;
  key: string;
  name: string;
  description: string | null;
  is_active: boolean;
  feature_flag_keys: string | null;
  notes: string | null;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface BetaCohortMembershipRead {
  id: number;
  beta_cohort_id: number;
  user_id: number;
  source: string;
  invited_by_user_id: number | null;
  is_active: boolean;
  joined_at: string;
  created_at: string;
  updated_at: string;
}

export interface BetaCohortDetailResponse {
  cohort: BetaCohortRead;
  memberships: BetaCohortMembershipRead[];
}

export interface UserBetaAccessResponse {
  user_id: number;
  cohorts: BetaCohortRead[];
  cohort_keys: string[];
}

export interface InternalSearchResult {
  entity_type: string;
  entity_id: string;
  title: string;
  subtitle: string | null;
  description: string | null;
  route: string | null;
  badge: string | null;
  metadata_json: string | null;
}

export interface InternalSearchGroup {
  entity_type: string;
  label: string;
  items: InternalSearchResult[];
}

export interface InternalSearchResponse {
  query: string;
  groups: InternalSearchGroup[];
}

export interface QuickActionItem {
  key: string;
  label: string;
  route: string | null;
  action_type: string;
  entity_type: string | null;
  entity_id: string | null;
  description: string | null;
  permission_hint: string | null;
}

export interface QuickActionResponse {
  items: QuickActionItem[];
}

export interface PublicStatusComponentRead {
  id: number;
  key: string;
  name: string;
  description: string | null;
  sort_order: number;
  is_active: boolean;
  current_status: string;
  created_at: string;
  updated_at: string;
}

export interface PublicStatusNoticeRead {
  id: number;
  title: string;
  summary: string;
  notice_type: string;
  public_status: string;
  component_key: string | null;
  linked_incident_id: number | null;
  starts_at: string;
  ends_at: string | null;
  is_active: boolean;
  is_public: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface PublicStatusPageResponse {
  overall_status: string;
  components: PublicStatusComponentRead[];
  active_notices: PublicStatusNoticeRead[];
  upcoming_maintenance: PublicStatusNoticeRead[];
}

export interface ReengagementSuggestionRead {
  id: number;
  user_id: number;
  child_profile_id: number | null;
  suggestion_type: string;
  title: string;
  body: string;
  related_book_id: number | null;
  state_key: string | null;
  is_dismissed: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReengagementDashboardResponse {
  engagement_state: UserEngagementStateRead | null;
  suggestions: ReengagementSuggestionRead[];
}

export interface EditorialProjectRead {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  age_band: string;
  content_lane_key: string | null;
  language: string;
  status: string;
  created_by_user_id: number | null;
  assigned_editor_user_id: number | null;
  source_type: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface EditorialAssetRead {
  id: number;
  project_id: number;
  asset_type: string;
  file_url: string;
  language: string | null;
  page_number: number | null;
  is_active: boolean;
  created_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface EditorialStoryDraftRead {
  id: number;
  story_idea_id: number | null;
  project_id: number | null;
  title: string;
  age_band: string;
  language: string;
  content_lane_key: string | null;
  full_text: string;
  summary: string;
  read_time_minutes: number;
  review_status: string;
  review_notes: string | null;
  approved_text: string | null;
  generation_source: string;
  created_at: string;
  updated_at: string;
}

export interface EditorialStoryPageRead {
  id: number;
  story_draft_id: number;
  page_number: number;
  page_text: string;
  scene_summary: string;
  location: string;
  mood: string;
  characters_present: string;
  illustration_prompt: string;
  image_status: string;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface StoryDraftVersionRead {
  id: number;
  story_draft_id: number;
  version_number: number;
  title: string;
  full_text: string;
  summary: string;
  review_status: string;
  review_notes: string | null;
  approved_text: string | null;
  created_by_user_id: number | null;
  created_at: string;
}

export interface StoryPageVersionRead {
  id: number;
  story_page_id: number;
  version_number: number;
  page_number: number;
  page_text: string;
  scene_summary: string;
  location: string;
  mood: string;
  characters_present: string;
  illustration_prompt: string;
  image_url: string | null;
  created_by_user_id: number | null;
  created_at: string;
}

export interface RollbackResponse {
  ok: boolean;
  message: string;
  entity_type: string;
  entity_id: number;
  rolled_back_to_version_id: number;
}

export interface EditorialProjectDraftResponse {
  draft: EditorialStoryDraftRead | null;
  pages: EditorialStoryPageRead[];
  preview_book: AdminBookSummary | null;
}

export interface PreviewBookResponse {
  book: AdminBookSummary;
  pages: ReaderPageRead[];
  preview_only: boolean;
}

export interface QualityCheckRead {
  id: number;
  target_type: string;
  target_id: number;
  check_type: string;
  status: string;
  score: number | null;
  issues_json: string | null;
  summary: string;
  created_by_job_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface StoryQualityReviewRead {
  id: number;
  story_id: number;
  quality_score: number;
  review_required: boolean;
  flagged_issues_json: string;
  evaluation_summary: string | null;
  evaluated_at: string;
  created_at: string;
  updated_at: string;
}

export interface IllustrationQualityReviewRead {
  id: number;
  illustration_id: number;
  story_id: number | null;
  style_consistency_score: number;
  character_consistency_score: number;
  color_palette_score: number;
  flagged_issues_json: string;
  review_required: boolean;
  evaluated_at: string;
  created_at: string;
  updated_at: string;
}

export interface StoryQualitySummaryResponse {
  story_id: number;
  quality_score: number;
  review_required: boolean;
  flagged_issues: string[];
}

export interface StoryQualityQueueItemResponse {
  story_id: number;
  title: string;
  review_status: string;
  quality_score: number;
  review_required: boolean;
  flagged_issues: string[];
  evaluation_summary: string | null;
  evaluated_at: string;
}

export interface EditorialQualityRunResponse {
  draft_checks: QualityCheckRead[];
  page_checks: QualityCheckRead[];
}

export interface ChildReadingProfileRead {
  id: number;
  child_profile_id: number;
  favorite_characters: string | null;
  preferred_tones: string | null;
  preferred_lengths: string | null;
  preferred_settings: string | null;
  preferred_styles: string | null;
  total_books_completed: number;
  total_books_replayed: number;
  last_profile_refresh_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChildProfileSelectionResponse {
  child_profile: ChildProfileRead;
  reading_profile: ChildReadingProfileRead | null;
}

export interface PipelineCountsResponse {
  idea_pending: number;
  idea_selected: number;
  draft_pending_review: number;
  needs_revision: number;
  approved_for_illustration: number;
  story_pages_prompt_ready: number;
  story_pages_image_generated: number;
  story_pages_image_approved: number;
  story_pages_image_rejected: number;
  illustrations_generated: number;
  illustrations_approved: number;
  illustrations_rejected: number;
  books_ready: number;
  books_published: number;
  audio_generated: number;
  audio_approved: number;
  audio_rejected: number;
  workflow_jobs_queued: number;
  workflow_jobs_running: number;
  workflow_jobs_failed: number;
  automation_schedules_active: number;
  automation_schedules_due: number;
}

export interface AdminNextActionItem {
  stage: string;
  entity_type: string;
  entity_id: number;
  title: string;
  status: string;
  suggested_action: string;
  created_at: string;
}

export interface AdminNextActionsResponse {
  items: AdminNextActionItem[];
}

export interface AdminStoryIdeaSummary {
  id: number;
  title: string;
  premise: string;
  age_band: string;
  content_lane_key?: string | null;
  tone: string;
  setting: string;
  theme: string;
  status: string;
  created_at: string;
}

/** Returned by POST /story-ideas/generate (how LLM vs curated was used). */
export interface IdeaGenerationSummary {
  path: "llm" | "llm_plus_curated" | "curated" | string;
  excluded_recent_premise_count: number;
  approved_story_suggestion_count: number;
  llm_idea_count: number;
  curated_idea_count: number;
}

export interface StoryIdeaBatchGenerateResponse {
  created_count: number;
  ideas: unknown[];
  generation_summary?: IdeaGenerationSummary | null;
}

export interface AdminStoryDraftSummary {
  id: number;
  story_idea_id: number;
  title: string;
  content_lane_key?: string | null;
  summary: string;
  review_status: string;
  read_time_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface StoryDraftReviewRead {
  id: number;
  story_idea_id: number;
  title: string;
  summary: string;
  full_text: string;
  approved_text: string | null;
  review_status: string;
  review_notes: string | null;
  content_lane_key?: string | null;
  read_time_minutes: number;
  generation_source: string;
  created_at: string;
  updated_at: string;
}

export interface StoryReviewQueueRead {
  id: number;
  story_id: number;
  generated_story: string;
  rewritten_story: string;
  story_brief: string | null;
  story_validation: string | null;
  outline: string;
  illustration_plan: string;
  story_metadata: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AdminStoryPageSummary {
  id: number;
  story_draft_id: number;
  page_number: number;
  scene_summary: string;
  image_status: string;
  created_at: string;
  updated_at: string;
}

export interface AdminIllustrationSummary {
  id: number;
  story_page_id: number;
  story_draft_id?: number | null;
  story_draft_title?: string | null;
  book_id?: number | null;
  publication_status?: string | null;
  published?: boolean | null;
  page_number?: number | null;
  scene_summary?: string | null;
  approval_status: string;
  provider: string;
  version_number: number;
  image_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IllustrationGenerateResponse {
  illustration: AdminIllustrationSummary;
  story_page_id: number;
  image_status: string;
}

export interface AdminBookSummary {
  id: number;
  story_draft_id: number;
  title: string;
  age_band: string;
  language: string;
  content_lane_key?: string | null;
  publication_status: string;
  published: boolean;
  audio_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminAudioSummary {
  id: number;
  book_id: number;
  voice_id: number;
  approval_status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiKeyRead {
  id: number;
  name: string;
  key_prefix: string;
  scopes: string;
  is_active: boolean;
  created_by_user_id: number | null;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiKeyCreateResponse {
  key: ApiKeyRead;
  raw_api_key: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
