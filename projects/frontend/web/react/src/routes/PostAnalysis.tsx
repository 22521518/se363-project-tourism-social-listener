import React, { useState, useMemo } from "react";
import { Loader2 } from "lucide-react";
import {
  YoutubeFiltersState,
  YoutubePostFilter,
} from "../components/YoutubePostFilter";
import { DataSourceTabs, DataSourceType } from "../components/DataSourceTabs";
import { WebCrawlResults } from "../components/WebCrawlResults";
import { VideoListItem } from "../components/VideoListItem";
import { QuickStatsBar } from "../components/QuickStatsBar";
import { useVideosWithStats } from "../hooks/useVideosWithStats";
import { ProcessingTaskTabs, TabType } from "../components/ProcessingTaskTabs";
import { RawDataList } from "../components/RawDataList";
import { LocationHierarchy } from "../components/LocationHierarchy";
import { ProcessingTask } from "../types/raw_data";

const defaultFilter: YoutubeFiltersState = {
  channel: "all",
  timeRange: "all",
};

export default function PostAnalysis() {
  const [activeSource, setActiveSource] = useState<DataSourceType>("youtube");
  const [activeTab, setActiveTab] = useState<TabType>("summary");
  const [filters, setFilters] = useState<YoutubeFiltersState>(defaultFilter);
  
  const { data, meta, loading, error, fetchMore } = useVideosWithStats(
    filters.channel,
    filters.timeRange
  );

  // Calculate aggregate stats from videos
  const aggregateStats = useMemo(() => {
    let totalComments = 0;
    let totalProcessed = 0;
    let positiveCount = 0;
    let negativeCount = 0;

    for (const video of data) {
      totalComments += video.stats.total_comments;
      totalProcessed += video.stats.processed_count;
      positiveCount += video.stats.sentiment.positive;
      negativeCount += video.stats.sentiment.negative;
    }

    return { totalComments, totalProcessed, positiveCount, negativeCount };
  }, [data]);

  // Render content based on active tab
  const renderTabContent = () => {
    if (activeTab === "summary") {
      // Summary tab shows the original video list with quick stats
      return (
        <>
          {/* Filters */}
          <YoutubePostFilter filters={filters} setFilters={setFilters} />

          {/* Quick Stats */}
          <QuickStatsBar
            totalVideos={meta.total}
            totalComments={aggregateStats.totalComments}
            totalProcessed={aggregateStats.totalProcessed}
            positiveCount={aggregateStats.positiveCount}
            negativeCount={aggregateStats.negativeCount}
          />

          {/* Video List */}
          <div className="space-y-4">
            {loading && data.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 flex items-center justify-center">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-gray-600">Loading videos...</span>
              </div>
            ) : error && data.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center text-gray-500">
                {error}
              </div>
            ) : data.length === 0 ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center text-gray-500">
                No videos with processing data found
              </div>
            ) : (
              <>
                {data.map((video) => (
                  <VideoListItem key={video.id} video={video} />
                ))}

                {/* Load More */}
                {meta.hasMore && (
                  <button
                    disabled={loading}
                    onClick={fetchMore}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      `Load More (${meta.total - data.length} remaining)`
                    )}
                  </button>
                )}
              </>
            )}
          </div>
        </>
      );
    }

    if (activeTab === "location_extraction") {
      // Location tab shows hierarchy drill-down
      return (
        <div className="space-y-4">
          <LocationHierarchy 
            onLocationClick={(type, id, name) => {
              console.log(`Clicked ${type}: ${id} (${name})`);
            }}
          />
          <RawDataList 
            sourceType={activeSource === "youtube" ? "youtube" : "webcrawl"} 
            taskFilter="location_extraction" 
          />
        </div>
      );
    }

    // Other task tabs show raw data filtered by that task
    return (
      <RawDataList 
        sourceType={activeSource === "youtube" ? "youtube" : "webcrawl"} 
        taskFilter={activeTab as ProcessingTask} 
      />
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Data Source Tabs (YouTube / Web Crawl) */}
        <DataSourceTabs
          activeSource={activeSource}
          onSourceChange={(source) => {
            setActiveSource(source);
            setActiveTab("summary");
          }}
        />

        {/* Processing Task Tabs */}
        <ProcessingTaskTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Tab Content */}
        {activeSource === "youtube" ? (
          renderTabContent()
        ) : (
          // Web Crawl section
          activeTab === "summary" ? (
            <WebCrawlResults />
          ) : activeTab === "location_extraction" ? (
            <div className="space-y-4">
              <LocationHierarchy />
              <RawDataList sourceType="webcrawl" taskFilter="location_extraction" />
            </div>
          ) : (
            <RawDataList sourceType="webcrawl" taskFilter={activeTab as ProcessingTask} />
          )
        )}
      </main>
    </div>
  );
}
