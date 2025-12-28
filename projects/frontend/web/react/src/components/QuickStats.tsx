import { MessageCircle, Users, TrendingUp, Eye } from 'lucide-react';

interface QuickStatsProps {
  filters: any;
}

export function QuickStats({ filters }: QuickStatsProps) {
  const stats = [
    {
      label: 'Total Mentions',
      value: '18,432',
      subtext: 'Posts tracked',
      change: '+12.5%',
      icon: MessageCircle,
      color: 'blue'
    },
    {
      label: 'Total Interactions',
      value: '156.2K',
      subtext: 'Reactions + Comments',
      change: '+18.3%',
      icon: Users,
      color: 'purple'
    },
    {
      label: 'Avg Engagement',
      value: '8.4',
      subtext: 'Per post',
      change: '+5.2%',
      icon: TrendingUp,
      color: 'green'
    },
    {
      label: 'Total Reach',
      value: '2.4M',
      subtext: 'Unique views',
      change: '+22.1%',
      icon: Eye,
      color: 'orange'
    }
  ];

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600'
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div key={stat.label} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-3">
              <div className={`p-3 rounded-lg ${colorClasses[stat.color as keyof typeof colorClasses]}`}>
                <Icon className="w-6 h-6" />
              </div>
              <span className="text-sm text-green-600 bg-green-50 px-2 py-1 rounded">
                {stat.change}
              </span>
            </div>
            
            <p className="text-gray-900 mb-1">{stat.value}</p>
            <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
            <p className="text-xs text-gray-500">{stat.subtext}</p>
          </div>
        );
      })}
    </div>
  );
}
