import { crawlRepository } from "../repositories/crawl.repository";
import { CrawlResultWithHistory, ContentType } from "../entities/crawl.entity";

// Colors for content types
const CONTENT_TYPE_COLORS: Record<ContentType, string> = {
  forum: '#8b5cf6',
  review: '#f59e0b',
  blog: '#3b82f6',
  agency: '#10b981',
  auto: '#6b7280',
};

export interface CrawlResultsResponse {
  data: CrawlResultWithHistory[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

export interface CrawlStatsFormatted {
  total_urls: number;
  by_content_type: Array<{
    name: string;
    value: number;
    color: string;
  }>;
}

export class CrawlService {
  /**
   * Get paginated crawl results.
   */
  async getResults(
    limit: number = 20,
    offset: number = 0,
    contentType?: string
  ): Promise<CrawlResultsResponse> {
    const typeFilter = contentType && contentType !== 'all'
      ? contentType as ContentType
      : undefined;

    try {
      const [results, total] = await Promise.all([
        crawlRepository.findAll(limit, offset, typeFilter),
        crawlRepository.getCount(typeFilter),
      ]);

      return {
        data: results,
        meta: {
          total,
          limit,
          offset,
          hasMore: offset + results.length < total,
        },
      };
    } catch (error) {
      // Handle case where tables don't exist
      console.warn('Crawl tables may not exist:', error);
      return {
        data: [],
        meta: {
          total: 0,
          limit,
          offset,
          hasMore: false,
        },
      };
    }
  }

  /**
   * Get crawl statistics.
   */
  async getStats(): Promise<CrawlStatsFormatted> {
    const [byType, total] = await Promise.all([
      crawlRepository.getStatsByContentType(),
      crawlRepository.getCount(),
    ]);

    const contentTypes: ContentType[] = ['review', 'blog', 'forum', 'agency', 'auto'];

    return {
      total_urls: total,
      by_content_type: contentTypes.map((type) => ({
        name: type.charAt(0).toUpperCase() + type.slice(1),
        value: byType[type] || 0,
        color: CONTENT_TYPE_COLORS[type],
      })),
    };
  }
}

export const crawlService = new CrawlService();
