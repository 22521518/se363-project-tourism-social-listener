export type IntentionType =
  | "QUESTION"
  | "FEEDBACK" 
  | "COMPLAINT"
  | "SUGGESTION"
  | "PRAISE"
  | "REQUEST"
  | "DISCUSSION"
  | "SPAM"
  | "OTHER";

// CATEGORY_COLORS
export const CATEGORY_COLORS: Record<IntentionType, string> = {
  QUESTION: "#3b82f6",
  FEEDBACK: "#10b981",
  COMPLAINT: "#f59e0b",
  SUGGESTION: "#8b5cf6",
  PRAISE: "#ec4899",
  REQUEST: "#06b6d4",
  DISCUSSION: "#f97316",
  SPAM: "#ef4444",
  OTHER: "#6b7280",
};

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