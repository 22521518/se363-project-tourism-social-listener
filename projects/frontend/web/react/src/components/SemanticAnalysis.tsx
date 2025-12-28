import { Brain, ThumbsUp, ThumbsDown, DollarSign, MapPin, Utensils, Hotel, Plane } from 'lucide-react';

interface SemanticAnalysisProps {
  filters: any;
}

export function SemanticAnalysis({ filters }: SemanticAnalysisProps) {
  const aspects = [
    {
      aspect: 'Location/Destination',
      icon: MapPin,
      positive: 6842,
      negative: 423,
      sentiment: 94,
      topMentions: ['Beautiful scenery', 'Great location', 'Convenient access'],
      color: 'blue'
    },
    {
      aspect: 'Price/Value',
      icon: DollarSign,
      positive: 4521,
      negative: 1834,
      sentiment: 71,
      topMentions: ['Good value', 'Affordable', 'Expensive'],
      color: 'green'
    },
    {
      aspect: 'Accommodation',
      icon: Hotel,
      positive: 5234,
      negative: 987,
      sentiment: 84,
      topMentions: ['Clean rooms', 'Comfortable beds', 'Great facilities'],
      color: 'purple'
    },
    {
      aspect: 'Food/Dining',
      icon: Utensils,
      positive: 4876,
      negative: 1245,
      sentiment: 80,
      topMentions: ['Delicious food', 'Variety options', 'Local cuisine'],
      color: 'orange'
    },
    {
      aspect: 'Transportation',
      icon: Plane,
      positive: 3421,
      negative: 1678,
      sentiment: 67,
      topMentions: ['Easy access', 'Delayed flights', 'Good connections'],
      color: 'indigo'
    }
  ];

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
    indigo: 'bg-indigo-100 text-indigo-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
      <div className="flex items-center gap-2 mb-6">
        <Brain className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Semantic Analysis by Aspects</h2>
          <p className="text-sm text-gray-600">Detailed breakdown of mentions by topic</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {aspects.map((aspect) => {
          const Icon = aspect.icon;
          const total = aspect.positive + aspect.negative;
          
          return (
            <div key={aspect.aspect} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4 mb-4">
                <div className={`p-3 rounded-lg ${colorClasses[aspect.color as keyof typeof colorClasses]}`}>
                  <Icon className="w-6 h-6" />
                </div>
                
                <div className="flex-1">
                  <h3 className="text-gray-900 mb-1">{aspect.aspect}</h3>
                  <p className="text-sm text-gray-600">{total.toLocaleString()} mentions</p>
                </div>
                
                <div className="text-right">
                  <div className={`text-sm px-3 py-1 rounded-full ${
                    aspect.sentiment >= 80 ? 'bg-green-100 text-green-700' :
                    aspect.sentiment >= 60 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {aspect.sentiment}% positive
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Positive</p>
                    <p className="text-green-600">{aspect.positive.toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <ThumbsDown className="w-4 h-4 text-red-600" />
                  <div>
                    <p className="text-sm text-gray-600">Negative</p>
                    <p className="text-red-600">{aspect.negative.toLocaleString()}</p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-600 mb-2">Top Mentions:</p>
                <div className="flex flex-wrap gap-2">
                  {aspect.topMentions.map((mention) => (
                    <span 
                      key={mention} 
                      className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                    >
                      {mention}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
