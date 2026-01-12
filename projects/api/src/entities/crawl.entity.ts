/**
 * Web Crawl Entity
 * Represents crawled web content for tourism data
 */

export type ContentType = 'forum' | 'review' | 'blog' | 'agency' | 'auto';
export type CrawlStrategy = 'single' | 'deep';
export type ExtractionStrategy = 'css' | 'llm';

export interface CrawlReview {
  author: string | null;
  text: string;
  rating: number | null;
}

export interface CrawlComment {
  author: string | null;
  text: string;
}

export interface BlogSection {
  heading: string;
  text: string;
}

export interface AgencyInfo {
  tour_name: string | null;
  price: string | null;
  duration: string | null;
  included_services: string[];
}

export interface CrawlMeta {
  crawl_time: Date;
  language: string | null;
  crawl_strategy: CrawlStrategy;
  extraction_strategy: ExtractionStrategy;
  detected_sections: string[];
}

export interface CrawlContent {
  title: string | null;
  information: string | null;
  reviews: CrawlReview[];
  comments: CrawlComment[];
  blog_sections: BlogSection[];
  agency_info: AgencyInfo | null;
}

export interface CrawlResult {
  id: number;
  crawl_history_id: number;
  title: string | null;
  information: string | null;
  language: string | null;
  reviews_json: CrawlReview[];
  comments_json: CrawlComment[];
  blog_sections_json: BlogSection[];
  agency_info_json: AgencyInfo | null;
  detected_sections: string[];
  crawl_strategy: CrawlStrategy;
  extraction_strategy: ExtractionStrategy;
  created_at: Date;
  updated_at: Date;
}

export interface CrawlHistory {
  id: number;
  url: string;
  content_type: ContentType;
  status: string;
  created_at: Date;
  updated_at: Date;
}

export interface CrawlResultWithHistory {
  id: string;
  request_id: string;
  url: string;
  content_type: ContentType;
  from_cache: boolean;
  meta: CrawlMeta;
  content: CrawlContent;
  created_at: Date;
}
