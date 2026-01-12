import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import {
  YouTubeVideoWithStats,
  VideosWithStatsResponse,
} from '../types/video_with_stats';

interface UseVideosWithStatsResult {
  data: YouTubeVideoWithStats[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
}

const DEFAULT_LIMIT = 10;

/**
 * Hook to fetch videos with processing stats
 */
export function useVideosWithStats(
  channel = 'all',
  timeRange = 'all',
  filters?: {
    sentiment?: string;
    intention?: string;
    travelType?: string;
    aspect?: string;
  }
): UseVideosWithStatsResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<YouTubeVideoWithStats[]>([]);
  const [meta, setMeta] = useState({
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
      const params = new URLSearchParams({
        limit: DEFAULT_LIMIT.toString(),
        offset: offset.toString(),
        channel,
        time_range: timeRange,
      });

      if (filters?.sentiment) params.append('sentiment', filters.sentiment);
      if (filters?.intention) params.append('intention', filters.intention);
      if (filters?.travelType) params.append('travel_type', filters.travelType);
      if (filters?.aspect) params.append('aspect', filters.aspect);

      const response = await fetchApi<VideosWithStatsResponse>(
        `/videos_with_stats?${params.toString()}`
      );

      const responseData = response?.data || [];
      const responseMeta = response?.meta || {
        total: 0,
        limit: DEFAULT_LIMIT,
        offset: 0,
        hasMore: false,
      };

      setData((prev) => (offset === 0 ? responseData : [...prev, ...responseData]));
      setMeta(responseMeta);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch videos');
      if (offset === 0) {
        setData([]);
        setMeta({ total: 0, limit: DEFAULT_LIMIT, offset: 0, hasMore: false });
      }
    } finally {
      setLoading(false);
    }
  }, [offset, channel, timeRange, filters?.sentiment, filters?.intention, filters?.travelType, filters?.aspect]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [channel, timeRange, filters?.sentiment, filters?.intention, filters?.travelType, filters?.aspect]);

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
