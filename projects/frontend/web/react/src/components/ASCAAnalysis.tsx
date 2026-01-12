import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { Brain, Loader2, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';
import { useASCAData } from '../hooks/useASCAData';
import { CATEGORY_COLORS, CategoryType, SENTIMENT_COLORS } from '../types/asca';

interface ASCAAnalysisProps {
  videoId?: string;
}

/**
 * Component for displaying ASCA (Aspect-based Sentiment Category Analysis).
 * Shows sentiment breakdown by aspect categories.
 */
export function ASCAAnalysis({ videoId }: ASCAAnalysisProps) {
  const { data, loading, error } = useASCAData(videoId);

  // Prepare data for stacked bar chart
  const chartData = data.map((item) => ({
    name: item.category,
    positive: item.positive,
    negative: item.negative,
    neutral: item.neutral,
    total: item.total,
  }));

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

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading ASCA analysis...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-sm text-red-500 py-4 text-center">{error}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="w-5 h-5 text-blue-600" />
          <h2 className="text-gray-900">Aspect-based Sentiment Analysis</h2>
        </div>
        <div className="text-sm text-gray-500 py-4 text-center">
          No ASCA data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-6">
        <Brain className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Aspect-based Sentiment Analysis</h2>
          <p className="text-sm text-gray-600">
            Sentiment breakdown by tourism aspects
          </p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
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

      {/* Stacked Bar Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11 }}
            width={100}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar
            dataKey="positive"
            stackId="a"
            fill={SENTIMENT_COLORS.positive}
            name="Positive"
          />
          <Bar
            dataKey="negative"
            stackId="a"
            fill={SENTIMENT_COLORS.negative}
            name="Negative"
          />
          <Bar
            dataKey="neutral"
            stackId="a"
            fill={SENTIMENT_COLORS.neutral}
            name="Neutral"
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Aspect Cards */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">By Aspect Category</h3>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((item) => {
            const positivePercent = item.total > 0 
              ? Math.round((item.positive / item.total) * 100) 
              : 0;
            
            return (
              <div
                key={item.category}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="font-medium text-gray-900 text-sm">
                    {item.category}
                  </span>
                </div>
                
                <p className="text-xl font-semibold text-gray-800 mb-2">
                  {item.total.toLocaleString()}
                </p>
                
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-green-600">+{item.positive}</span>
                  <span className="text-red-600">-{item.negative}</span>
                  <span className="text-gray-500">~{item.neutral}</span>
                </div>
                
                {/* Sentiment bar */}
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="h-2 rounded-full bg-green-500 transition-all"
                    style={{ width: `${positivePercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {positivePercent}% positive
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
