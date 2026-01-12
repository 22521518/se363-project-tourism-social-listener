import { Brain, ThumbsUp, ThumbsDown, Minus, DollarSign, MapPin, Utensils, Hotel, Star, Loader2, LucideIcon } from 'lucide-react';
import { useASCAData } from '../hooks/useASCAData';

interface SemanticAnalysisProps {
  filters: any;
  videoId?: string;
}

// Icon mapping for ASCA categories
const CATEGORY_ICONS: Record<string, LucideIcon> = {
  LOCATION: MapPin,
  PRICE: DollarSign,
  ACCOMMODATION: Hotel,
  FOOD: Utensils,
  SERVICE: Star,
  AMBIENCE: Brain,
};

// Color mapping for ASCA categories
const CATEGORY_COLOR_CLASSES: Record<string, string> = {
  LOCATION: 'bg-blue-100 text-blue-600',
  PRICE: 'bg-green-100 text-green-600',
  ACCOMMODATION: 'bg-purple-100 text-purple-600',
  FOOD: 'bg-orange-100 text-orange-600',
  SERVICE: 'bg-pink-100 text-pink-600',
  AMBIENCE: 'bg-cyan-100 text-cyan-600',
};

// Category display names
const CATEGORY_NAMES: Record<string, string> = {
  LOCATION: 'Location/Destination',
  PRICE: 'Price/Value',
  ACCOMMODATION: 'Accommodation',
  FOOD: 'Food/Dining',
  SERVICE: 'Service Quality',
  AMBIENCE: 'Ambience',
};

export function SemanticAnalysis({ filters, videoId }: SemanticAnalysisProps) {
  const { data, loading, error } = useASCAData(videoId);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading semantic analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Semantic Analysis by Aspects</h2>
        </div>
        <div className="text-sm text-red-500 py-4 text-center">{error}</div>
      </div>
    );
  }

  // Filter out categories with no data
  const aspectsWithData = data.filter(item => item.total > 0);

  if (aspectsWithData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Semantic Analysis by Aspects</h2>
        </div>
        <div className="text-sm text-gray-500 py-4 text-center">
          No ASCA analysis data available yet
        </div>
      </div>
    );
  }

  // Calculate totals
  const totals = data.reduce(
    (acc, item) => ({
      positive: acc.positive + item.positive,
      negative: acc.negative + item.negative,
      neutral: acc.neutral + item.neutral,
      total: acc.total + item.total,
    }),
    { positive: 0, negative: 0, neutral: 0, total: 0 }
  );

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
      <div className="flex items-center gap-2 mb-6">
        <Brain className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Semantic Analysis by Aspects</h2>
          <p className="text-sm text-gray-600">Detailed breakdown of mentions by topic (ASCA)</p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
          <div>
            <p className="text-2xl font-semibold text-blue-700">
              {totals.total.toLocaleString()}
            </p>
            <p className="text-sm text-blue-600">Total Mentions</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 bg-green-50 rounded-lg">
          <ThumbsUp className="w-5 h-5 text-green-600" />
          <div>
            <p className="text-2xl font-semibold text-green-700">
              {totals.positive.toLocaleString()}
            </p>
            <p className="text-sm text-green-600">Positive</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 bg-red-50 rounded-lg">
          <ThumbsDown className="w-5 h-5 text-red-600" />
          <div>
            <p className="text-2xl font-semibold text-red-700">
              {totals.negative.toLocaleString()}
            </p>
            <p className="text-sm text-red-600">Negative</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <Minus className="w-5 h-5 text-gray-600" />
          <div>
            <p className="text-2xl font-semibold text-gray-700">
              {totals.neutral.toLocaleString()}
            </p>
            <p className="text-sm text-gray-600">Neutral</p>
          </div>
        </div>
      </div>

      {/* Aspect Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {data.map((aspect) => {
          const Icon = CATEGORY_ICONS[aspect.category] || Brain;
          const colorClass = CATEGORY_COLOR_CLASSES[aspect.category] || 'bg-gray-100 text-gray-600';
          const displayName = CATEGORY_NAMES[aspect.category] || aspect.category;
          const total = aspect.positive + aspect.negative + aspect.neutral;
          const sentiment = total > 0 ? Math.round((aspect.positive / total) * 100) : 0;
          
          return (
            <div key={aspect.category} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4 mb-4">
                <div className={`p-3 rounded-lg ${colorClass}`}>
                  <Icon className="w-6 h-6" />
                </div>
                
                <div className="flex-1">
                  <h3 className="text-gray-900 mb-1">{displayName}</h3>
                  <p className="text-sm text-gray-600">{total.toLocaleString()} mentions</p>
                </div>
                
                <div className="text-right">
                  <div className={`text-sm px-3 py-1 rounded-full ${
                    sentiment >= 80 ? 'bg-green-100 text-green-700' :
                    sentiment >= 60 ? 'bg-yellow-100 text-yellow-700' :
                    sentiment >= 40 ? 'bg-orange-100 text-orange-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {sentiment}% positive
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Positive</p>
                    <p className="text-green-600 font-semibold">{aspect.positive.toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <ThumbsDown className="w-4 h-4 text-red-600" />
                  <div>
                    <p className="text-sm text-gray-600">Negative</p>
                    <p className="text-red-600 font-semibold">{aspect.negative.toLocaleString()}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Minus className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-sm text-gray-600">Neutral</p>
                    <p className="text-gray-600 font-semibold">{aspect.neutral.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {/* Sentiment Bar */}
              <div className="pt-4 border-t border-gray-200">
                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
                  {total > 0 && (
                    <>
                      <div 
                        className="bg-green-500 transition-all"
                        style={{ width: `${(aspect.positive / total) * 100}%` }}
                      />
                      <div 
                        className="bg-red-500 transition-all"
                        style={{ width: `${(aspect.negative / total) * 100}%` }}
                      />
                      <div 
                        className="bg-gray-400 transition-all"
                        style={{ width: `${(aspect.neutral / total) * 100}%` }}
                      />
                    </>
                  )}
                </div>
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Positive: {total > 0 ? Math.round((aspect.positive / total) * 100) : 0}%</span>
                  <span>Negative: {total > 0 ? Math.round((aspect.negative / total) * 100) : 0}%</span>
                  <span>Neutral: {total > 0 ? Math.round((aspect.neutral / total) * 100) : 0}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
