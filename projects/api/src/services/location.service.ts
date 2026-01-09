import { locationRepository } from '../repositories/location.repository';
import { GeographyStats, Location } from '../entities/location.entity';

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
    const normalized = this.normalizeLocation(location.word);

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

  normalizeLocation(input: string): string {
    return input
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // strip accents
      .trim();
  }
}

export const locationService = new LocationService();
