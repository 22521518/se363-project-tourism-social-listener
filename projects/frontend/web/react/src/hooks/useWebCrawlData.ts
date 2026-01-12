import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import { CrawlResult, CrawlResultsWithMeta } from '../types/web_crawl';

interface CrawlResultMeta {
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

interface UseWebCrawlDataResult {
  data: CrawlResult[];
  meta: CrawlResultMeta;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
}

const DEFAULT_LIMIT = 20;

/**
 * Custom hook to fetch web crawl results from the API.
 * @param contentType Optional content type filter
 */
export function useWebCrawlData(contentType = 'all'): UseWebCrawlDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<CrawlResult[]>([]);
  const [meta, setMeta] = useState<CrawlResultMeta>({
    total: 0,
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasMore: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const typeParam = contentType !== 'all' ? `&content_type=${contentType}` : '';
      const response = await fetchApi<CrawlResultsWithMeta>(
        `/crawl_results?limit=${DEFAULT_LIMIT}&offset=${offset}${typeParam}`
      );

      // Safely handle response data
      const responseData = response?.data || [];
      const responseMeta = response?.meta || {
        total: 0,
        limit: DEFAULT_LIMIT,
        offset: 0,
        hasMore: false,
      };

      setData((prev) => {
        return offset === 0 ? responseData : [...prev, ...responseData];
      });
      setMeta(responseMeta);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch crawl data');
      // Keep existing data on error for pagination, reset if first page
      if (offset === 0) {
        setData([]);
        setMeta({
          total: 0,
          limit: DEFAULT_LIMIT,
          offset: 0,
          hasMore: false,
        });
      }
    } finally {
      setLoading(false);
    }
  }, [offset, contentType]);

  // Reset offset when content type changes
  useEffect(() => {
    setOffset(0);
  }, [contentType]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    loading,
    error,
    refetch: () => {
      setOffset(0);
      fetchData();
    },
    fetchMore: () => setOffset((prev) => prev + DEFAULT_LIMIT),
  };
}
