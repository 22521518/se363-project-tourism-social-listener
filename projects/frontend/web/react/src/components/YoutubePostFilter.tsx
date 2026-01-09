import { Filter } from "lucide-react";
import { useYoutubeChannelData } from "../hooks/useYoutubeChannelData";
import { ImageWithFallback } from "./figma/ImageWithFallback";

export interface YoutubeFiltersState {
  channel: string;
  timeRange: string;
}

export interface YoutubePostFilterProps {
  filters: YoutubeFiltersState;
  setFilters: (filters: YoutubeFiltersState) => void;
}

export function YoutubePostFilter({
  filters,
  setFilters,
}: YoutubePostFilterProps) {
  const { data: channels, loading } = useYoutubeChannelData();
  const updateFilter = (key: keyof YoutubeFiltersState, value: string) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-blue-600" />
        <span className="text-gray-900">Smart Filters</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Channel */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Channel</label>
          <select
            value={filters.channel}
            onChange={(e) => updateFilter("channel", e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Channels</option>
            {channels?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title}
              </option>
            ))}
          </select>
        </div>

        {/* Time Range */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Time Range</label>
          <select
            value={filters.timeRange}
            onChange={(e) => updateFilter("timeRange", e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Time</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
            <option value="6m">Last 6 Months</option>
            <option value="1y">Last Year</option>
          </select>
        </div>
      </div>
    </div>
  );
}
