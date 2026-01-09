import { Radio, BarChart3, FileText, Route } from "lucide-react";
import { Link, useLocation } from "react-router";

export function Header() {
  const { pathname } = useLocation();
  const tabs = [
    { id: "dashboard" as const, label: "Overview", icon: BarChart3 },
    { id: "posts" as const, label: "Posts Analysis", icon: FileText },
    // { id: 'itinerary' as const, label: 'Itinerary Tracker', icon: Route }
  ];

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Radio className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-gray-900">Tourism Social Listener</h1>
              <p className="text-sm text-gray-500">
                Advanced tracking & analysis
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <Link key={tab.id} to={`/${tab.id}`}>
                  <button
                    
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      pathname === `/${tab.id}`
                        ? "bg-blue-600 text-white"
                        : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden sm:inline">{tab.label}</span>
                  </button>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
}
