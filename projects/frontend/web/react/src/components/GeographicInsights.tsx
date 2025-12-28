import { MapPin, Globe } from 'lucide-react';

export function GeographicInsights() {
  const locations = [
    { country: 'United States', mentions: 8945, percentage: 28, flag: '🇺🇸' },
    { country: 'United Kingdom', mentions: 6234, percentage: 19, flag: '🇬🇧' },
    { country: 'France', mentions: 4567, percentage: 14, flag: '🇫🇷' },
    { country: 'Italy', mentions: 3821, percentage: 12, flag: '🇮🇹' },
    { country: 'Spain', mentions: 3456, percentage: 11, flag: '🇪🇸' },
    { country: 'Japan', mentions: 2890, percentage: 9, flag: '🇯🇵' },
    { country: 'Thailand', mentions: 1234, percentage: 4, flag: '🇹🇭' },
    { country: 'Others', mentions: 1023, percentage: 3, flag: '🌍' }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Globe className="w-5 h-5 text-gray-600" />
        <div>
          <h2 className="text-gray-900">Geographic Insights</h2>
          <p className="text-sm text-gray-600">Mentions by location</p>
        </div>
      </div>
      
      <div className="space-y-4">
        {locations.map((location) => (
          <div key={location.country} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{location.flag}</span>
                <div>
                  <p className="text-sm text-gray-900">{location.country}</p>
                  <p className="text-xs text-gray-500">{location.mentions.toLocaleString()} mentions</p>
                </div>
              </div>
              <span className="text-sm text-gray-600">{location.percentage}%</span>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${location.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <MapPin className="w-4 h-4" />
          <span>Tracking mentions from 127 countries</span>
        </div>
      </div>
    </div>
  );
}
