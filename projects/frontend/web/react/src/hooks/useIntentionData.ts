import { useState, useEffect, useCallback } from 'react';
import { fetchApi } from '../services/api';
import { IntentionStats } from '../types/intention';

interface UseIntentionsDataResult {
  data: IntentionStats[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch intentions statistics from the API.
 */
export function useIntentionsData(): UseIntentionsDataResult {
  const [data, setData] = useState<IntentionStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await fetchApi<IntentionStats[]>('/intentions/stats');
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
