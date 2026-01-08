import React, { useState } from "react";
import { useYoutubeVideoData } from "../hooks/useYoutubeVideoData";
import VideoCard from "../components/VideoCard";

export default function PostAnalysis() {
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const { data, refetch, loading } = useYoutubeVideoData(limit, offset);

  return (
    <div className="space-y-6">
      {data?.map((video) => (
        <VideoCard key={video.id} video={video} />
      ))}

      <button
        onClick={() => {
          setOffset(offset + limit);
        }}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer block mx-auto"
      >
        Load More
      </button>
      {loading && <div className="text-center text-gray-600">Loading...</div>}
    </div>
  );
}
