import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Compass, Loader2 } from 'lucide-react';
import { useGeographyData } from '../hooks/useGeographyData';

interface TourismClassificationProps {
  filters: any;
}

export function TourismClassification({ filters }: TourismClassificationProps) {
  // Fetch geography data from API
  const { data: geoData, loading: geoLoading, error: geoError } = useGeographyData();

  const purposeData = [
    { name: 'Leisure/Vacation', value: 4200, color: '#3b82f6' },
    { name: 'Adventure', value: 2800, color: '#10b981' },
    { name: 'Cultural', value: 2100, color: '#f59e0b' },
    { name: 'Business', value: 1800, color: '#6366f1' },
    { name: 'Eco-Tourism', value: 1600, color: '#14b8a6' },
    { name: 'Wellness', value: 1200, color: '#ec4899' }
  ];

  const orgData = [
    { name: 'Individual/Solo', value: 3500, color: '#8b5cf6' },
    { name: 'Family', value: 3200, color: '#3b82f6' },
    { name: 'Couple', value: 2800, color: '#ec4899' },
    { name: 'Package Tour', value: 2400, color: '#f59e0b' },
    { name: 'Group', value: 1900, color: '#10b981' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Compass className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Tourism Classification</h2>
          <p className="text-sm text-gray-600">Distribution by categories</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* By Purpose */}
        <div>
          <h3 className="text-sm text-gray-700 mb-3">By Purpose</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={purposeData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {purposeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {purposeData.map((item) => (
              <div key={item.name} className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }}></div>
                <span className="text-gray-600">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* By Organization */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm text-gray-700 mb-2">By Organization</h3>
          <div className="space-y-2">
            {orgData.map((item) => (
              <div key={item.name} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{item.name}</span>
                  <span className="text-gray-600">{item.value}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all"
                    style={{ 
                      width: `${(item.value / Math.max(...orgData.map(d => d.value))) * 100}%`,
                      backgroundColor: item.color
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* By Geography */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm text-gray-700 mb-1">By Geography</h3>
          <p className="text-xs text-gray-500 mb-3">Origin: Vietnam</p>
          <div className="space-y-3">
            {geoLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                <span className="ml-2 text-sm text-gray-500">Loading...</span>
              </div>
            ) : geoError ? (
              <div className="text-sm text-red-500 py-2">{geoError}</div>
            ) : geoData.length === 0 ? (
              <div className="text-sm text-gray-500 py-2">No geography data available</div>
            ) : (
              geoData.map((item) => (
                <div key={item.name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-700 font-medium">{item.name}</span>
                      <span className="text-xs text-gray-400">
                        {item.name === 'Domestic' && '(Vietnam)'}
                        {item.name === 'Regional' && '(South East Asia)'}
                        {item.name === 'International' && '(World)'}
                      </span>
                    </div>
                    <span className="text-gray-600 font-semibold">{item.value.toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{ 
                        width: `${(item.value / Math.max(...geoData.map(d => d.value), 1)) * 100}%`,
                        backgroundColor: item.color
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
