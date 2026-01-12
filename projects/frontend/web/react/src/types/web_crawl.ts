/**
 * Web Crawl types for the frontend.
 * Maps to backend DTOs from projects/services/ingestion/web-crawl
 */

// Content type for crawl requests
export type ContentType = 'forum' | 'review' | 'blog' | 'agency' | 'auto';

// Crawl strategy
export type CrawlStrategy = 'single' | 'deep';

// Extraction strategy
export type ExtractionStrategy = 'css' | 'llm';

/**
 * Review data extracted from the page.
 */
export interface CrawlReview {
  author: string | null;
  text: string;
  rating: number | null;
}

/**
 * Comment/discussion data extracted from forums.
 */
export interface CrawlComment {
  author: string | null;
  text: string;
}

/**
 * Blog section with heading and content.
 */
export interface BlogSection {
  heading: string;
  text: string;
}

/**
 * Travel agency/tour information.
 */
export interface AgencyInfo {
  tour_name: string | null;
  price: string | null;
  duration: string | null;
  included_services: string[];
}

/**
 * Metadata about the crawl operation.
 */
export interface CrawlMeta {
  crawl_time: string;
  language: string | null;
  crawl_strategy: CrawlStrategy;
  extraction_strategy: ExtractionStrategy;
  detected_sections: string[];
}

/**
 * Content container for crawl results.
 */
export interface CrawlContent {
  title: string | null;
  information: string | null;
  reviews: CrawlReview[];
  comments: CrawlComment[];
  blog_sections: BlogSection[];
  agency_info: AgencyInfo | null;
}

/**
 * Complete crawl result matching the output contract.
 */
export interface CrawlResult {
  id: string;
  request_id: string;
  url: string;
  content_type: ContentType;
  from_cache: boolean;
  meta: CrawlMeta;
  content: CrawlContent;
  created_at: string;
}

/**
 * Paginated crawl results response.
 */
export interface CrawlResultsWithMeta {
  data: CrawlResult[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
}

/**
 * Statistics for crawl results.
 */
export interface CrawlStats {
  total_urls: number;
  by_content_type: Record<ContentType, number>;
  total_reviews: number;
  total_comments: number;
  total_blogs: number;
}

// Colors for content types
export const CONTENT_TYPE_COLORS: Record<ContentType, string> = {
  forum: '#8b5cf6',    // Purple
  review: '#f59e0b',   // Amber
  blog: '#3b82f6',     // Blue
  agency: '#10b981',   // Green
  auto: '#6b7280',     // Gray
};
