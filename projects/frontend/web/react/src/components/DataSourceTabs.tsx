import { Youtube, Globe } from "lucide-react";

export type DataSourceType = "youtube" | "webcrawl";

interface DataSourceTabsProps {
  activeSource: DataSourceType;
  onSourceChange: (source: DataSourceType) => void;
}

/**
 * Tab navigation component to switch between YouTube and Web Crawl data sources.
 */
export function DataSourceTabs({
  activeSource,
  onSourceChange,
}: DataSourceTabsProps) {
  const tabs = [
    {
      id: "youtube" as DataSourceType,
      label: "YouTube Data",
      icon: Youtube,
      description: "Videos, Comments & Channels",
    },
    {
      id: "webcrawl" as DataSourceType,
      label: "Web Crawl Data",
      icon: Globe,
      description: "Reviews, Blogs & Forums",
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-2">
      <div className="flex gap-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSource === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onSourceChange(tab.id)}
              className={`
                flex-1 flex items-center gap-3 rounded transition-all
                ${
                  isActive
                    ? "bg-blue-50 border-2 border-blue-500 text-blue-700"
                    : "bg-gray-50 border-2 border-transparent text-gray-600 hover:bg-gray-100"
                }
              `}
              style={{
                padding: 8,
              }}
            >
              <Icon
                className={`w-5 h-5 ${
                  isActive ? "text-blue-600" : "text-gray-500"
                }`}
              />
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems:'start'
                }}
              >
                <p
                  className={`font-medium ${
                    isActive ? "text-blue-700" : "text-gray-700"
                  }`}
                  style={{
                    fontWeight: 600,
                  }}
                >
                  {tab.label}
                </p>
                <p className="text-xs text-gray-500">{tab.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
