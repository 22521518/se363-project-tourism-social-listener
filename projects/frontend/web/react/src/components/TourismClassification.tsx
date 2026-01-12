import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Compass, Loader2, ChevronRight, Globe } from "lucide-react";
import { useContinentData } from "../hooks/useLocationHierarchy";
import { useIntentionsData } from "../hooks/useIntentionData";
import { useTravelingTypeData } from "../hooks/useTravelingTypeData";
import { useNavigate } from "react-router";

interface TourismClassificationProps {
  filters: any;
  id?: string;
}

export function TourismClassification({
  filters,
  id,
}: TourismClassificationProps) {
  const navigate = useNavigate();
  
  // Fetch continent data from API
  const {
    data: continentData,
    total: continentTotal,
    loading: continentLoading,
    error: continentError,
  } = useContinentData();
  const {
    data: intentionData,
    loading: intentionLoading,
    error: intentionError,
  } = useIntentionsData(id);
  const {
    data: travelingTypeData,
    loading: travelingTypeLoading,
    error: travelingTypeError,
  } = useTravelingTypeData(id);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Compass className="w-5 h-5 text-blue-600" />
        <div>
          <h2 className="text-gray-900">Tourism Classification</h2>
          <p className="text-sm text-gray-600">Distribution by categories</p>
        </div>
      </div>

      <div className="space-y-6">
        {/* By Traveling Type */}
        <div>
          <h3 className="text-sm text-gray-700 mb-3">By Traveling Type</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={travelingTypeData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {travelingTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          {travelingTypeLoading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
              <span className="ml-2 text-sm text-gray-500">Loading...</span>
            </div>
          ) : travelingTypeError ? (
            <div className="text-sm text-red-500 py-2">
              {travelingTypeError}
            </div>
          ) : travelingTypeData.length === 0 ? (
            <div className="text-sm text-gray-500 py-2">
              No traveling type data available
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 mt-2">
              {travelingTypeData.map((item) => (
                <div
                  key={item.name}
                  className="flex items-center gap-2 text-xs"
                >
                  <div
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: item.color }}
                  ></div>
                  <span className="text-gray-600">
                    {item.name}: {item.value}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* By Intentions */}
        <div className="pt-4 border-t border-gray-200">
          <h3 className="text-sm text-gray-700 mb-2">By Intentions</h3>
          <div className="space-y-2">
            {intentionLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                <span className="ml-2 text-sm text-gray-500">Loading...</span>
              </div>
            ) : intentionError ? (
              <div className="text-sm text-red-500 py-2">{intentionError}</div>
            ) : intentionData.length === 0 ? (
              <div className="text-sm text-gray-500 py-2">
                No intentions data available
              </div>
            ) : (
              intentionData.map((item) => (
                <div key={item.name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{item.name}</span>
                    <span className="text-gray-600">{item.value}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          (item.value /
                            Math.max(...intentionData.map((d) => d.value))) *
                          100
                        }%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* By Geography - Continents */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-500" />
              <h3 className="text-sm text-gray-700">By Continent</h3>
            </div>
            <button
              onClick={() => navigate("/geography")}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              View all
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            Total: {continentTotal.toLocaleString()} mentions
          </p>
          <div className="space-y-3">
            {continentLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
                <span className="ml-2 text-sm text-gray-500">Loading...</span>
              </div>
            ) : continentError ? (
              <div className="text-sm text-red-500 py-2">{continentError}</div>
            ) : continentData.length === 0 ? (
              <div className="text-sm text-gray-500 py-2">
                No continent data available
              </div>
            ) : (
              continentData.map((item) => (
                <div
                  key={item.id}
                  className="space-y-1 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/geography/${item.id}`)}
                >
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-gray-700 font-medium">
                        {item.name}
                      </span>
                      <span className="text-xs text-gray-400">
                        ({item.countries?.length || 0} countries)
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 font-semibold">
                        {item.count.toLocaleString()}
                      </span>
                      <ChevronRight className="w-4 h-4 text-gray-400" />
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          (item.count /
                            Math.max(...continentData.map((d) => d.count), 1)) *
                          100
                        }%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
