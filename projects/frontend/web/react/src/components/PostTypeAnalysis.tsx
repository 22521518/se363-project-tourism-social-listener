import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { FileText } from 'lucide-react';

interface PostTypeAnalysisProps {
  filters: any;
}

export function PostTypeAnalysis({ filters }: PostTypeAnalysisProps) {
  const data = [
    {
      type: 'User Review',
      mentions: 6800,
      interactions: 45200,
      avgSentiment: 78
    },
    {
      type: 'Travel Inquiry',
      mentions: 4200,
      interactions: 28400,
      avgSentiment: 65
    },
    {
      type: 'Agency Question',
      mentions: 3800,
      interactions: 31200,
      avgSentiment: 62
    },
    {
      type: 'Influencer Post',
      mentions: 2100,
      interactions: 89600,
      avgSentiment: 85
    },
    {
      type: 'Itinerary Share',
      mentions: 1500,
      interactions: 12800,
      avgSentiment: 72
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <FileText className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Post Type Analysis</h2>
          <p className="text-sm text-gray-600">Volume & engagement by post type</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="type" 
            tick={{ fontSize: 11 }}
            angle={-15}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Bar dataKey="mentions" fill="#3b82f6" name="Mentions" />
          <Bar dataKey="interactions" fill="#10b981" name="Interactions (÷100)" />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm text-gray-700 mb-3">Average Sentiment by Type</h3>
        <div className="space-y-2">
          {data.map((item) => (
            <div key={item.type} className="flex items-center gap-3">
              <span className="text-sm text-gray-700 w-32 truncate">{item.type}</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    item.avgSentiment >= 75 ? 'bg-green-500' :
                    item.avgSentiment >= 60 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${item.avgSentiment}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 w-12 text-right">{item.avgSentiment}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
