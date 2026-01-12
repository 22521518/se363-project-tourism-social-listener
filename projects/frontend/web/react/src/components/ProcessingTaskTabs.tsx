import { ProcessingTask, TASK_LABELS, TASK_COLORS } from "../types/raw_data";
import {
  BarChart3,
  Target,
  MapPin,
  Plane,
  LayoutDashboard,
} from "lucide-react";

export type TabType = "summary" | ProcessingTask;

interface ProcessingTaskTabsProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  processedCounts?: {
    asca: number;
    intention: number;
    location_extraction: number;
    traveling_type: number;
  };
}

const TAB_ICONS: Record<TabType, React.ReactNode> = {
  summary: <LayoutDashboard className="w-4 h-4" />,
  asca: <BarChart3 className="w-4 h-4" />,
  intention: <Target className="w-4 h-4" />,
  location_extraction: <MapPin className="w-4 h-4" />,
  traveling_type: <Plane className="w-4 h-4" />,
};

const ALL_TABS: TabType[] = [
  "summary",
  "asca",
  "intention",
  "location_extraction",
  "traveling_type",
];

/**
 * Tab navigation component for processing tasks
 */
export function ProcessingTaskTabs({
  activeTab,
  onTabChange,
  processedCounts,
}: ProcessingTaskTabsProps) {
  return (
    <div className="bg-white rounded shadow-sm border border-gray-200 p-2 flex flex-wrap">
      {ALL_TABS.map((tab) => {
        const isActive = activeTab === tab;
        const label =
          tab === "summary" ? "Summary" : TASK_LABELS[tab as ProcessingTask];
        const color =
          tab === "summary" ? "#6366f1" : TASK_COLORS[tab as ProcessingTask];
        const count =
          tab !== "summary" && processedCounts
            ? processedCounts[tab as ProcessingTask]
            : undefined;

        return (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`
                flex items-center gap-2 px-4 py-3 text-sm  transition-colors px-2 py-1 rounded
             
              `}
            style={{
              fontWeight: 550,
              flex: "1 1 auto",
              color: isActive ? color : "#6b7280",
              borderColor: isActive ? color : undefined,
              background: isActive ? color + "20" : undefined,
            }}
          >
            {TAB_ICONS[tab]}
            <span>{label}</span>
            {count !== undefined && (
              <span
                className="px-1.5 py-0.5 text-xs rounded-full"
                style={{
                  backgroundColor: `${color}20`,
                  color: color,
                }}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
