import { intentionRepository } from "../repositories/intention.repository";
import { IntentionStats, IntentionType } from "../entities/intention.entity";

const CATEGORY_COLORS: Record<IntentionType, string> = {
  question: "#3b82f6", // Blue - Question
  feedback: "#10b981", // Green - Feedback
  complaint: "#f59e0b", // Orange - Complaint
  suggestion: "#8b5cf6", // Purple - Suggestion
  praise: "#ec4899", // Pink - Praise
  request: "#06b6d4", // Cyan - Request
  discussion: "#f97316", // Amber - Discussion
  spam: "#ef4444", // Red - Spam
  other: "#6b7280", // Gray - Other
};
export class IntentionService {
  /**
   * Aggregate intentions by category.
   * Categories:
   */
  async getIntentionStats(): Promise<IntentionStats[]> {
    const intentions = await intentionRepository.findAll();

    // Count by category
    const countByCategory = new Map<IntentionType, number>([
      ["question", 0],
      ["feedback", 0],
      ["complaint", 0],
      ["suggestion", 0],
      ["praise", 0],
      ["request", 0],
      ["discussion", 0],
      ["spam", 0],
      ["other", 0],
    ]);

    for (const intention of intentions) {
      countByCategory.set(
        intention.intention_type,
        (countByCategory.get(intention.intention_type) || 0) + 1
      );
    }

    // Convert to array - always include all categories even with 0 count
    const stats: IntentionStats[] = [
      {
        name: "Question",
        value: countByCategory.get("question") || 0,
        color: CATEGORY_COLORS.question,
      },
      {
        name: "Feedback",
        value: countByCategory.get("feedback") || 0,
        color: CATEGORY_COLORS.feedback,
      },
      {
        name: "Complaint",
        value: countByCategory.get("complaint") || 0,
        color: CATEGORY_COLORS.complaint,
      },
      {
        name: "Suggestion",
        value: countByCategory.get("suggestion") || 0,
        color: CATEGORY_COLORS.suggestion,
      },
      {
        name: "Praise",
        value: countByCategory.get("praise") || 0,
        color: CATEGORY_COLORS.praise,
      },
      {
        name: "Request",
        value: countByCategory.get("request") || 0,
        color: CATEGORY_COLORS.request,
      },
      {
        name: "Discussion",
        value: countByCategory.get("discussion") || 0,
        color: CATEGORY_COLORS.discussion,
      },
      {
        name: "Spam",
        value: countByCategory.get("spam") || 0,
        color: CATEGORY_COLORS.spam,
      },
      {
        name: "Other",
        value: countByCategory.get("other") || 0,
        color: CATEGORY_COLORS.other,
      },
    ];

    return stats.sort((a, b) => b.value - a.value);
  }
}

export const intentionService = new IntentionService();
