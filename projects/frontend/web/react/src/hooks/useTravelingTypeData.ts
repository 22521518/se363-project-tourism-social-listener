import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import { TravelingTypeStats } from '../types/traveling-type';

interface UseTravelingTypeDataResult {
  data: TravelingTypeStats[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useTravelingTypeData(): UseTravelingTypeDataResult {
  const [data, setData] = useState<TravelingTypeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await fetchApi<TravelingTypeStats[]>('/traveling_types/stats');
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      // Fallback to empty array on error
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
