import { useState, useEffect, useCallback } from "react";
import { fetchApi } from "../services/api";
import { YouTubeVideo } from "../types/youtube_video";

interface UseYoutubeVideoDataResult {
  data: YouTubeVideo[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useYoutubeVideoData(
  limit = 20,
  offset = 0
): UseYoutubeVideoDataResult {
  const [data, setData] = useState<YouTubeVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<YouTubeVideo[]>(
        `/youtube_videos?limit=${limit}&offset=${offset}`
      );
      setData(prev => [...prev, ...data]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
      // Fallback to empty array on error
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
