import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import { ASCAStats, CATEGORY_COLORS, CategoryType } from '../types/asca';

interface ASCAStatsFormatted {
  category: string;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
  color: string;
}

interface UseASCADataResult {
  data: ASCAStatsFormatted[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch ASCA (Aspect-based Sentiment) statistics from the API.
 * @param videoId Optional video ID to filter stats for a specific video
 */
export function useASCAData(videoId = ''): UseASCADataResult {
  const [data, setData] = useState<ASCAStatsFormatted[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = videoId
        ? `/asca/stats/video/${videoId}`
        : '/asca/stats';

      const stats = await fetchApi<ASCAStats[]>(endpoint);

      // Format data with colors
      const formatted = stats.map((item) => ({
        category: item.category,
        positive: item.positive,
        negative: item.negative,
        neutral: item.neutral,
        total: item.total,
        color: CATEGORY_COLORS[item.category as CategoryType] || '#6b7280',
      }));

      setData(formatted);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch ASCA data');
      // Fallback to empty array on error
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
