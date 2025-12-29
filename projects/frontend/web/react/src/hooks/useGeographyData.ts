import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import { GeographyStats } from '../types/location';

interface UseGeographyDataResult {
  data: GeographyStats[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch geography statistics from the API.
 */
export function useGeographyData(): UseGeographyDataResult {
  const [data, setData] = useState<GeographyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await fetchApi<GeographyStats[]>('/locations/geography');
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
