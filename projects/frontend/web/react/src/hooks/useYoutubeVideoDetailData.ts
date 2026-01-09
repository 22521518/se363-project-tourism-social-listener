import { useState, useEffect, useCallback } from "react";
import { fetchApi } from "../services/api";
import {
  YouTubeVideo,
  YoutubeVideoListMeta,
  YoutubeVideoListWithMeta,
} from "../types/youtube_video";

interface UseYoutubeVideoDataResult {
  data: YouTubeVideo | undefined;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useYoutubeVideoDetailData(
  id: string | undefined
): UseYoutubeVideoDataResult {
  const [data, setData] = useState<YouTubeVideo>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<YouTubeVideo>(`/youtube_videos/${id}`);
      setData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
      // Fallback to empty array on error
      setData(undefined);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
