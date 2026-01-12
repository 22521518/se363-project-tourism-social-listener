import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Loader2, Target } from 'lucide-react';
import { fetchApi } from '../services/api';
import { IntentionStats } from '../types/intention';

interface IntentionChartProps {
  videoId: string;
}

export function IntentionChart({ videoId }: IntentionChartProps) {
  const [data, setData] = useState<IntentionStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const stats = await fetchApi<IntentionStats[]>(`/intentions/stats/video/${videoId}`);
        setData(stats.filter(item => item.value > 0)); // Only show categories with data
      } catch (err) {
        console.error('Error fetching intention stats:', err);
        setError('Failed to load intention data');
      } finally {
        setLoading(false);
      }
    };

    if (videoId) {
      fetchData();
    }
  }, [videoId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex justify-center items-center h-[300px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex justify-center items-center h-[300px] text-red-500">
        {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex justify-center items-center h-[300px] text-gray-500">
        No intention data available
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6 flex items-center gap-2">
        <Target className="w-5 h-5 text-purple-600" />
        <div>
          <h2 className="text-gray-900 font-semibold">User Intentions</h2>
          <p className="text-sm text-gray-600">Distribution of user intentions in comments</p>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" />
          <YAxis 
            dataKey="name" 
            type="category" 
            width={80}
            tick={{ fontSize: 11 }}
          />
          <Tooltip 
            cursor={{ fill: 'transparent' }}
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || '#8884d8'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
