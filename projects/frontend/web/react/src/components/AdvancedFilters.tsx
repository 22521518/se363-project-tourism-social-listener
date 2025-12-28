import { Filter, Calendar } from 'lucide-react';

interface FiltersState {
  tourismPurpose: string;
  tourismOrg: string;
  tourismGeo: string;
  postType: string;
  timeRange: string;
  sentiment: string;
}

interface AdvancedFiltersProps {
  filters: FiltersState;
  setFilters: (filters: FiltersState) => void;
}

export function AdvancedFilters({ filters, setFilters }: AdvancedFiltersProps) {
  const updateFilter = (key: keyof FiltersState, value: string) => {
    setFilters({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-blue-600" />
        <span className="text-gray-900">Smart Filters</span>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Tourism Purpose */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Tourism Purpose</label>
          <select
            value={filters.tourismPurpose}
            onChange={(e) => updateFilter('tourismPurpose', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Purposes</option>
            <option value="leisure">Leisure/Vacation</option>
            <option value="business">Business</option>
            <option value="adventure">Adventure</option>
            <option value="cultural">Cultural</option>
            <option value="eco">Eco-Tourism</option>
            <option value="wellness">Wellness/Spa</option>
            <option value="religious">Religious</option>
          </select>
        </div>

        {/* Tourism Organization */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Organization Type</label>
          <select
            value={filters.tourismOrg}
            onChange={(e) => updateFilter('tourismOrg', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="individual">Individual/Solo</option>
            <option value="couple">Couple</option>
            <option value="family">Family</option>
            <option value="group">Group</option>
            <option value="package">Package Tour</option>
            <option value="self-planned">Self-Planned</option>
          </select>
        </div>

        {/* Tourism Geography */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Geography</label>
          <select
            value={filters.tourismGeo}
            onChange={(e) => updateFilter('tourismGeo', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Regions</option>
            <option value="domestic">Domestic</option>
            <option value="international">International</option>
            <option value="regional">Regional/Nearby</option>
            <option value="long-haul">Long-Haul</option>
          </select>
        </div>

        {/* Post Type */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Post Type</label>
          <select
            value={filters.postType}
            onChange={(e) => updateFilter('postType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Posts</option>
            <option value="agency-question">Travel Agency Question</option>
            <option value="user-review">User Review</option>
            <option value="influencer">Influencer/Celebrity</option>
            <option value="itinerary">Itinerary Share</option>
            <option value="inquiry">Travel Inquiry</option>
          </select>
        </div>

        {/* Time Range */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Time Range</label>
          <select
            value={filters.timeRange}
            onChange={(e) => updateFilter('timeRange', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>

        {/* Sentiment */}
        <div>
          <label className="block text-sm text-gray-600 mb-2">Sentiment</label>
          <select
            value={filters.sentiment}
            onChange={(e) => updateFilter('sentiment', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>
        </div>
      </div>
    </div>
  );
}
