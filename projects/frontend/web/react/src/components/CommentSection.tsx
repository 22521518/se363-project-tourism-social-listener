import React, { useEffect, useState } from "react";
import { AdvancedFilters } from "./AdvancedFilters";
import { QuickStats } from "./QuickStats";
import { SemanticAnalysis } from "./SemanticAnalysis";
import { TourismClassification } from "./TourismClassification";
import {
  useYoutubeCommentIntentionData,
  useYoutubeCommentTravelingTypeData,
} from "../hooks/useYoutubeCommentData";
import CommentCard from "./CommentCard";

export default function CommentSection({ videoId }: { videoId: string }) {
  const [tab, setTab] = useState<
    "intention" | "traveling_type" | "location" | "sentiment"
  >("intention");
  const [filters, setFilters] = useState({
    tourismType: "all",
    // tourismOrg: 'all',
    postIntention: "all",
    tourismGeo: "all",
    postType: "comment",
    timeRange: "7d",
    sentiment: "all",
  });
  const {
    data: intentionComments,
    meta: intentionCommentMeta,
    loading: intentionCommentLoading,
    fetchMore: fetchMoreIntentionComment,
  } = useYoutubeCommentIntentionData(
    videoId,
    filters.postIntention,
    filters.timeRange
  );

  const {
    data: travelingTypeComments,
    meta: travelingTypeCommentMeta,
    loading: travelingTypeCommentLoading,
    fetchMore: fetchMoreTravelingTypeComment,
  } = useYoutubeCommentTravelingTypeData(
    videoId,
    filters.tourismType,
    filters.timeRange
  );

  const { data, meta, loading, fetchMore } =
    tab === "intention"
      ? {
          data: intentionComments,
          meta: intentionCommentMeta,
          loading: intentionCommentLoading,
          fetchMore: fetchMoreIntentionComment,
        }
      : tab === "traveling_type"
      ? {
          data: travelingTypeComments,
          meta: travelingTypeCommentMeta,
          loading: travelingTypeCommentLoading,
          fetchMore: fetchMoreTravelingTypeComment,
        }
      : { data: [], meta: null, loading: false, fetchMore: () => {} }; // for location & sentiment → empty
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* <QuickStats filters={filters} /> */}

      <TourismClassification id={videoId} filters={filters} />
      {/* <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <PostTypeAnalysis filters={filters} />
            </div> */}

      <SemanticAnalysis filters={filters} />
      <AdvancedFilters filters={filters} setFilters={setFilters} />
      {/* Tab buttons */}
      <div
        style={{ display: "flex", gap: 8 }}
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6"
      >

        {["intention", "traveling_type", "location", "sentiment"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t as typeof tab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors border ${
              tab === t
                ? "bg-blue-600 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <ul
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 6,
        }}
      >
        {data?.map((c) => (
          <CommentCard key={c.id} comment={c} />
        ))}
      </ul>
      {meta?.hasMore && (
        <button
          disabled={loading}
          onClick={() =>fetchMore()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer block mx-auto"
        >
          Load More
        </button>
      )}
      {loading && <div className="text-center text-gray-600">Loading...</div>}
    </div>
  );
}
