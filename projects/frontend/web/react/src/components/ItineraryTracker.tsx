import { Route, MapPin, Calendar, DollarSign, Users, Star } from 'lucide-react';

interface ItineraryTrackerProps {
  filters: any;
}

export function ItineraryTracker({ filters }: ItineraryTrackerProps) {
  const itineraries = [
    {
      id: 1,
      title: '7-Day Bali Adventure',
      author: 'Sarah Johnson',
      destination: 'Bali, Indonesia',
      duration: '7 days',
      budget: '$2,500-3,000',
      travelers: 'Family (4 people)',
      sentiment: 'positive',
      mentions: 234,
      saves: 1890,
      
      days: [
        {
          day: 1,
          title: 'Arrival & Ubud',
          activities: ['Airport pickup', 'Check-in hotel', 'Ubud Rice Terraces', 'Monkey Forest'],
          accommodation: 'Ubud Luxury Resort',
          meals: ['Breakfast included', 'Lunch at local restaurant', 'Dinner at hotel'],
          cost: '$350'
        },
        {
          day: 2,
          title: 'Cultural Tour',
          activities: ['Tirta Empul Temple', 'Coffee plantation', 'Traditional dance show'],
          accommodation: 'Ubud Luxury Resort',
          meals: ['Breakfast included', 'Lunch at plantation', 'Traditional Balinese dinner'],
          cost: '$280'
        },
        {
          day: 3,
          title: 'Beach Day',
          activities: ['Transfer to Seminyak', 'Beach time', 'Sunset at Tanah Lot Temple'],
          accommodation: 'Seminyak Beach Resort',
          meals: ['Breakfast included', 'Beachside lunch', 'Seafood dinner'],
          cost: '$320'
        }
      ],
      
      highlights: ['Family-friendly', 'Cultural immersion', 'Beach relaxation', 'All transfers included'],
      topAspects: {
        location: 95,
        value: 85,
        activities: 92,
        accommodation: 88
      }
    },
    {
      id: 2,
      title: '5-Day Thailand Beach Escape',
      author: 'Mike & Lisa',
      destination: 'Phuket, Thailand',
      duration: '5 days',
      budget: '$1,800-2,200',
      travelers: 'Couple',
      sentiment: 'positive',
      mentions: 156,
      saves: 1234,
      
      days: [
        {
          day: 1,
          title: 'Arrival & Resort',
          activities: ['Airport transfer', 'Resort check-in', 'Spa treatment', 'Beach sunset'],
          accommodation: 'Luxury Beach Resort',
          meals: ['Welcome drinks', 'Romantic dinner on beach'],
          cost: '$420'
        },
        {
          day: 2,
          title: 'Island Hopping',
          activities: ['Phi Phi Islands tour', 'Snorkeling', 'Maya Bay visit'],
          accommodation: 'Luxury Beach Resort',
          meals: ['Breakfast buffet', 'BBQ lunch on boat', 'Dinner at resort'],
          cost: '$280'
        }
      ],
      
      highlights: ['All-inclusive resort', 'Private tours', 'Couples spa', 'Island hopping'],
      topAspects: {
        location: 92,
        value: 78,
        activities: 88,
        accommodation: 95
      }
    }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Route className="w-5 h-5 text-blue-600" />
            <div>
              <h2 className="text-gray-900">Itinerary Tracker</h2>
              <p className="text-sm text-gray-600">Track popular travel itineraries shared by users</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Total tracked</p>
            <p className="text-gray-900">{itineraries.length} itineraries</p>
          </div>
        </div>
      </div>

      {itineraries.map((itinerary) => (
        <div key={itinerary.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl mb-2">{itinerary.title}</h3>
                <p className="text-blue-100">by {itinerary.author}</p>
              </div>
              <div className="flex gap-2">
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                  {itinerary.mentions} mentions
                </span>
                <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                  {itinerary.saves} saves
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                <div>
                  <p className="text-xs text-blue-100">Destination</p>
                  <p className="text-sm">{itinerary.destination}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <div>
                  <p className="text-xs text-blue-100">Duration</p>
                  <p className="text-sm">{itinerary.duration}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                <div>
                  <p className="text-xs text-blue-100">Budget</p>
                  <p className="text-sm">{itinerary.budget}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <div>
                  <p className="text-xs text-blue-100">Travelers</p>
                  <p className="text-sm">{itinerary.travelers}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Highlights */}
            <div className="mb-6">
              <h4 className="text-sm text-gray-900 mb-3">Highlights</h4>
              <div className="flex flex-wrap gap-2">
                {itinerary.highlights.map((highlight) => (
                  <span key={highlight} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
                    {highlight}
                  </span>
                ))}
              </div>
            </div>

            {/* Aspect Scores */}
            <div className="mb-6 pb-6 border-b border-gray-200">
              <h4 className="text-sm text-gray-900 mb-3">Sentiment by Aspect</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {Object.entries(itinerary.topAspects).map(([aspect, score]) => (
                  <div key={aspect} className="text-center">
                    <div className="mb-2">
                      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-green-400 to-green-600 text-white">
                        <span className="text-lg">{score}</span>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 capitalize">{aspect}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Day by Day */}
            <div>
              <h4 className="text-sm text-gray-900 mb-4">Day-by-Day Breakdown</h4>
              <div className="space-y-4">
                {itinerary.days.map((day) => (
                  <div key={day.day} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                            Day {day.day}
                          </span>
                          <h5 className="text-gray-900">{day.title}</h5>
                        </div>
                      </div>
                      <span className="text-sm text-gray-600">{day.cost}</span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-gray-600 mb-2">Activities</p>
                        <ul className="space-y-1">
                          {day.activities.map((activity, idx) => (
                            <li key={idx} className="text-gray-700 flex items-start gap-2">
                              <span className="text-blue-600 mt-1">•</span>
                              <span>{activity}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-600 mb-2">Accommodation</p>
                        <p className="text-gray-700">{day.accommodation}</p>
                      </div>
                      
                      <div>
                        <p className="text-xs text-gray-600 mb-2">Meals</p>
                        <ul className="space-y-1">
                          {day.meals.map((meal, idx) => (
                            <li key={idx} className="text-gray-700 text-xs">{meal}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
