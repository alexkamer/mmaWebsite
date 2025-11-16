/**
 * API client for FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

// Fighter endpoints
export const fightersAPI = {
  list: (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    weight_class?: string;
    weight_classes?: string[];
    nationality?: string;
    starts_with?: string;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
    if (params?.search) queryParams.set('search', params.search);
    if (params?.weight_class) queryParams.set('weight_class', params.weight_class);
    if (params?.weight_classes && params.weight_classes.length > 0) {
      queryParams.set('weight_classes', params.weight_classes.join(','));
    }
    if (params?.nationality) queryParams.set('nationality', params.nationality);
    if (params?.starts_with) queryParams.set('starts_with', params.starts_with);

    return fetchAPI<FighterListResponse>(`/api/fighters/?${queryParams}`);
  },

  getFilters: () => fetchAPI<FilterOptionsResponse>('/api/fighters/filters'),

  search: (query: string, params?: { limit?: number }) => {
    const queryParams = new URLSearchParams();
    queryParams.set('search', query);
    if (params?.limit) queryParams.set('page_size', params.limit.toString());

    return fetchAPI<FighterListResponse>(`/api/fighters/?${queryParams}`);
  },

  get: (id: number) => fetchAPI<FighterDetail>(`/api/fighters/${id}`),

  getFights: (id: number, limit = 20) =>
    fetchAPI<{ fights: Fight[] }>(`/api/fighters/${id}/fights?limit=${limit}`),

  compare: (fighter1Id: number, fighter2Id: number) =>
    fetchAPI<FighterComparison>(`/api/fighters/compare/${fighter1Id}/${fighter2Id}`),
};

// Event endpoints
export const eventsAPI = {
  list: (params?: { year?: number; promotion?: string; limit?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.year) queryParams.set('year', params.year.toString());
    if (params?.promotion) queryParams.set('promotion', params.promotion);
    if (params?.limit) queryParams.set('limit', params.limit.toString());

    return fetchAPI<EventListResponse>(`/api/events/?${queryParams}`);
  },

  get: (id: number) => fetchAPI<EventDetail>(`/api/events/${id}`),

  getYears: () => fetchAPI<{ years: number[] }>('/api/events/years'),

  getNext: () => fetchAPI<Event>('/api/events/upcoming/next'),

  getRecentFinishes: (params?: { limit?: number; promotion?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.promotion) queryParams.set('promotion', params.promotion);

    return fetchAPI<RecentFinishesResponse>(`/api/events/recent-finishes?${queryParams}`);
  },
};

// Rankings endpoints
export const rankingsAPI = {
  getAll: () => fetchAPI<RankingsResponse>('/api/rankings/'),

  getDivision: (division: string) =>
    fetchAPI<{ division: string; rankings: RankingEntry[] }>(`/api/rankings/division/${division}`),
};

// ESPN endpoints
export const espnAPI = {
  getNextEvent: () => fetchAPI<NextEventResponse>('/api/espn/next-event'),
};

// Wordle endpoints
export const wordleAPI = {
  getDaily: () => fetchAPI<{ date: string; hint: string }>('/api/wordle/daily'),

  submitGuess: (guessId: number) =>
    fetchAPI<WordleGuessResponse>(`/api/wordle/guess?guess_id=${guessId}`, {
      method: 'POST',
    }),

  reveal: () => fetchAPI<WordleFighter>('/api/wordle/reveal'),
};

// Betting endpoints
export const bettingAPI = {
  getYears: (league = 'ufc') =>
    fetchAPI<{ years: number[] }>(`/api/betting/years?league=${league}`),

  getOverview: (league = 'ufc', year?: string) => {
    const queryParams = new URLSearchParams({ league });
    if (year) queryParams.set('year', year);
    return fetchAPI<BettingOverview>(`/api/betting/overview?${queryParams}`);
  },

  getWeightClasses: (league = 'ufc', year?: string) => {
    const queryParams = new URLSearchParams({ league });
    if (year) queryParams.set('year', year);
    return fetchAPI<{ weight_classes: WeightClassStats[] }>(`/api/betting/weight-classes?${queryParams}`);
  },

  getRoundsFormat: (league = 'ufc', year?: string) => {
    const queryParams = new URLSearchParams({ league });
    if (year) queryParams.set('year', year);
    return fetchAPI<{ formats: RoundsFormatStats[] }>(`/api/betting/rounds-format?${queryParams}`);
  },

  getFinishTypes: (league = 'ufc', year?: string) => {
    const queryParams = new URLSearchParams({ league });
    if (year) queryParams.set('year', year);
    return fetchAPI<{ finish_types: FinishTypeStats[] }>(`/api/betting/finish-types?${queryParams}`);
  },

  getCards: (league = 'ufc', year?: string) => {
    const queryParams = new URLSearchParams({ league });
    if (year) queryParams.set('year', year);
    return fetchAPI<{ cards: CardStats[]; total: number }>(`/api/betting/cards?${queryParams}`);
  },
};

// Query endpoints
export const queryAPI = {
  ask: (question: string) =>
    fetchAPI<QueryResponse>(`/api/query/?question=${encodeURIComponent(question)}`, {
      method: 'POST',
    }),

  getExamples: () => fetchAPI<QueryExamplesResponse>('/api/query/examples'),
};

// Type definitions
export interface FighterBase {
  id: number;
  name: string;
  nickname?: string;
  image_url?: string;
  weight_class?: string;
  nationality?: string;
  flag_url?: string;
  team?: string;
  wins?: number;
  losses?: number;
  draws?: number;
}

export interface FighterDetail extends FighterBase {
  height?: string;
  weight?: string;
  reach?: string;
  stance?: string;
  date_of_birth?: string;
  wins?: number;
  losses?: number;
  draws?: number;
  no_contests?: number;
}

export interface FighterListResponse {
  fighters: FighterBase[];
  total: number;
  page: number;
  page_size: number;
}

export interface Fight {
  id: number;
  event_name: string;
  date: string;
  promotion: string;
  opponent_name: string;
  opponent_id: number;
  winner_id?: number;
  method?: string;
  method_detail?: string;
  round?: number;
  time?: string;
  result: 'win' | 'loss' | 'draw';
}

export interface Event {
  id: number;
  name: string;
  date?: string;
  location?: string;
  promotion?: string;
}

export interface EventDetail extends Event {
  venue?: string;
  fights?: EventFight[];
}

export interface EventFight {
  id: number;
  fighter1_id: number;
  fighter1_name: string;
  fighter1_image?: string;
  fighter2_id: number;
  fighter2_name: string;
  fighter2_image?: string;
  winner_id?: number;
  method?: string;
  method_detail?: string;
  round?: number;
  time?: string;
  weight_class?: string;
  is_title_fight?: boolean;
  winner?: 'fighter1' | 'fighter2';
  result?: string;
}

export interface EventListResponse {
  events: Event[];
  total: number;
}

export interface RankingEntry {
  rank: number;
  fighter_id?: number;
  fighter_name: string;
  division: string;
  is_champion: boolean;
  is_interim: boolean;
}

export interface RankingsResponse {
  divisions: Record<string, RankingEntry[]>;
  last_updated?: string;
}

export interface BettingOverview {
  total_fights: number;
  favorite_wins: number;
  underdog_wins: number;
  favorite_win_pct: number;
  underdog_win_pct: number;
}

export interface WeightClassStats {
  weight_class: string;
  total_fights: number;
  favorite_wins: number;
  underdog_wins: number;
  favorite_win_pct: number;
  underdog_win_pct: number;
}

export interface RoundsFormatStats {
  rounds_format: number;
  total_fights: number;
  favorite_wins: number;
  underdog_wins: number;
  favorite_win_pct: number;
  underdog_win_pct: number;
}

export interface FinishTypeStats {
  weight_class: string;
  total_fights: number;
  decisions: number;
  knockouts: number;
  submissions: number;
  decision_pct: number;
  knockout_pct: number;
  submission_pct: number;
  finish_pct: number;
}

export interface CardStats {
  event_id: number;
  event_name: string;
  date: string;
  fights_with_odds: number;
  favorite_wins: number;
  underdog_wins: number;
  decisions: number;
  knockouts: number;
  submissions: number;
  favorite_win_pct: number;
  underdog_win_pct: number;
  decision_pct: number;
  knockout_pct: number;
  submission_pct: number;
}

export interface NextEventResponse {
  event: {
    event_id: number;
    event_name: string;
    date: string;
    venue_name?: string;
    city?: string;
    state?: string;
    country?: string;
  };
  fights: NextEventFight[];
  total_fights: number;
}

export interface NextEventFight {
  fight_id: string;
  fighter_1_id: string;
  fighter_1_name: string;
  fighter_1_image?: string;
  fighter_1_record: string;
  fighter_1_odds?: string;
  fighter_2_id: string;
  fighter_2_name: string;
  fighter_2_image?: string;
  fighter_2_record: string;
  fighter_2_odds?: string;
  weight_class?: string;
  rounds_format?: number;
  match_number?: number;
}

export interface FighterRecord {
  wins: number;
  losses: number;
  draws: number;
  ko_wins: number;
  sub_wins: number;
}

export interface FighterComparisonData extends FighterDetail {
  age?: number;
  record: FighterRecord;
  recent_fights: Fight[];
}

export interface HeadToHeadFight {
  id: string;
  event_name: string;
  date: string;
  promotion: string;
  fighter_1_id: number;
  fighter_2_id: number;
  fighter_1_winner: number;
  fighter_2_winner: number;
  method: string;
  round?: number;
  time?: string;
  weight_class?: string;
  winner_id?: number | null;
}

export interface FighterComparison {
  fighter1: FighterComparisonData;
  fighter2: FighterComparisonData;
  head_to_head: {
    fights: HeadToHeadFight[];
    summary: {
      fighter1_wins: number;
      fighter2_wins: number;
      draws: number;
    };
  };
  common_opponents?: any[];
}

export interface WordleFighter {
  id: number;
  name: string;
  weight_class?: string;
  nationality?: string;
  age?: number;
  image_url?: string;
}

export interface WordleGuessResponse {
  correct: boolean;
  guess: WordleFighter;
  hints: {
    weight_class: string;
    nationality: string;
    age: string;
  };
  target?: WordleFighter;
}

export interface QueryResponse {
  question: string;
  answer: string;
  data: any;
  query_type: string;
  suggestions?: string[];
}

export interface QueryExample {
  category: string;
  queries: string[];
}

export interface QueryExamplesResponse {
  examples: QueryExample[];
}

export interface RecentFinish {
  fight_id: number;
  event_id: number;
  event_name: string;
  event_date: string;
  fighter1_id: number;
  fighter1_name: string;
  fighter1_image?: string;
  fighter2_id: number;
  fighter2_name: string;
  fighter2_image?: string;
  winner_name: string;
  winner_id?: number;
  winner_image?: string;
  finish_type: string;
  round: number;
  time: string;
  weight_class: string;
}

export interface RecentFinishesResponse {
  finishes: RecentFinish[];
  total: number;
}

export interface FilterOption {
  weight_class?: string;
  nationality?: string;
  count: number;
}

export interface FilterOptionsResponse {
  weight_classes: FilterOption[];
  nationalities: FilterOption[];
}
