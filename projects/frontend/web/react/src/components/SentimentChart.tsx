import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface SentimentChartProps {
  timeRange: string;
}

export function SentimentChart({ timeRange }: SentimentChartProps) {
  const data = [
    { date: 'Nov 24', positive: 420, neutral: 180, negative: 80 },
    { date: 'Nov 25', positive: 380, neutral: 220, negative: 95 },
    { date: 'Nov 26', positive: 510, neutral: 190, negative: 70 },
    { date: 'Nov 27', positive: 460, neutral: 210, negative: 85 },
    { date: 'Nov 28', positive: 580, neutral: 170, negative: 60 },
    { date: 'Nov 29', positive: 520, neutral: 200, negative: 75 },
    { date: 'Nov 30', positive: 650, neutral: 160, negative: 55 }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6">
        <h2 className="text-gray-900 mb-1">Sentiment Analysis</h2>
        <p className="text-sm text-gray-600">Mentions over time by sentiment</p>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="positive" 
            stackId="1"
            stroke="#10b981" 
            fill="#10b981"
            fillOpacity={0.6}
          />
          <Area 
            type="monotone" 
            dataKey="neutral" 
            stackId="1"
            stroke="#6b7280" 
            fill="#6b7280"
            fillOpacity={0.6}
          />
          <Area 
            type="monotone" 
            dataKey="negative" 
            stackId="1"
            stroke="#ef4444" 
            fill="#ef4444"
            fillOpacity={0.6}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
