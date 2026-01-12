import { useState, useCallback } from 'react';
import { fetchApi } from '../services/api';
import {
  YouTubeCommentWithStats,
  CommentsWithStatsResponse,
} from '../types/video_with_stats';

interface UseCommentsWithStatsResult {
  data: YouTubeCommentWithStats[];
  meta: {
    total: number;
    hasMore: boolean;
  };
  loading: boolean;
  error: string | null;
  fetch: () => void;
  fetchMore: () => void;
}

const DEFAULT_LIMIT = 10;

/**
 * Hook to fetch comments for a video with processing stats
 */
export function useCommentsWithStats(videoId: string): UseCommentsWithStatsResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<YouTubeCommentWithStats[]>([]);
  const [meta, setMeta] = useState({ total: 0, hasMore: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (newOffset = 0) => {
    if (!videoId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetchApi<CommentsWithStatsResponse>(
        `/videos_with_stats/${videoId}/comments?limit=${DEFAULT_LIMIT}&offset=${newOffset}`
      );

      const responseData = response?.data || [];
      const responseMeta = response?.meta || { total: 0, hasMore: false };

      setData((prev) => (newOffset === 0 ? responseData : [...prev, ...responseData]));
      setMeta(responseMeta);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch comments');
      if (newOffset === 0) {
        setData([]);
        setMeta({ total: 0, hasMore: false });
      }
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  return {
    data,
    meta,
    loading,
    error,
    fetch: () => {
      setOffset(0);
      fetchData(0);
    },
    fetchMore: () => {
      const newOffset = offset + DEFAULT_LIMIT;
      setOffset(newOffset);
      fetchData(newOffset);
    },
  };
}
