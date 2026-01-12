import { useState } from "react";
import { useNavigate, useParams } from "react-router";
import {
  Globe,
  MapPin,
  Building2,
  ChevronRight,
  ChevronLeft,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import {
  useContinentData,
  useCountryData,
  useRegionData,
  ContinentStats,
  CountryStats,
  RegionStats,
} from "../hooks/useLocationHierarchy";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// Color palette for continents
const CONTINENT_COLORS: Record<string, string> = {
  africa: "#f59e0b",
  asia: "#ef4444",
  europe: "#3b82f6",
  "north-america": "#10b981",
  "south-america": "#8b5cf6",
  oceania: "#ec4899",
  antarctica: "#6b7280",
};

export default function Geography() {
  const navigate = useNavigate();
  const { continentId, countryId } = useParams();

  // Fetch data based on current level
  const {
    data: continents,
    total: continentTotal,
    loading: continentsLoading,
    error: continentsError,
  } = useContinentData();

  const {
    data: countries,
    continentName,
    total: countryTotal,
    loading: countriesLoading,
    error: countriesError,
  } = useCountryData(continentId || null);

  const {
    data: regions,
    countryName,
    total: regionTotal,
    loading: regionsLoading,
    error: regionsError,
  } = useRegionData(countryId || null);

  // Determine current view level
  const currentLevel = countryId ? "region" : continentId ? "country" : "continent";

  const handleBack = () => {
    if (currentLevel === "region") {
      navigate(`/geography/${continentId}`);
    } else if (currentLevel === "country") {
      navigate("/geography");
    } else {
      navigate("/dashboard");
    }
  };

  const renderBreadcrumb = () => {
    return (
      <nav className="flex items-center gap-2 text-sm text-gray-600 mb-6">
        <button
          onClick={() => navigate("/dashboard")}
          className="hover:text-blue-600"
        >
          Dashboard
        </button>
        <ChevronRight className="w-4 h-4" />
        <button
          onClick={() => navigate("/geography")}
          className={`hover:text-blue-600 ${
            currentLevel === "continent" ? "text-gray-900 font-medium" : ""
          }`}
        >
          Geography
        </button>
        {continentId && (
          <>
            <ChevronRight className="w-4 h-4" />
            <button
              onClick={() => navigate(`/geography/${continentId}`)}
              className={`hover:text-blue-600 ${
                currentLevel === "country" ? "text-gray-900 font-medium" : ""
              }`}
            >
              {continentName || continentId}
            </button>
          </>
        )}
        {countryId && (
          <>
            <ChevronRight className="w-4 h-4" />
            <span className="text-gray-900 font-medium">
              {countryName || countryId}
            </span>
          </>
        )}
      </nav>
    );
  };

  const renderContinents = () => {
    if (continentsLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-3 text-gray-600">Loading continents...</span>
        </div>
      );
    }

    if (continentsError) {
      return (
        <div className="text-center py-12 text-red-500">{continentsError}</div>
      );
    }

    if (continents.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          No continent data available
        </div>
      );
    }

    const maxCount = Math.max(...continents.map((c) => c.count), 1);

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-blue-700">Total Continents</span>
            </div>
            <span className="text-2xl font-bold text-blue-900">
              {continents.length}
            </span>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Building2 className="w-5 h-5 text-green-600" />
              <span className="text-sm text-green-700">Total Countries</span>
            </div>
            <span className="text-2xl font-bold text-green-900">
              {continents.reduce((acc, c) => acc + (c.countries?.length || 0), 0)}
            </span>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-purple-700">Total Mentions</span>
            </div>
            <span className="text-2xl font-bold text-purple-900">
              {continentTotal.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Mentions by Continent
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={continents} layout="vertical">
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {continents.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Continent List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y">
          {continents.map((continent) => (
            <div
              key={continent.id}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => navigate(`/geography/${continent.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: continent.color }}
                  />
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {continent.name}
                    </h4>
                    <p className="text-sm text-gray-500">
                      {continent.countries?.length || 0} countries
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="font-semibold text-gray-900">
                      {continent.count.toLocaleString()}
                    </span>
                    <p className="text-xs text-gray-500">mentions</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${(continent.count / maxCount) * 100}%`,
                    backgroundColor: continent.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderCountries = () => {
    if (countriesLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-3 text-gray-600">Loading countries...</span>
        </div>
      );
    }

    if (countriesError) {
      return (
        <div className="text-center py-12 text-red-500">{countriesError}</div>
      );
    }

    if (countries.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          No country data available for this continent
        </div>
      );
    }

    const maxCount = Math.max(...countries.map((c) => c.count), 1);
    const continentColor =
      CONTINENT_COLORS[continentId?.toLowerCase() || ""] || "#3b82f6";

    return (
      <div className="space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Building2 className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-blue-700">Countries</span>
            </div>
            <span className="text-2xl font-bold text-blue-900">
              {countries.length}
            </span>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-purple-700">Total Mentions</span>
            </div>
            <span className="text-2xl font-bold text-purple-900">
              {countryTotal.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Country List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y">
          {countries.map((country, index) => (
            <div
              key={country.id}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => navigate(`/geography/${continentId}/${country.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm w-6">
                    {index + 1}.
                  </span>
                  <div>
                    <h4 className="font-medium text-gray-900">{country.name}</h4>
                    <p className="text-sm text-gray-500">
                      {country.regions?.length || 0} regions
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="font-semibold text-gray-900">
                      {country.count.toLocaleString()}
                    </span>
                    <p className="text-xs text-gray-500">mentions</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2 ml-9">
                <div
                  className="h-2 rounded-full transition-all"
                  style={{
                    width: `${(country.count / maxCount) * 100}%`,
                    backgroundColor: continentColor,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderRegions = () => {
    if (regionsLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-3 text-gray-600">Loading regions...</span>
        </div>
      );
    }

    if (regionsError) {
      return (
        <div className="text-center py-12 text-red-500">{regionsError}</div>
      );
    }

    if (regions.length === 0) {
      return (
        <div className="text-center py-12 text-gray-500">
          No region data available for this country
        </div>
      );
    }

    const maxCount = Math.max(...regions.map((r) => r.count), 1);

    return (
      <div className="space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-blue-700">Regions</span>
            </div>
            <span className="text-2xl font-bold text-blue-900">
              {regions.length}
            </span>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-purple-700">Total Mentions</span>
            </div>
            <span className="text-2xl font-bold text-purple-900">
              {regionTotal.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Region List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y">
          {regions.map((region, index) => (
            <div key={region.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-gray-400 text-sm w-6">
                    {index + 1}.
                  </span>
                  <h4 className="font-medium text-gray-900">{region.name}</h4>
                </div>
                <div className="text-right">
                  <span className="font-semibold text-gray-900">
                    {region.count.toLocaleString()}
                  </span>
                  <p className="text-xs text-gray-500">mentions</p>
                </div>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2 ml-9">
                <div
                  className="h-2 rounded-full transition-all bg-blue-500"
                  style={{
                    width: `${(region.count / maxCount) * 100}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Back button */}
        <button
          onClick={handleBack}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>

        {/* Breadcrumb */}
        {renderBreadcrumb()}

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Globe className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {currentLevel === "region"
                ? countryName || "Regions"
                : currentLevel === "country"
                ? continentName || "Countries"
                : "Geographic Distribution"}
            </h1>
            <p className="text-gray-600">
              {currentLevel === "region"
                ? "Explore regions and cities"
                : currentLevel === "country"
                ? "Explore countries in this continent"
                : "Explore mentions by geographic location"}
            </p>
          </div>
        </div>

        {/* Content */}
        {currentLevel === "region"
          ? renderRegions()
          : currentLevel === "country"
          ? renderCountries()
          : renderContinents()}
      </div>
    </div>
  );
}
