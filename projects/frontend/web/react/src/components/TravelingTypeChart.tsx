import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Loader2, Plane } from 'lucide-react';
import { fetchApi } from '../services/api';
import { TravelingTypeStats } from '../types/traveling-type';

interface TravelingTypeChartProps {
  videoId: string;
}

export function TravelingTypeChart({ videoId }: TravelingTypeChartProps) {
  const [data, setData] = useState<TravelingTypeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const stats = await fetchApi<TravelingTypeStats[]>(`/traveling_types/stats/video/${videoId}`);
        setData(stats.filter(item => item.value > 0)); // Only show categories with data
      } catch (err) {
        console.error('Error fetching traveling type stats:', err);
        setError('Failed to load traveling type data');
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
        No traveling type data available
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6 flex items-center gap-2">
        <Plane className="w-5 h-5 text-amber-600" />
        <div>
          <h2 className="text-gray-900 font-semibold">Traveling Types</h2>
          <p className="text-sm text-gray-600">Traveler categories identified</p>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color || '#8884d8'} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
          />
          <Legend 
            layout="vertical" 
            verticalAlign="middle" 
            align="right"
            wrapperStyle={{ fontSize: '12px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
