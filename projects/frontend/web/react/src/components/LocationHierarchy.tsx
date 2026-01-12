import { useState } from 'react';
import { ChevronRight, MapPin, Globe, Home, Loader2 } from 'lucide-react';
import { useContinentData, useCountryData, useRegionData, ContinentStats } from '../hooks/useLocationHierarchy';

interface LocationHierarchyProps {
  onLocationClick?: (type: 'continent' | 'country' | 'region', id: string, name: string) => void;
}

/**
 * Location hierarchy drill-down component
 * Continent → Country → Region
 */
export function LocationHierarchy({ onLocationClick }: LocationHierarchyProps) {
  const [selectedContinent, setSelectedContinent] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  
  const { data: continents, total, loading: continentsLoading } = useContinentData();
  const { data: countries, continentName, loading: countriesLoading } = useCountryData(selectedContinent);
  const { data: regions, countryName, loading: regionsLoading } = useRegionData(selectedCountry);

  const handleContinentClick = (continent: ContinentStats) => {
    setSelectedContinent(continent.id);
    setSelectedCountry(null);
    onLocationClick?.('continent', continent.id, continent.name);
  };

  const handleCountryClick = (countryId: string, countryName: string) => {
    setSelectedCountry(countryId);
    onLocationClick?.('country', countryId, countryName);
  };

  const handleBack = () => {
    if (selectedCountry) {
      setSelectedCountry(null);
    } else if (selectedContinent) {
      setSelectedContinent(null);
    }
  };

  // Breadcrumb
  const renderBreadcrumb = () => (
    <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
      <button
        onClick={() => { setSelectedContinent(null); setSelectedCountry(null); }}
        className="flex items-center gap-1 hover:text-blue-600"
      >
        <Globe className="w-4 h-4" />
        <span>World</span>
      </button>
      {selectedContinent && (
        <>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <button
            onClick={() => setSelectedCountry(null)}
            className="hover:text-blue-600"
          >
            {continentName || selectedContinent}
          </button>
        </>
      )}
      {selectedCountry && (
        <>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <span className="text-gray-900 font-medium">
            {countryName || selectedCountry}
          </span>
        </>
      )}
    </div>
  );

  // Loading state
  const isLoading = continentsLoading || (selectedContinent && countriesLoading) || (selectedCountry && regionsLoading);

  if (isLoading && !continents.length) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading locations...</span>
        </div>
      </div>
    );
  }

  // Render regions view
  if (selectedCountry && regions.length > 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        {renderBreadcrumb()}
        
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <Home className="w-5 h-5 text-green-600" />
            Regions in {countryName}
          </h3>
          <button
            onClick={handleBack}
            className="text-sm text-blue-600 hover:underline"
          >
            ← Back to countries
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {regions.map((region) => (
            <button
              key={region.id}
              onClick={() => onLocationClick?.('region', region.id, region.name)}
              className="p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-left transition-colors"
            >
              <div className="font-medium text-gray-900">{region.name}</div>
              <div className="text-sm text-gray-500">{region.count} mentions</div>
            </button>
          ))}
        </div>

        {regionsLoading && (
          <div className="flex justify-center py-4">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          </div>
        )}
      </div>
    );
  }

  // Render countries view
  if (selectedContinent && countries.length > 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        {renderBreadcrumb()}
        
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-600" />
            Countries in {continentName}
          </h3>
          <button
            onClick={handleBack}
            className="text-sm text-blue-600 hover:underline"
          >
            ← Back to continents
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {countries.map((country) => (
            <button
              key={country.id}
              onClick={() => handleCountryClick(country.id, country.name)}
              className="p-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-left transition-colors group"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{country.name}</span>
                <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
              </div>
              <div className="text-sm text-gray-500">{country.count} mentions</div>
              {country.regions.length > 0 && (
                <div className="text-xs text-blue-600 mt-1">
                  {country.regions.length} regions
                </div>
              )}
            </button>
          ))}
        </div>

        {countriesLoading && (
          <div className="flex justify-center py-4">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          </div>
        )}
      </div>
    );
  }

  // Render continents view (default)
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {selectedContinent && renderBreadcrumb()}
      
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900 flex items-center gap-2">
          <Globe className="w-5 h-5 text-blue-600" />
          Location by Continent
        </h3>
        <span className="text-sm text-gray-500">{total} total mentions</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {continents.map((continent) => (
          <button
            key={continent.id}
            onClick={() => handleContinentClick(continent)}
            className="p-4 rounded-lg text-left transition-all hover:shadow-md group"
            style={{ backgroundColor: `${continent.color}10` }}
          >
            <div className="flex items-center justify-between">
              <span 
                className="font-semibold"
                style={{ color: continent.color }}
              >
                {continent.name}
              </span>
              <ChevronRight 
                className="w-5 h-5 transition-transform group-hover:translate-x-1"
                style={{ color: continent.color }}
              />
            </div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {continent.count.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">mentions</div>
            {continent.countries.length > 0 && (
              <div className="text-xs mt-2" style={{ color: continent.color }}>
                {continent.countries.length} countries found
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
