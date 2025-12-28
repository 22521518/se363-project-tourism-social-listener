import { TrendingUp, MessageCircle, Users, Heart } from 'lucide-react';

interface MetricsOverviewProps {
  timeRange: string;
}

export function MetricsOverview({ timeRange }: MetricsOverviewProps) {
  const metrics = [
    {
      label: 'Total Mentions',
      value: '24,567',
      change: '+12.5%',
      trend: 'up',
      icon: MessageCircle,
      color: 'blue'
    },
    {
      label: 'Reach',
      value: '1.2M',
      change: '+8.3%',
      trend: 'up',
      icon: Users,
      color: 'purple'
    },
    {
      label: 'Engagement Rate',
      value: '4.8%',
      change: '+2.1%',
      trend: 'up',
      icon: Heart,
      color: 'pink'
    },
    {
      label: 'Sentiment Score',
      value: '78/100',
      change: '+5.2%',
      trend: 'up',
      icon: TrendingUp,
      color: 'green'
    }
  ];

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    purple: 'bg-purple-100 text-purple-600',
    pink: 'bg-pink-100 text-pink-600',
    green: 'bg-green-100 text-green-600'
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div key={metric.label} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm text-gray-600 mb-1">{metric.label}</p>
                <p className="text-gray-900 mb-2">{metric.value}</p>
                <div className="flex items-center gap-1">
                  <span className="text-sm text-green-600">{metric.change}</span>
                  <span className="text-xs text-gray-500">vs last period</span>
                </div>
              </div>
              <div className={`p-3 rounded-lg ${colorClasses[metric.color as keyof typeof colorClasses]}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
