import { useState } from 'react';
import { MessageCircle, Heart, Share2, Eye, ChevronDown, ChevronUp, MapPin, Tag, Users } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface DetailedMentionsProps {
  filters: any;
}

export function DetailedMentions({ filters }: DetailedMentionsProps) {
  const [expandedPost, setExpandedPost] = useState<number | null>(null);

  const posts = [
    {
      id: 1,
      type: 'user-review',
      author: 'Sarah Johnson',
      username: '@sarahtravels',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      timestamp: '2 hours ago',
      platform: 'Instagram',
      
      // Main post content
      content: 'Just completed an amazing 5-day adventure tour in Bali! 🌴 The combination of culture, nature, and relaxation was perfect. Highly recommend for families!',
      videoTranscript: 'Hi everyone! Just wrapped up our Bali trip. Day 1 we visited Ubud rice terraces - absolutely stunning. The guide was knowledgeable...',
      
      // Classifications
      tourismPurpose: 'Adventure',
      tourismOrg: 'Family',
      tourismGeo: 'International',
      location: 'Bali, Indonesia',
      
      // Semantic aspects
      aspects: {
        destination: { sentiment: 'positive', score: 95 },
        price: { sentiment: 'positive', score: 85 },
        accommodation: { sentiment: 'positive', score: 90 },
        food: { sentiment: 'positive', score: 88 },
        transportation: { sentiment: 'neutral', score: 70 }
      },
      
      // Extracted data
      extractedInfo: {
        desiredLocation: 'Bali, Indonesia',
        transportation: 'Flight + Private car',
        priceRange: '$2,500-3,000 per person',
        services: ['Guided tours', 'Hotel pickup', 'Meals included']
      },
      
      // Metrics
      volume: {
        mentions: 1,
        reactions: 1823,
        comments: 156,
        shares: 89,
        views: 28400
      },
      totalInteractions: 2068,
      sentiment: 'positive',
      
      // Comments
      comments: [
        {
          author: 'Emma Wilson',
          content: 'This looks amazing! How much did the whole trip cost?',
          sentiment: 'neutral',
          timestamp: '1 hour ago'
        },
        {
          author: 'Travel Agency Pro',
          content: 'We offer similar packages! DM for details 📩',
          sentiment: 'neutral',
          timestamp: '45 min ago'
        },
        {
          author: 'Mike Chen',
          content: 'Beautiful! Adding to my bucket list',
          sentiment: 'positive',
          timestamp: '30 min ago'
        }
      ]
    },
    {
      id: 2,
      type: 'agency-question',
      author: 'TravelDeals Asia',
      username: '@traveldeals_asia',
      avatar: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&h=100&fit=crop',
      timestamp: '5 hours ago',
      platform: 'Facebook',
      
      content: 'Looking for a romantic beach getaway for couples in Southeast Asia. Budget: $1,500-2,000. Prefer all-inclusive resorts. Any recommendations? 🏖️',
      
      tourismPurpose: 'Leisure',
      tourismOrg: 'Couple',
      tourismGeo: 'Regional',
      location: 'Southeast Asia',
      
      aspects: {
        destination: { sentiment: 'neutral', score: 50 },
        price: { sentiment: 'neutral', score: 50 },
        accommodation: { sentiment: 'neutral', score: 50 }
      },
      
      extractedInfo: {
        desiredLocation: 'Southeast Asia (Beach)',
        transportation: 'Not specified',
        priceRange: '$1,500-2,000',
        services: ['All-inclusive resort', 'Romantic setting']
      },
      
      volume: {
        mentions: 1,
        reactions: 234,
        comments: 67,
        shares: 12,
        views: 8900
      },
      totalInteractions: 313,
      sentiment: 'neutral',
      
      comments: [
        {
          author: 'Resort Expert',
          content: 'Check out Phuket or Koh Samui in Thailand. Perfect for couples!',
          sentiment: 'positive',
          timestamp: '4 hours ago'
        },
        {
          author: 'Maria Santos',
          content: 'El Nido in Philippines is amazing and within your budget',
          sentiment: 'positive',
          timestamp: '3 hours ago'
        }
      ]
    },
    {
      id: 3,
      type: 'influencer',
      author: 'Alex Rivers',
      username: '@alexrivers',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      timestamp: '1 day ago',
      platform: 'TikTok',
      
      content: 'Top 5 sustainable eco-resorts in Costa Rica 🌿 These places are changing the tourism game! Swipe to see my favorites.',
      videoTranscript: 'Number 5: Lapa Rios Lodge - This place is nestled in the rainforest... Number 4: Pacuare Lodge...',
      
      tourismPurpose: 'Eco',
      tourismOrg: 'Individual',
      tourismGeo: 'International',
      location: 'Costa Rica',
      
      aspects: {
        destination: { sentiment: 'positive', score: 98 },
        accommodation: { sentiment: 'positive', score: 95 },
        price: { sentiment: 'neutral', score: 65 }
      },
      
      extractedInfo: {
        desiredLocation: 'Costa Rica',
        transportation: 'Various',
        priceRange: 'Mid to high-end',
        services: ['Eco-tours', 'Sustainable practices', 'Nature activities']
      },
      
      volume: {
        mentions: 1,
        reactions: 45600,
        comments: 2340,
        shares: 8900,
        views: 567000
      },
      totalInteractions: 56840,
      sentiment: 'positive',
      
      comments: [
        {
          author: 'EcoWarrior',
          content: 'Finally someone promoting sustainable tourism! 🙌',
          sentiment: 'positive',
          timestamp: '20 hours ago'
        },
        {
          author: 'Budget Traveler',
          content: 'These look expensive though... any budget alternatives?',
          sentiment: 'negative',
          timestamp: '18 hours ago'
        }
      ]
    }
  ];

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'user-review': 'User Review',
      'agency-question': 'Travel Agency',
      'influencer': 'Influencer',
      'inquiry': 'Travel Inquiry',
      'itinerary': 'Itinerary'
    };
    return labels[type] || type;
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'user-review': 'bg-blue-100 text-blue-700',
      'agency-question': 'bg-purple-100 text-purple-700',
      'influencer': 'bg-pink-100 text-pink-700',
      'inquiry': 'bg-green-100 text-green-700',
      'itinerary': 'bg-orange-100 text-orange-700'
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  const getSentimentColor = (sentiment: string) => {
    const colors: Record<string, string> = {
      'positive': 'bg-green-100 text-green-700',
      'negative': 'bg-red-100 text-red-700',
      'neutral': 'bg-gray-100 text-gray-700'
    };
    return colors[sentiment] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-gray-900">Detailed Post Analysis</h2>
            <p className="text-sm text-gray-600">{posts.length} posts tracked with full semantic analysis</p>
          </div>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Export Data
          </button>
        </div>
      </div>

      {posts.map((post) => (
        <div key={post.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {/* Post Header */}
          <div className="flex items-start gap-4 mb-4">
            <ImageWithFallback
              src={post.avatar}
              alt={post.author}
              className="w-12 h-12 rounded-full object-cover"
            />
            
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-gray-900">{post.author}</p>
                <span className="text-sm text-gray-500">{post.username}</span>
                <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">{post.platform}</span>
              </div>
              
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <MapPin className="w-3 h-3" />
                <span>{post.location}</span>
                <span>•</span>
                <span>{post.timestamp}</span>
              </div>
            </div>
            
            <div className="flex gap-2">
              <span className={`text-xs px-2 py-1 rounded ${getTypeColor(post.type)}`}>
                {getTypeLabel(post.type)}
              </span>
              <span className={`text-xs px-2 py-1 rounded ${getSentimentColor(post.sentiment)}`}>
                {post.sentiment}
              </span>
            </div>
          </div>

          {/* Main Content */}
          <p className="text-gray-700 mb-4">{post.content}</p>

          {/* Classifications */}
          <div className="flex flex-wrap gap-2 mb-4 pb-4 border-b border-gray-200">
            <div className="flex items-center gap-1 text-sm bg-blue-50 text-blue-700 px-3 py-1 rounded-full">
              <Tag className="w-3 h-3" />
              <span>{post.tourismPurpose}</span>
            </div>
            <div className="flex items-center gap-1 text-sm bg-purple-50 text-purple-700 px-3 py-1 rounded-full">
              <Users className="w-3 h-3" />
              <span>{post.tourismOrg}</span>
            </div>
            <div className="flex items-center gap-1 text-sm bg-green-50 text-green-700 px-3 py-1 rounded-full">
              <MapPin className="w-3 h-3" />
              <span>{post.tourismGeo}</span>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Reactions</p>
              <p className="text-gray-900">{post.volume.reactions.toLocaleString()}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Comments</p>
              <p className="text-gray-900">{post.volume.comments.toLocaleString()}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Shares</p>
              <p className="text-gray-900">{post.volume.shares.toLocaleString()}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Views</p>
              <p className="text-gray-900">{post.volume.views.toLocaleString()}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Interactions</p>
              <p className="text-gray-900">{post.totalInteractions.toLocaleString()}</p>
            </div>
          </div>

          {/* Expand/Collapse */}
          <button
            onClick={() => setExpandedPost(expandedPost === post.id ? null : post.id)}
            className="w-full flex items-center justify-center gap-2 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <span>
              {expandedPost === post.id ? 'Hide' : 'Show'} detailed analysis
            </span>
            {expandedPost === post.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {/* Expanded Content */}
          {expandedPost === post.id && (
            <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
              {/* Extracted Information */}
              <div>
                <h3 className="text-sm text-gray-900 mb-3">Extracted Information</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 bg-gray-50 p-4 rounded-lg">
                  <div>
                    <p className="text-xs text-gray-600">Desired Location</p>
                    <p className="text-sm text-gray-900">{post.extractedInfo.desiredLocation}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Transportation</p>
                    <p className="text-sm text-gray-900">{post.extractedInfo.transportation}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Price Range</p>
                    <p className="text-sm text-gray-900">{post.extractedInfo.priceRange}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Services</p>
                    <p className="text-sm text-gray-900">{post.extractedInfo.services.join(', ')}</p>
                  </div>
                </div>
              </div>

              {/* Semantic Aspects */}
              <div>
                <h3 className="text-sm text-gray-900 mb-3">Semantic Analysis by Aspects</h3>
                <div className="space-y-2">
                  {Object.entries(post.aspects).map(([aspect, data]) => (
                    <div key={aspect} className="flex items-center gap-3">
                      <span className="text-sm text-gray-700 w-32 capitalize">{aspect}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            data.sentiment === 'positive' ? 'bg-green-500' :
                            data.sentiment === 'negative' ? 'bg-red-500' :
                            'bg-gray-400'
                          }`}
                          style={{ width: `${data.score}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 w-20 text-right">
                        {data.score}% {data.sentiment}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Comments */}
              <div>
                <h3 className="text-sm text-gray-900 mb-3">Comments ({post.comments.length})</h3>
                <div className="space-y-3">
                  {post.comments.map((comment, idx) => (
                    <div key={idx} className="bg-gray-50 p-3 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-gray-900">{comment.author}</p>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded ${getSentimentColor(comment.sentiment)}`}>
                            {comment.sentiment}
                          </span>
                          <span className="text-xs text-gray-500">{comment.timestamp}</span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700">{comment.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
