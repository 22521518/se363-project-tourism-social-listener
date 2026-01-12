/**
 * Location Hierarchy Data
 * Maps countries to continents and regions/states to countries
 */

export interface ContinentData {
  name: string;
  countries: string[];
}

export const CONTINENTS: Record<string, ContinentData> = {
  asia: {
    name: 'Asia',
    countries: [
      'vietnam', 'thailand', 'cambodia', 'laos', 'myanmar', 'malaysia', 'singapore',
      'indonesia', 'philippines', 'brunei', 'timor-leste', 'china', 'japan', 'korea',
      'south korea', 'north korea', 'taiwan', 'hong kong', 'macau', 'mongolia',
      'india', 'pakistan', 'bangladesh', 'nepal', 'bhutan', 'sri lanka', 'maldives',
      'kazakhstan', 'uzbekistan', 'turkmenistan', 'tajikistan', 'kyrgyzstan',
      'afghanistan', 'iran', 'iraq', 'syria', 'jordan', 'lebanon', 'israel',
      'palestine', 'saudi arabia', 'uae', 'united arab emirates', 'qatar', 'bahrain',
      'kuwait', 'oman', 'yemen', 'turkey', 'georgia', 'armenia', 'azerbaijan',
    ],
  },
  europe: {
    name: 'Europe',
    countries: [
      'france', 'germany', 'italy', 'spain', 'portugal', 'united kingdom', 'uk',
      'england', 'scotland', 'wales', 'ireland', 'netherlands', 'belgium', 'luxembourg',
      'switzerland', 'austria', 'poland', 'czech', 'czechia', 'slovakia', 'hungary',
      'romania', 'bulgaria', 'greece', 'croatia', 'slovenia', 'serbia', 'montenegro',
      'bosnia', 'albania', 'north macedonia', 'kosovo', 'ukraine', 'russia',
      'belarus', 'moldova', 'lithuania', 'latvia', 'estonia', 'finland', 'sweden',
      'norway', 'denmark', 'iceland', 'cyprus', 'malta', 'monaco', 'andorra',
      'liechtenstein', 'san marino', 'vatican',
    ],
  },
  north_america: {
    name: 'North America',
    countries: [
      'united states', 'usa', 'us', 'america', 'canada', 'mexico', 'guatemala',
      'belize', 'honduras', 'el salvador', 'nicaragua', 'costa rica', 'panama',
      'cuba', 'jamaica', 'haiti', 'dominican republic', 'puerto rico', 'bahamas',
      'trinidad and tobago', 'barbados', 'grenada', 'saint lucia', 'dominica',
    ],
  },
  south_america: {
    name: 'South America',
    countries: [
      'brazil', 'argentina', 'chile', 'peru', 'colombia', 'venezuela', 'ecuador',
      'bolivia', 'paraguay', 'uruguay', 'guyana', 'suriname', 'french guiana',
    ],
  },
  africa: {
    name: 'Africa',
    countries: [
      'egypt', 'morocco', 'algeria', 'tunisia', 'libya', 'south africa', 'kenya',
      'tanzania', 'ethiopia', 'nigeria', 'ghana', 'senegal', 'ivory coast',
      'cameroon', 'uganda', 'rwanda', 'zambia', 'zimbabwe', 'botswana', 'namibia',
      'mozambique', 'madagascar', 'mauritius', 'seychelles',
    ],
  },
  oceania: {
    name: 'Oceania',
    countries: [
      'australia', 'new zealand', 'fiji', 'papua new guinea', 'samoa', 'tonga',
      'vanuatu', 'solomon islands', 'micronesia', 'palau', 'marshall islands',
      'kiribati', 'nauru', 'tuvalu', 'guam', 'new caledonia', 'french polynesia',
    ],
  },
};

/**
 * Country regions/states/provinces data
 */
export interface CountryRegions {
  [country: string]: string[];
}

export const COUNTRY_REGIONS: CountryRegions = {
  vietnam: [
    'hanoi', 'hà nội', 'ho chi minh', 'hồ chí minh', 'saigon', 'sài gòn',
    'da nang', 'đà nẵng', 'hai phong', 'hải phòng', 'can tho', 'cần thơ',
    'hue', 'huế', 'nha trang', 'da lat', 'đà lạt', 'phu quoc', 'phú quốc',
    'ha long', 'hạ long', 'hoi an', 'hội an', 'sapa', 'sa pa', 'quy nhon',
    'vung tau', 'ninh binh', 'mekong delta', 'central highlands',
  ],
  thailand: [
    'bangkok', 'phuket', 'chiang mai', 'pattaya', 'krabi', 'koh samui',
    'ayutthaya', 'sukhothai', 'chiang rai', 'hua hin', 'koh phi phi',
    'koh tao', 'koh phangan', 'kanchanaburi', 'pai',
  ],
  japan: [
    'tokyo', 'osaka', 'kyoto', 'hiroshima', 'nara', 'fukuoka', 'sapporo',
    'nagoya', 'yokohama', 'kobe', 'okinawa', 'hakone', 'nikko', 'kamakura',
    'kanazawa', 'takayama', 'miyajima', 'mount fuji',
  ],
  korea: [
    'seoul', 'busan', 'jeju', 'gyeongju', 'incheon', 'daegu', 'gwangju',
    'daejeon', 'suwon', 'jeonju', 'gangneung', 'sokcho',
  ],
  'south korea': [
    'seoul', 'busan', 'jeju', 'gyeongju', 'incheon', 'daegu', 'gwangju',
  ],
  singapore: [
    'marina bay', 'sentosa', 'orchard road', 'chinatown', 'little india',
    'gardens by the bay', 'clarke quay', 'changi',
  ],
  malaysia: [
    'kuala lumpur', 'penang', 'langkawi', 'malacca', 'melaka', 'kota kinabalu',
    'cameron highlands', 'george town', 'johor bahru', 'ipoh', 'kuching',
  ],
  indonesia: [
    'bali', 'jakarta', 'yogyakarta', 'lombok', 'ubud', 'bandung', 'surabaya',
    'komodo', 'flores', 'raja ampat', 'sumatra', 'sulawesi', 'borneo',
  ],
  philippines: [
    'manila', 'cebu', 'boracay', 'palawan', 'el nido', 'bohol', 'siargao',
    'davao', 'baguio', 'coron', 'puerto princesa',
  ],
  france: [
    'paris', 'nice', 'lyon', 'marseille', 'bordeaux', 'toulouse', 'strasbourg',
    'montpellier', 'provence', 'normandy', 'brittany', 'french riviera',
    'cote d\'azur', 'loire valley', 'alsace', 'champagne',
  ],
  italy: [
    'rome', 'venice', 'florence', 'milan', 'naples', 'turin', 'bologna',
    'cinque terre', 'amalfi coast', 'tuscany', 'sicily', 'sardinia',
    'verona', 'pisa', 'positano', 'capri', 'lake como',
  ],
  spain: [
    'barcelona', 'madrid', 'seville', 'valencia', 'granada', 'bilbao',
    'malaga', 'ibiza', 'mallorca', 'canary islands', 'san sebastian',
    'toledo', 'cordoba', 'santiago de compostela',
  ],
  germany: [
    'berlin', 'munich', 'frankfurt', 'hamburg', 'cologne', 'dresden',
    'heidelberg', 'nuremberg', 'bavaria', 'black forest', 'rothenburg',
  ],
  'united kingdom': [
    'london', 'edinburgh', 'manchester', 'liverpool', 'birmingham', 'oxford',
    'cambridge', 'bath', 'bristol', 'york', 'glasgow', 'brighton', 'cornwall',
  ],
  'united states': [
    'new york', 'los angeles', 'san francisco', 'las vegas', 'miami',
    'chicago', 'boston', 'washington dc', 'seattle', 'hawaii', 'california',
    'florida', 'texas', 'grand canyon', 'yellowstone', 'yosemite',
  ],
  australia: [
    'sydney', 'melbourne', 'brisbane', 'perth', 'gold coast', 'cairns',
    'adelaide', 'great barrier reef', 'uluru', 'tasmania', 'darwin',
  ],
  china: [
    'beijing', 'shanghai', 'hong kong', 'guangzhou', 'shenzhen', 'xi\'an',
    'hangzhou', 'chengdu', 'guilin', 'suzhou', 'yunnan', 'tibet', 'lhasa',
  ],
  india: [
    'delhi', 'mumbai', 'goa', 'jaipur', 'agra', 'kerala', 'varanasi',
    'bangalore', 'kolkata', 'chennai', 'udaipur', 'rajasthan', 'ladakh',
  ],
};

/**
 * Normalize a location string for comparison
 */
export function normalizeLocation(input: string): string {
  return input
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // strip accents
    .trim();
}

/**
 * Get continent for a location
 */
export function getContinentForLocation(location: string): string | null {
  const normalized = normalizeLocation(location);

  for (const [continentKey, continentData] of Object.entries(CONTINENTS)) {
    // Check if location is a country in this continent
    if (continentData.countries.some(country =>
      normalized === normalizeLocation(country) ||
      normalized.includes(normalizeLocation(country))
    )) {
      return continentKey;
    }

    // Check if location is a region in a country of this continent
    for (const country of continentData.countries) {
      const regions = COUNTRY_REGIONS[country];
      if (regions && regions.some(region =>
        normalized === normalizeLocation(region) ||
        normalized.includes(normalizeLocation(region))
      )) {
        return continentKey;
      }
    }
  }

  return null;
}

/**
 * Get country for a location
 */
export function getCountryForLocation(location: string): string | null {
  const normalized = normalizeLocation(location);

  // First check if it's a country name itself
  for (const [, continentData] of Object.entries(CONTINENTS)) {
    for (const country of continentData.countries) {
      if (normalized === normalizeLocation(country) ||
        normalized.includes(normalizeLocation(country))) {
        return country;
      }
    }
  }

  // Then check if it's a region within a country
  for (const [country, regions] of Object.entries(COUNTRY_REGIONS)) {
    if (regions.some(region =>
      normalized === normalizeLocation(region) ||
      normalized.includes(normalizeLocation(region))
    )) {
      return country;
    }
  }

  return null;
}
