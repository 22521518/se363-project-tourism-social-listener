import { useState, useEffect, useCallback } from "react";
import { fetchApi } from "../services/api";
import { YouTubeComment } from "../types/youtube_comment";

interface UseYoutubeCommentDataResult {
  data: YouTubeComment[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

interface UseYoutubeVideoCommentDataResult {
  data: YouTubeComment[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}
/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useYoutubeCommentData(): UseYoutubeCommentDataResult {
  const [data, setData] = useState<YouTubeComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await fetchApi<YouTubeComment[]>("/youtube_comments");
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
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

export function useYoutubeVideoCommentData(id:string): UseYoutubeVideoCommentDataResult {
  const [data, setData] = useState<YouTubeComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await fetchApi<YouTubeComment[]>(`/youtube_comments/videos/${id}`);
      setData(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
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
