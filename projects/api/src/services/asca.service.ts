import { ascaRepository } from "../repositories/asca.repository";
import { ASCACategoryStats, CategoryType } from "../entities/asca.entity";

// Colors for ASCA categories
const CATEGORY_COLORS: Record<CategoryType, string> = {
  LOCATION: '#3b82f6',
  PRICE: '#10b981',
  ACCOMMODATION: '#8b5cf6',
  FOOD: '#f59e0b',
  SERVICE: '#ec4899',
  AMBIENCE: '#06b6d4',
};

export interface ASCAStatsFormatted {
  category: string;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
  color: string;
}

export class ASCAService {
  /**
   * Get ASCA stats formatted for frontend.
   */
  async getStats(): Promise<ASCAStatsFormatted[]> {
    try {
      const stats = await ascaRepository.getCategoryStats();
      return this.formatStats(stats);
    } catch (error) {
      console.warn('ASCA tables may not exist:', error);
      return this.formatStats([]);
    }
  }

  /**
   * Get ASCA stats for a specific video.
   */
  async getStatsByVideoId(videoId: string): Promise<ASCAStatsFormatted[]> {
    try {
      const stats = await ascaRepository.getCategoryStatsByVideoId(videoId);
      return this.formatStats(stats);
    } catch (error) {
      console.warn('ASCA tables may not exist:', error);
      return this.formatStats([]);
    }
  }

  /**
   * Get total counts (total, approved, pending).
   */
  async getTotalCounts() {
    try {
      return await ascaRepository.getTotalCounts();
    } catch (error) {
      console.warn('ASCA tables may not exist:', error);
      return { total: 0, approved: 0, pending: 0 };
    }
  }

  /**
   * Format raw stats with colors and sorting.
   */
  private formatStats(stats: ASCACategoryStats[]): ASCAStatsFormatted[] {
    // Ensure all categories are present
    const allCategories: CategoryType[] = [
      'LOCATION',
      'PRICE',
      'ACCOMMODATION',
      'FOOD',
      'SERVICE',
      'AMBIENCE',
    ];

    const statsMap = new Map<string, ASCACategoryStats>();
    for (const stat of stats) {
      statsMap.set(stat.category, stat);
    }

    const formatted: ASCAStatsFormatted[] = allCategories.map((category) => {
      const stat = statsMap.get(category);
      return {
        category,
        positive: stat?.positive || 0,
        negative: stat?.negative || 0,
        neutral: stat?.neutral || 0,
        total: stat?.total || 0,
        color: CATEGORY_COLORS[category],
      };
    });

    // Sort by total descending
    return formatted.sort((a, b) => b.total - a.total);
  }
}

export const ascaService = new ASCAService();
