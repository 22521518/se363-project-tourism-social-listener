
export interface IntentionStats {
  name: string;
  value: number;
  color: string;
}

export const INTENTION_COLORS: Record<string, string> = {
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

