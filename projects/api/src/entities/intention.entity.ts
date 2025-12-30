export type IntentionType =
  | "question"
  | "feedback"
  | "complaint"
  | "suggestion"
  | "praise"
  | "request"
  | "discussion"
  | "spam"
  | "other";

export interface IntentionExtraction {
  id: string;
  source_id: string;
  source_type: string;
  raw_text: string;
  intention_type: IntentionType;
  created_at: string;
}

export interface IntentionStats {
  name: string;
  value: number;
  color: string;
}