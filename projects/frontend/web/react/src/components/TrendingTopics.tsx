import { TrendingUp, Hash } from 'lucide-react';

interface TrendingTopicsProps {
  platform: string;
}

export function TrendingTopics({ platform }: TrendingTopicsProps) {
  const topics = [
    { hashtag: '#SustainableTourism', mentions: 8542, change: 24 },
    { hashtag: '#BeachVacation', mentions: 7231, change: 18 },
    { hashtag: '#TravelDeals', mentions: 6890, change: -5 },
    { hashtag: '#AdventureTravel', mentions: 5467, change: 32 },
    { hashtag: '#LuxuryResorts', mentions: 4821, change: 15 },
    { hashtag: '#FamilyTravel', mentions: 4102, change: 8 },
    { hashtag: '#CulturalTourism', mentions: 3756, change: 21 },
    { hashtag: '#EcoTourism', mentions: 3289, change: 45 }
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp className="w-5 h-5 text-gray-600" />
        <div>
          <h2 className="text-gray-900">Trending Topics</h2>
          <p className="text-sm text-gray-600">Most mentioned hashtags & keywords</p>
        </div>
      </div>
      
      <div className="space-y-3">
        {topics.map((topic, index) => (
          <div key={topic.hashtag} className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors">
            <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded text-sm text-gray-600">
              {index + 1}
            </div>
            
            <Hash className="w-4 h-4 text-blue-600" />
            
            <div className="flex-1 min-w-0">
              <p className="text-gray-900 truncate">{topic.hashtag}</p>
              <p className="text-sm text-gray-500">{topic.mentions.toLocaleString()} mentions</p>
            </div>
            
            <div className={`text-sm px-2 py-1 rounded ${
              topic.change > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {topic.change > 0 ? '+' : ''}{topic.change}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
