import { locationRepository } from '../repositories/location.repository';
import { GeographyStats, Location } from '../entities/location.entity';

/**
 * South East Asia countries for Regional classification.
 * Origin country (Vietnam) is excluded - it goes to Domestic.
 */
const SOUTH_EAST_ASIA_COUNTRIES = new Set([
  'thailand', 'cambodia', 'laos', 'myanmar', 'malaysia', 'singapore',
  'indonesia', 'philippines', 'brunei', 'timor-leste', 'east timor',
  // Common alternative names
  'thai', 'lao', 'burma',
]);

/**
 * Vietnam and its variations for Domestic classification.
 */
const VIETNAM_NAMES = new Set([
  'vietnam', 'việt nam', 'viet nam', 'vietnamese',
  // Major Vietnamese cities/provinces are considered domestic
  'hanoi', 'hà nội', 'ho chi minh', 'hồ chí minh', 'saigon', 'sài gòn',
  'da nang', 'đà nẵng', 'hue', 'huế', 'nha trang', 'da lat', 'đà lạt',
  'phu quoc', 'phú quốc', 'ha long', 'hạ long', 'sapa', 'sa pa',
  'hoi an', 'hội an', 'can tho', 'cần thơ', 'vung tau', 'vũng tàu',
  'quy nhon', 'quy nhơn', 'hai phong', 'hải phòng', 'ninh binh', 'ninh bình',
]);

type GeographyCategory = 'Domestic' | 'Regional' | 'International';

const CATEGORY_COLORS: Record<GeographyCategory, string> = {
  Domestic: '#3b82f6',      // Blue - Vietnam
  International: '#10b981', // Green - Rest of World
  Regional: '#f59e0b',      // Orange - South East Asia
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
   * Classify a location as Domestic, Regional, or International.
   */
  private classifyLocation(location: Location): GeographyCategory {
    const name = location.name.toLowerCase().trim();

    // Check if it's Vietnam (Domestic)
    if (VIETNAM_NAMES.has(name)) {
      return 'Domestic';
    }

    // Check if name contains Vietnam-related keywords
    for (const vietnamName of VIETNAM_NAMES) {
      if (name.includes(vietnamName)) {
        return 'Domestic';
      }
    }

    // Check if it's South East Asia (Regional)
    if (SOUTH_EAST_ASIA_COUNTRIES.has(name)) {
      return 'Regional';
    }

    // Check if name contains SEA country names
    for (const seaCountry of SOUTH_EAST_ASIA_COUNTRIES) {
      if (name.includes(seaCountry)) {
        return 'Regional';
      }
    }

    // Everything else is International
    return 'International';
  }
}

export const locationService = new LocationService();
