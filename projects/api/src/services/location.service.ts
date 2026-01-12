import { locationRepository } from '../repositories/location.repository';
import {
  GeographyStats,
  Location,
  ContinentStats,
  CountryStats,
  RegionStats,
  LocationHierarchyResponse,
  CountryListResponse,
  RegionListResponse,
} from '../entities/location.entity';
import {
  CONTINENTS,
  COUNTRY_REGIONS,
  normalizeLocation,
  getContinentForLocation,
  getCountryForLocation,
} from './location_hierarchy.data';

/**
 * South East Asia countries and common variants (lowercase, normalized).
 * Used for REGIONAL / FOREIGN classification.
 */
const SOUTH_EAST_ASIA_COUNTRIES = new Set([
  // === Official country names ===
  'vietnam',
  'thailand',
  'cambodia',
  'laos',
  'myanmar',
  'malaysia',
  'singapore',
  'indonesia',
  'philippines',
  'brunei',
  'timor-leste',

  // === Alternative / common English names ===
  'east timor',
  'burma',          // Myanmar
  'siam',           // Thailand (old name)

  // === Adjectives / demonyms (commonly appear in text) ===
  'thai',
  'lao',
  'laotian',
  'burmese',
  'malaysian',
  'singaporean',
  'indonesian',
  'filipino',
  'filipina',
  'bruneian',
  'vietnamese',
  'cambodian',

  // === Common abbreviations ===
  'vn',  // Vietnam
  'th',  // Thailand
  'sg',  // Singapore
  'my',  // Malaysia
  'id',  // Indonesia
  'ph',  // Philippines
  'kh',  // Cambodia
  'la',  // Laos
  'mm',  // Myanmar
  'bn',  // Brunei
  'tl',  // Timor-Leste
]);

/**
 * Vietnam and its variations for DOMESTIC classification.
 * Includes country names, demonyms, major cities, provinces, and aliases.
 */
const VIETNAM_NAMES = new Set([
  // === Country level ===
  'vietnam',
  'viet nam',
  'việt nam',
  'vn',
  'vietnamese',

  // === Major cities (tier 1) ===
  'hanoi', 'hà nội',
  'ho chi minh', 'hồ chí minh', 'hcm', 'hcmc',
  'saigon', 'sài gòn',
  'da nang', 'đà nẵng',
  'hai phong', 'hải phòng',
  'can tho', 'cần thơ',

  // === Tier 2 cities / tourism hotspots ===
  'hue', 'huế',
  'nha trang',
  'da lat', 'đà lạt',
  'phu quoc', 'phú quốc',
  'ha long', 'hạ long',
  'hoi an', 'hội an',
  'quy nhon', 'quy nhơn',
  'vung tau', 'vũng tàu',
  'sapa', 'sa pa',

  // === Northern provinces ===
  'bac ninh', 'bắc ninh',
  'bac giang', 'bắc giang',
  'lao cai', 'lào cai',
  'yen bai', 'yên bái',
  'ninh binh', 'ninh bình',
  'thai nguyen', 'thái nguyên',
  'lang son', 'lạng sơn',
  'quang ninh', 'quảng ninh',

  // === Central provinces ===
  'quang binh', 'quảng bình',
  'quang tri', 'quảng trị',
  'quang nam', 'quảng nam',
  'quang ngai', 'quảng ngãi',
  'binh dinh', 'bình định',
  'phu yen', 'phú yên',
  'khanh hoa', 'khánh hòa',

  // === Southern provinces ===
  'dong nai', 'đồng nai',
  'binh duong', 'bình dương',
  'binh phuoc', 'bình phước',
  'tay ninh', 'tây ninh',
  'long an',
  'tien giang', 'tiền giang',
  'ben tre', 'bến tre',
  'an giang',
  'kien giang', 'kiên giang',
  'soc trang', 'sóc trăng',
  'bac lieu', 'bạc liêu',
  'ca mau', 'cà mau',
]);


type GeographyCategory = 'Domestic' | 'Regional' | 'International';

const CATEGORY_COLORS: Record<GeographyCategory, string> = {
  Domestic: '#3b82f6',      // Blue - Vietnam
  International: '#10b981', // Green - Rest of World
  Regional: '#f59e0b',      // Orange - South East Asia
};

const CONTINENT_COLORS: Record<string, string> = {
  asia: '#ef4444',          // Red
  europe: '#3b82f6',        // Blue
  north_america: '#22c55e', // Green
  south_america: '#f59e0b', // Orange
  africa: '#8b5cf6',        // Purple
  oceania: '#06b6d4',       // Cyan
};

export class LocationService {
  /**
   * Aggregate locations by geography category:
   * - Domestic: Vietnam
   * - Regional: South East Asia (excluding Vietnam)
   * - International: Rest of the world
   */
  async getGeographyStats(): Promise<GeographyStats[]> {
    const locations = await locationRepository.findAllLocationsFlat();

    // Count by category
    const countByCategory = new Map<GeographyCategory, number>([
      ['Domestic', 0],
      ['Regional', 0],
      ['International', 0],
    ]);

    for (const loc of locations) {
      const category = this.classifyLocation(loc);
      countByCategory.set(category, (countByCategory.get(category) || 0) + 1);
    }

    // Convert to array - always include all categories even with 0 count
    const stats: GeographyStats[] = [
      { name: 'Domestic', value: countByCategory.get('Domestic') || 0, color: CATEGORY_COLORS.Domestic },
      { name: 'Regional', value: countByCategory.get('Regional') || 0, color: CATEGORY_COLORS.Regional },
      { name: 'International', value: countByCategory.get('International') || 0, color: CATEGORY_COLORS.International },
    ];

    return stats.sort((a, b) => b.value - a.value);
  }

  /**
   * Get location hierarchy by continents
   */
  async getContinentStats(): Promise<LocationHierarchyResponse> {
    const locations = await locationRepository.findAllLocationsFlat();

    // Count by continent
    const countByContinent = new Map<string, number>();
    const countriesByContinent = new Map<string, Set<string>>();

    for (const loc of locations) {
      const continent = getContinentForLocation(loc.word);
      if (continent) {
        countByContinent.set(continent, (countByContinent.get(continent) || 0) + 1);

        const country = getCountryForLocation(loc.word);
        if (country) {
          if (!countriesByContinent.has(continent)) {
            countriesByContinent.set(continent, new Set());
          }
          countriesByContinent.get(continent)!.add(country);
        }
      }
    }

    const continents: ContinentStats[] = [];
    let total = 0;

    for (const [continentKey, continentData] of Object.entries(CONTINENTS)) {
      const count = countByContinent.get(continentKey) || 0;
      total += count;

      continents.push({
        id: continentKey,
        name: continentData.name,
        count,
        countries: Array.from(countriesByContinent.get(continentKey) || []),
        color: CONTINENT_COLORS[continentKey] || '#6b7280',
      });
    }

    // Sort by count descending
    continents.sort((a, b) => b.count - a.count);

    return { continents, total };
  }

  /**
   * Get countries for a specific continent
   */
  async getCountriesForContinent(continentId: string): Promise<CountryListResponse> {
    const locations = await locationRepository.findAllLocationsFlat();
    const continentData = CONTINENTS[continentId];

    if (!continentData) {
      return { countries: [], continent: continentId, total: 0 };
    }

    // Count by country
    const countByCountry = new Map<string, number>();
    const regionsByCountry = new Map<string, Set<string>>();

    for (const loc of locations) {
      const country = getCountryForLocation(loc.word);
      if (country && continentData.countries.includes(country)) {
        countByCountry.set(country, (countByCountry.get(country) || 0) + 1);

        // Check if this is a region
        const regions = COUNTRY_REGIONS[country];
        if (regions) {
          const normalized = normalizeLocation(loc.word);
          for (const region of regions) {
            if (normalized.includes(normalizeLocation(region))) {
              if (!regionsByCountry.has(country)) {
                regionsByCountry.set(country, new Set());
              }
              regionsByCountry.get(country)!.add(region);
            }
          }
        }
      }
    }

    const countries: CountryStats[] = [];
    let total = 0;

    for (const [country, count] of countByCountry.entries()) {
      total += count;
      countries.push({
        id: country.replace(/\s+/g, '_').toLowerCase(),
        name: country.charAt(0).toUpperCase() + country.slice(1),
        continent: continentId,
        count,
        regions: Array.from(regionsByCountry.get(country) || []),
      });
    }

    // Sort by count descending
    countries.sort((a, b) => b.count - a.count);

    return { countries, continent: continentData.name, total };
  }

  /**
   * Get regions for a specific country
   */
  async getRegionsForCountry(countryId: string): Promise<RegionListResponse> {
    const locations = await locationRepository.findAllLocationsFlat();
    const countryName = countryId.replace(/_/g, ' ').toLowerCase();
    const regions = COUNTRY_REGIONS[countryName] || [];

    if (regions.length === 0) {
      return { regions: [], country: countryId, total: 0 };
    }

    // Count by region
    const countByRegion = new Map<string, number>();

    for (const loc of locations) {
      const normalized = normalizeLocation(loc.word);
      for (const region of regions) {
        if (normalized === normalizeLocation(region) ||
          normalized.includes(normalizeLocation(region))) {
          countByRegion.set(region, (countByRegion.get(region) || 0) + 1);
        }
      }
    }

    const regionStats: RegionStats[] = [];
    let total = 0;

    for (const [region, count] of countByRegion.entries()) {
      total += count;
      regionStats.push({
        id: region.replace(/\s+/g, '_').toLowerCase(),
        name: region.charAt(0).toUpperCase() + region.slice(1),
        country: countryId,
        count,
      });
    }

    // Sort by count descending
    regionStats.sort((a, b) => b.count - a.count);

    return { regions: regionStats, country: countryName, total };
  }

  /**
   * Classify a location as Domestic, Regional, or International.
   */
  private classifyLocation(location: Location): GeographyCategory {
    const normalized = normalizeLocation(location.word);

    // Check if it's Vietnam (Domestic)
    if (VIETNAM_NAMES.has(normalized)) {
      return 'Domestic';
    }

    // Check if name contains Vietnam-related keywords
    for (const vietnamName of VIETNAM_NAMES) {
      if (normalized.includes(vietnamName)) {
        return 'Domestic';
      }
    }

    // Check if it's South East Asia (Regional)
    if (SOUTH_EAST_ASIA_COUNTRIES.has(normalized)) {
      return 'Regional';
    }

    // Check if name contains SEA country names
    for (const seaCountry of SOUTH_EAST_ASIA_COUNTRIES) {
      if (normalized.includes(seaCountry)) {
        return 'Regional';
      }
    }

    // Everything else is International
    return 'International';
  }
}

export const locationService = new LocationService();
