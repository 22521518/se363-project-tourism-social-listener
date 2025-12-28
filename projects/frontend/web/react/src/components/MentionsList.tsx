import { Twitter, Instagram, Facebook, MapPin, Heart, MessageCircle, Share2 } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface MentionsListProps {
  platform: string;
  sentiment: string;
}

export function MentionsList({ platform, sentiment }: MentionsListProps) {
  const mentions = [
    {
      id: 1,
      platform: 'twitter',
      author: 'Sarah Johnson',
      username: '@sarahtravels',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      content: 'Just had the most amazing experience at the Grand Canyon! The sunset views were absolutely breathtaking. Highly recommend! 🌅',
      sentiment: 'positive',
      timestamp: '2 hours ago',
      location: 'Arizona, USA',
      likes: 234,
      comments: 45,
      shares: 23
    },
    {
      id: 2,
      platform: 'instagram',
      author: 'Travel Explorer',
      username: '@travelexplorer',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      content: 'Beach vacation goals achieved! Crystal clear waters and pristine beaches. This resort is a hidden gem! 🏖️ #BeachVacation',
      sentiment: 'positive',
      timestamp: '4 hours ago',
      location: 'Maldives',
      likes: 1823,
      comments: 156,
      shares: 89
    },
    {
      id: 3,
      platform: 'facebook',
      author: 'Mike Anderson',
      username: 'mike.anderson',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop',
      content: 'The customer service at this hotel needs improvement. Long wait times and unresponsive staff. Expected better.',
      sentiment: 'negative',
      timestamp: '6 hours ago',
      location: 'Paris, France',
      likes: 45,
      comments: 23,
      shares: 5
    },
    {
      id: 4,
      platform: 'twitter',
      author: 'Adventure Seeker',
      username: '@adventurepro',
      avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=100&h=100&fit=crop',
      content: 'Completed the most thrilling mountain trek today! The guides were professional and the views were incredible.',
      sentiment: 'positive',
      timestamp: '8 hours ago',
      location: 'Nepal',
      likes: 567,
      comments: 78,
      shares: 34
    },
    {
      id: 5,
      platform: 'instagram',
      author: 'Emily Davis',
      username: '@emilywanders',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop',
      content: 'Cultural immersion at its finest! Visited local markets and tried authentic cuisine. This trip exceeded expectations.',
      sentiment: 'positive',
      timestamp: '12 hours ago',
      location: 'Bangkok, Thailand',
      likes: 923,
      comments: 102,
      shares: 56
    }
  ];

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'twitter': return Twitter;
      case 'instagram': return Instagram;
      case 'facebook': return Facebook;
      default: return MessageCircle;
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'twitter': return 'text-blue-500';
      case 'instagram': return 'text-pink-500';
      case 'facebook': return 'text-blue-600';
      default: return 'text-gray-500';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'bg-green-100 text-green-700';
      case 'negative': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-6">
        <h2 className="text-gray-900 mb-1">Recent Mentions</h2>
        <p className="text-sm text-gray-600">Latest social media conversations</p>
      </div>
      
      <div className="space-y-4">
        {mentions.map((mention) => {
          const PlatformIcon = getPlatformIcon(mention.platform);
          
          return (
            <div key={mention.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3 mb-3">
                <ImageWithFallback
                  src={mention.avatar}
                  alt={mention.author}
                  className="w-12 h-12 rounded-full object-cover"
                />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-gray-900">{mention.author}</p>
                    <span className="text-sm text-gray-500">{mention.username}</span>
                    <PlatformIcon className={`w-4 h-4 ${getPlatformColor(mention.platform)}`} />
                  </div>
                  
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <MapPin className="w-3 h-3" />
                    <span>{mention.location}</span>
                    <span>•</span>
                    <span>{mention.timestamp}</span>
                  </div>
                </div>
                
                <span className={`text-xs px-2 py-1 rounded ${getSentimentColor(mention.sentiment)}`}>
                  {mention.sentiment}
                </span>
              </div>
              
              <p className="text-gray-700 mb-3">{mention.content}</p>
              
              <div className="flex items-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Heart className="w-4 h-4" />
                  <span>{mention.likes}</span>
                </div>
                <div className="flex items-center gap-1">
                  <MessageCircle className="w-4 h-4" />
                  <span>{mention.comments}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Share2 className="w-4 h-4" />
                  <span>{mention.shares}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
