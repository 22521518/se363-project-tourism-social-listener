import { useState, useEffect, useCallback } from "react";
import { fetchApi } from "../services/api";
import {
  YoutubeVideo,
  YoutubeVideoListMeta,
  YoutubeVideoListWithMeta,
} from "../types/youtube_video";

interface UseYoutubeVideoDataResult {
  data: YoutubeVideo[];
  meta: YoutubeVideoListMeta;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
}

const limit = 20;
/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useYoutubeVideoData(
  channel = "all",
  timeRange = "all"
): UseYoutubeVideoDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<YoutubeVideo[]>([]);
  const [meta, setMeta] = useState<YoutubeVideoListMeta>({
    total: 0,
    limit: 0,
    offset: 0,
    hasMore: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<YoutubeVideoListWithMeta>(
        `/youtube_videos?limit=${limit}&offset=${offset}&channel=${channel}&timeRange=${timeRange}`
      );
      setData((prev) => {
        return offset === 0 ? data.data : [...prev, ...data.data];
      });

      setMeta(data.meta);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data");
      // Fallback to empty array on error
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [limit, offset, channel, timeRange]);

  useEffect(() => {
    setOffset(0);
  }, [channel, timeRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    meta,
    loading,
    error,
    refetch: fetchData,
    fetchMore: () => setOffset((prev) => prev + limit),
  };
}
