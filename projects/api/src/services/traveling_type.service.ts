import { travelingTypeRepository } from "../repositories/traveling_type.repository";
import {
  TravelingTypeStats,
  TravelingType,
} from "../entities/traveling_type.entity";
import { CATEGORY_COLORS } from "../entities/traveling_type.entity";


export class TravelingTypeService {
  /**
   * Aggregate traveling types by category.
   * Categories:
   */
  async getTravelingTypeStats(): Promise<TravelingTypeStats[]> {
    const travelingTypes = await travelingTypeRepository.findAll(10000);

    // Count by category
    const countByCategory = new Map<TravelingType, number>([
      ["BUSINESS", 0],
      ["LEISURE", 0],
      ["ADVENTURE", 0],
      ["BACKPACKING", 0],
      ["LUXURY", 0],
      ["BUDGET", 0],
      ["SOLO", 0],
      ["GROUP", 0],
      ["FAMILY", 0],
      ["ROMANTIC", 0],
      ["OTHER", 0],
    ]);

    for (const travelingType of travelingTypes) {
      countByCategory.set(
        travelingType.traveling_type,
        (countByCategory.get(travelingType.traveling_type) || 0) + 1
      );
    }

    // Convert to array - always include all categories even with 0 count
    const stats: TravelingTypeStats[] = [
      {
        name: "Business",
        value: countByCategory.get("BUSINESS") || 0,
        color: CATEGORY_COLORS.BUSINESS,
      },
      {
        name: "Leisure",
        value: countByCategory.get("LEISURE") || 0,
        color: CATEGORY_COLORS.LEISURE,
      },
      {
        name: "Adventure",
        value: countByCategory.get("ADVENTURE") || 0,
        color: CATEGORY_COLORS.ADVENTURE,
      },
      {
        name: "Backpacking",
        value: countByCategory.get("BACKPACKING") || 0,
        color: CATEGORY_COLORS.BACKPACKING,
      },
      {
        name: "Luxury",
        value: countByCategory.get("LUXURY") || 0,
        color: CATEGORY_COLORS.LUXURY,
      },
      {
        name: "Budget",
        value: countByCategory.get("BUDGET") || 0,
        color: CATEGORY_COLORS.BUDGET,
      },
      {
        name: "Solo",
        value: countByCategory.get("SOLO") || 0,
        color: CATEGORY_COLORS.SOLO,
      },
      {
        name: "Group",
        value: countByCategory.get("GROUP") || 0,
        color: CATEGORY_COLORS.GROUP,
      },
      {
        name: "Family",
        value: countByCategory.get("FAMILY") || 0,
        color: CATEGORY_COLORS.FAMILY,
      },
      {
        name: "Romantic",
        value: countByCategory.get("ROMANTIC") || 0,
        color: CATEGORY_COLORS.ROMANTIC,
      },
      {
        name: "Other",
        value: countByCategory.get("OTHER") || 0,
        color: CATEGORY_COLORS.OTHER,
      },
    ];

    return stats.sort((a, b) => b.value - a.value);
  }
}

export const travelingTypeService = new TravelingTypeService();
