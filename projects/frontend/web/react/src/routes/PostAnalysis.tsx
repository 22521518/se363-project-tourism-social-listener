import React, { useEffect, useState } from "react";
import { useYoutubeVideoData } from "../hooks/useYoutubeVideoData";
import VideoCard from "../components/VideoCard";
import {
  YoutubeFiltersState,
  YoutubePostFilter,
} from "../components/YoutubePostFilter";

const defaultFilter: YoutubeFiltersState = {
  channel: "all",
  timeRange: "all",
};
export default function PostAnalysis() {
  const [filters, setFilters] = useState<YoutubeFiltersState>(defaultFilter);
  const { data, meta, refetch, loading, fetchMore } = useYoutubeVideoData(
    filters.channel,
    filters.timeRange
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <YoutubePostFilter filters={filters} setFilters={setFilters} />

      <div>resuts: {meta.total}</div>
      <ul
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
        }}
      >
        {data?.map((video) => (
          <VideoCard key={video.id} video={video} />
        ))}
      </ul>

      {meta.hasMore && !loading && (
        <button
          disabled={loading}
          onClick={fetchMore}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer block mx-auto"
        >
          Load More
        </button>
      )}
      {loading && <div className="text-center text-gray-600">Loading...</div>}
    </div>
  );
}
