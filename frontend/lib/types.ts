export interface ClarificationContext {
  round: number;
  previous_questions: string[];
  user_answers: string[];
}

export interface ExtractedFieldView {
  value: string | number | boolean;
  source_url: string;
}

export interface ProductResult {
  name: string;
  price: number | null;
  matched_constraints: string[];
  soft_score: number;
  fields: Record<string, ExtractedFieldView>;
}

export interface ExecutionLog {
  stage: string;
  title: string;
  detail: string;
  type: string;
}

export interface CriticFeedback {
  missing_data: string[];
  negative_prompts: string[];
  failed_criteria: string[];
}

export interface VerdictDetails {
  verdict: string;
  weighted_score: number;
  relevance_score: number;
  constraint_score: number;
  evidence_score: number;
  completeness_score: number;
  rationale: string;
  feedback?: CriticFeedback | null;
}

export interface PipelineMetadata {
  iterations: number;
  is_best_available: boolean;
  from_cache?: boolean;
  from_memory?: boolean;
  memory_similarity?: number | null;
  weighted_score: number;
  assumptions_made: string[];
  generated_queries?: string[];
  logs?: ExecutionLog[];
  verdict?: VerdictDetails;
}

export interface SearchResultPayload {
  products: ProductResult[];
  synthesis: string | null;
  metadata: PipelineMetadata;
}

export interface ProgressPayload {
  stage: string;
  message: string;
}

export interface ClarificationPayload {
  question: string;
  round: number;
}

export interface ErrorPayload {
  code: string;
  message: string;
  details: string | null;
}

// Saved item interface for DB-backed saved items page
export interface SavedItem {
  name: string;
  price: number | null;
  image: string;
  merchant: string;
  link: string;
  created_at?: string;
}

// One entry in the user's DB-backed search history.
export interface SearchHistoryItem {
  query: string;
  best_match_name: string | null;
  best_match_price: number | null;
  best_match_url: string | null;
  created_at: string;
}

// Discriminated union: TypeScript narrows the `payload` type automatically
// based on the `event` field's literal value.
export type SSEEvent =
  | { event: "progress"; payload: ProgressPayload }
  | { event: "needs_clarification"; payload: ClarificationPayload }
  | { event: "result"; payload: SearchResultPayload }
  | { event: "error"; payload: ErrorPayload };

export const PIPELINE_STAGE_ORDER = [
  "normalizing",
  "generating",
  "cache_check",
  "searching",
  "sanitizing",
  "extracting",
  "matching",
  "critiquing",
  "retrying",
  "synthesizing",
  "done",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGE_ORDER)[number];