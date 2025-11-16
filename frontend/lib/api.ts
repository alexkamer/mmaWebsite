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
  list: (params?: { page?: number; page_size?: number; search?: string; weight_class?: string }) => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
    if (params?.search) queryParams.set('search', params.search);
    if (params?.weight_class) queryParams.set('weight_class', params.weight_class);

    return fetchAPI<FighterListResponse>(`/api/fighters/?${queryParams}`);
  },

  get: (id: number) => fetchAPI<FighterDetail>(`/api/fighters/${id}`),

  getFights: (id: number, limit = 20) =>
    fetchAPI<{ fights: Fight[] }>(`/api/fighters/${id}/fights?limit=${limit}`),
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
};

// Rankings endpoints
export const rankingsAPI = {
  getAll: () => fetchAPI<RankingsResponse>('/api/rankings/'),

  getDivision: (division: string) =>
    fetchAPI<{ division: string; rankings: RankingEntry[] }>(`/api/rankings/division/${division}`),
};

// Type definitions
export interface FighterBase {
  id: number;
  name: string;
  nickname?: string;
  image_url?: string;
  weight_class?: string;
  nationality?: string;
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
