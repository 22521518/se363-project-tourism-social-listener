import { intentionRepository } from "../repositories/intention.repository";
import {
  CATEGORY_COLORS,
  IntentionStats,
  IntentionType,
  IntentionExtraction,
} from "../entities/intention.entity";

export class IntentionService {
  /**
   * Aggregate intentions by category.
   * Categories:
   */
  async getIntentionStats(): Promise<IntentionStats[]> {
    const intentions = await intentionRepository.findAll();

    // Count by category
    const countByCategory = new Map<IntentionType, number>([
      ["QUESTION", 0],
      ["FEEDBACK", 0],
      ["COMPLAINT", 0],
      ["SUGGESTION", 0],
      ["PRAISE", 0],
      ["REQUEST", 0],
      ["DISCUSSION", 0],
      ["SPAM", 0],
      ["OTHER", 0],
    ]);

    for (const intention of intentions) {
      // Convert to uppercase to match database values
      const intentionType =
        intention.intention_type.toUpperCase() as IntentionType;
      countByCategory.set(
        intentionType,
        (countByCategory.get(intentionType) || 0) + 1
      );
    }

    // Convert to array - always include all categories even with 0 count
    const stats: IntentionStats[] = [
      {
        name: "Question",
        value: countByCategory.get("QUESTION") || 0,
        color: CATEGORY_COLORS.QUESTION,
      },
      {
        name: "Feedback",
        value: countByCategory.get("FEEDBACK") || 0,
        color: CATEGORY_COLORS.FEEDBACK,
      },
      {
        name: "Complaint",
        value: countByCategory.get("COMPLAINT") || 0,
        color: CATEGORY_COLORS.COMPLAINT,
      },
      {
        name: "Suggestion",
        value: countByCategory.get("SUGGESTION") || 0,
        color: CATEGORY_COLORS.SUGGESTION,
      },
      {
        name: "Praise",
        value: countByCategory.get("PRAISE") || 0,
        color: CATEGORY_COLORS.PRAISE,
      },
      {
        name: "Request",
        value: countByCategory.get("REQUEST") || 0,
        color: CATEGORY_COLORS.REQUEST,
      },
      {
        name: "Discussion",
        value: countByCategory.get("DISCUSSION") || 0,
        color: CATEGORY_COLORS.DISCUSSION,
      },
      {
        name: "Spam",
        value: countByCategory.get("SPAM") || 0,
        color: CATEGORY_COLORS.SPAM,
      },
      {
        name: "Other",
        value: countByCategory.get("OTHER") || 0,
        color: CATEGORY_COLORS.OTHER,
      },
    ];

    return stats.sort((a, b) => b.value - a.value);
  }

  async getVideoIntentionStats(id: string): Promise<IntentionStats[]> {
    const intentions = await intentionRepository.findByVideo(id);

    // Count by category
    const countByCategory = new Map<IntentionType, number>([
      ["QUESTION", 0],
      ["FEEDBACK", 0],
      ["COMPLAINT", 0],
      ["SUGGESTION", 0],
      ["PRAISE", 0],
      ["REQUEST", 0],
      ["DISCUSSION", 0],
      ["SPAM", 0],
      ["OTHER", 0],
    ]);

    for (const intention of intentions) {
      // Convert to uppercase to match database values
      const intentionType =
        intention.intention_type.toUpperCase() as IntentionType;
      countByCategory.set(
        intentionType,
        (countByCategory.get(intentionType) || 0) + 1
      );
    }

    // Convert to array - always include all categories even with 0 count
    const stats: IntentionStats[] = [
      {
        name: "Question",
        value: countByCategory.get("QUESTION") || 0,
        color: CATEGORY_COLORS.QUESTION,
      },
      {
        name: "Feedback",
        value: countByCategory.get("FEEDBACK") || 0,
        color: CATEGORY_COLORS.FEEDBACK,
      },
      {
        name: "Complaint",
        value: countByCategory.get("COMPLAINT") || 0,
        color: CATEGORY_COLORS.COMPLAINT,
      },
      {
        name: "Suggestion",
        value: countByCategory.get("SUGGESTION") || 0,
        color: CATEGORY_COLORS.SUGGESTION,
      },
      {
        name: "Praise",
        value: countByCategory.get("PRAISE") || 0,
        color: CATEGORY_COLORS.PRAISE,
      },
      {
        name: "Request",
        value: countByCategory.get("REQUEST") || 0,
        color: CATEGORY_COLORS.REQUEST,
      },
      {
        name: "Discussion",
        value: countByCategory.get("DISCUSSION") || 0,
        color: CATEGORY_COLORS.DISCUSSION,
      },
      {
        name: "Spam",
        value: countByCategory.get("SPAM") || 0,
        color: CATEGORY_COLORS.SPAM,
      },
      {
        name: "Other",
        value: countByCategory.get("OTHER") || 0,
        color: CATEGORY_COLORS.OTHER,
      },
    ];

    return stats.sort((a, b) => b.value - a.value);
  }

  async getVideoIntentions(id: string): Promise<IntentionExtraction[]> {
    return intentionRepository.findByVideo(id);
  }
}

export const intentionService = new IntentionService();
