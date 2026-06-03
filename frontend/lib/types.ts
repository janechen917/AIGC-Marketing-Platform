/** 与后端 schema 对齐的 TS 类型。 */

export type ComplianceIssue = {
  rule: string;
  message: string;
  level: string;
};

export type ComplianceCheckResponse = {
  passed: boolean;
  issue_count: number;
  issues: ComplianceIssue[];
};

export type CopyGenerateRequest = {
  product_name: string;
  selling_points: string[];
  target_audience: string;
  platform: string;
  style?: string;
  length_hint?: string;
  title_count?: number;
  brand_name?: string | null;
  required_phrases?: string[];
  forbidden_competitors?: string[];
  require_hashtag?: boolean;
  require_cta?: boolean;
  max_length?: number | null;
  max_emojis?: number | null;
};

export type CopyGenerateResponse = {
  draft_text: string;
  polished_text: string;
  draft_model: string;
  polish_model: string;
  compliance: ComplianceCheckResponse;
};

export type ReviewsGenerateRequest = {
  product_name: string;
  selling_points: string[];
  platform: string;
  style?: string;
  target_count?: number;
  batch_size?: number;
  max_rounds?: number;
  similarity_threshold?: number;
  persona_pool?: string[];
  require_hashtag?: boolean;
  require_cta?: boolean;
};

export type ReviewsGenerateResponse = {
  reviews: string[];
  total_generated: number;
  rounds: number;
  deduped_dropped: number;
  compliance_dropped: number;
  csv_content: string;
};

export type TaskEnqueueResponse = {
  task_id: string;
  state: string;
  task_name: string;
};

export type TaskStatusResponse = {
  task_id: string;
  state: string;
  ready: boolean;
  successful: boolean;
  result?: unknown;
  error?: string;
};

export type PosterGenerateRequest = {
  prompt: string;
  size?: string | null;
};

export type PosterTaskResponse = {
  id: string;
  status: string; // pending | running | done | failed
  prompt: string;
  size: string;
  model_used: string;
  image_url: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type VideoStartRequest = {
  prompt: string;
  shot_count?: number;
};

export type VideoConfirmRequest = {
  video_id: string;
  stage: "script_done" | "images_done";
  payload?: Record<string, unknown> | null;
};

export type VideoTaskResponse = {
  id: string;
  status: string;
  stage: string;
  prompt: string;
  shot_count: number;
  script_model: string;
  image_model: string;
  clip_model: string;
  script_data: Record<string, unknown> | null;
  image_urls: string[] | null;
  clip_urls: string[] | null;
  final_video_url: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};
