import { useState, useEffect, useCallback } from "react";
import { fetchApi } from "../services/api";
import {
  YoutubeComment,
  YoutubeCommentListMeta,
  YoutubeCommentListWithMeta,
} from "../types/youtube_comment";

interface UseYoutubeCommentDataResult {
  data: YoutubeComment[];
  meta: YoutubeCommentListMeta;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  fetchMore: () => void;
}

const limit = 20;
/**
 * Custom hook to fetch traveling type statistics from the API.
 */
export function useYoutubeCommentIntentionData(
  video_id = "",
  intention_type = "all",
  timeRange = "all"
): UseYoutubeCommentDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<YoutubeComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState<YoutubeCommentListMeta>({
    total: 0,
    limit: 0,
    offset: 0,
    hasMore: false,
  });
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<YoutubeCommentListWithMeta>(
        `/youtube_comments/video/${video_id}/intention?limit=${limit}&offset=${offset}&intention_type=${intention_type}&timeRange=${timeRange}`
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
  }, [limit, offset, video_id, intention_type, timeRange]);

  useEffect(() => {
    setOffset(0);
  }, [intention_type, timeRange]);

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

export function useYoutubeCommentTravelingTypeData(
  video_id = "",
  traveling_type = "all",
  timeRange = "all"
): UseYoutubeCommentDataResult {
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<YoutubeComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState<YoutubeCommentListMeta>({
    total: 0,
    limit: 0,
    offset: 0,
    hasMore: false,
  });
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi<YoutubeCommentListWithMeta>(
        `/youtube_comments/video/${video_id}/traveling_type?limit=${limit}&offset=${offset}&traveling_type=${traveling_type}&timeRange=${timeRange}`
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
  }, [limit, offset, video_id, traveling_type, timeRange]);

  useEffect(() => {
    setOffset(0);
  }, [traveling_type, timeRange]);

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
