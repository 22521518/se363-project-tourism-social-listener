import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import {
  RawDataItem,
  RawDataResponse,
  ProcessingFilter,
  ProcessingTask,
  ProcessingSummary,
} from '../types/raw_data';

interface UseRawDataResult {
  data: RawDataItem[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  summary: ProcessingSummary;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
}

const DEFAULT_LIMIT = 20;

const DEFAULT_SUMMARY: ProcessingSummary = {
  total_items: 0,
  processed_counts: {
    asca: 0,
    intention: 0,
    location_extraction: 0,
    traveling_type: 0,
  },
};

/**
 * Hook to fetch raw YouTube data with processing status
 */
export function useRawYouTubeData(
  processingFilter: ProcessingFilter = 'all',
  task: ProcessingTask | 'all' = 'all'
): UseRawDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<RawDataItem[]>([]);
  const [meta, setMeta] = useState({
    total: 0,
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasMore: false,
  });
  const [summary, setSummary] = useState<ProcessingSummary>(DEFAULT_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: DEFAULT_LIMIT.toString(),
        offset: offset.toString(),
        processing_status: processingFilter,
        task,
      });

      const response = await fetchApi<RawDataResponse>(
        `/raw_data/youtube?${params.toString()}`
      );

      console.log('useRawYouTubeData response:', response);
      console.log('useRawYouTubeData response.data:', response?.data);

      const responseData = response?.data || [];
      const responseMeta = response?.meta || {
        total: 0,
        limit: DEFAULT_LIMIT,
        offset: 0,
        hasMore: false,
      };
      const responseSummary = response?.summary || DEFAULT_SUMMARY;

      setData((prev) => (offset === 0 ? responseData : [...prev, ...responseData]));
      setMeta(responseMeta);
      setSummary(responseSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      if (offset === 0) {
        setData([]);
        setMeta({ total: 0, limit: DEFAULT_LIMIT, offset: 0, hasMore: false });
        setSummary(DEFAULT_SUMMARY);
      }
    } finally {
      setLoading(false);
    }
  }, [offset, processingFilter, task]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [processingFilter, task]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    summary,
    loading,
    error,
    refetch: () => {
      setOffset(0);
      fetchData();
    },
    fetchMore: () => setOffset((prev) => prev + DEFAULT_LIMIT),
  };
}

/**
 * Hook to fetch raw WebCrawl data with processing status
 */
export function useRawWebCrawlData(
  processingFilter: ProcessingFilter = 'all',
  task: ProcessingTask | 'all' = 'all'
): UseRawDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<RawDataItem[]>([]);
  const [meta, setMeta] = useState({
    total: 0,
    limit: DEFAULT_LIMIT,
    offset: 0,
    hasMore: false,
  });
  const [summary, setSummary] = useState<ProcessingSummary>(DEFAULT_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: DEFAULT_LIMIT.toString(),
        offset: offset.toString(),
        processing_status: processingFilter,
        task,
      });

      const response = await fetchApi<RawDataResponse>(
        `/raw_data/webcrawl?${params.toString()}`
      );

      const responseData = response?.data || [];
      const responseMeta = response?.meta || {
        total: 0,
        limit: DEFAULT_LIMIT,
        offset: 0,
        hasMore: false,
      };
      const responseSummary = response?.summary || DEFAULT_SUMMARY;

      setData((prev) => (offset === 0 ? responseData : [...prev, ...responseData]));
      setMeta(responseMeta);
      setSummary(responseSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      if (offset === 0) {
        setData([]);
        setMeta({ total: 0, limit: DEFAULT_LIMIT, offset: 0, hasMore: false });
        setSummary(DEFAULT_SUMMARY);
      }
    } finally {
      setLoading(false);
    }
  }, [offset, processingFilter, task]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [processingFilter, task]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    summary,
    loading,
    error,
    refetch: () => {
      setOffset(0);
      fetchData();
    },
    fetchMore: () => setOffset((prev) => prev + DEFAULT_LIMIT),
  };
}
