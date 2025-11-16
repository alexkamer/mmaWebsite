import { useQuery } from "@tanstack/react-query"
import { fightersAPI, eventsAPI, rankingsAPI, espnAPI, bettingAPI, wordleAPI, queryAPI } from "@/lib/api"

// Fighters
export function useFighters(params?: Parameters<typeof fightersAPI.list>[0]) {
  return useQuery({
    queryKey: ["fighters", params],
    queryFn: () => fightersAPI.list(params),
  })
}

export function useFighter(id: number) {
  return useQuery({
    queryKey: ["fighter", id],
    queryFn: () => fightersAPI.get(id),
    enabled: !!id,
  })
}

export function useFighterFights(id: number, limit = 20) {
  return useQuery({
    queryKey: ["fighter-fights", id, limit],
    queryFn: () => fightersAPI.getFights(id, limit),
    enabled: !!id,
  })
}

export function useFighterComparison(fighter1Id: number, fighter2Id: number) {
  return useQuery({
    queryKey: ["fighter-comparison", fighter1Id, fighter2Id],
    queryFn: () => fightersAPI.compare(fighter1Id, fighter2Id),
    enabled: !!fighter1Id && !!fighter2Id,
  })
}

// Events
export function useEvents(params?: Parameters<typeof eventsAPI.list>[0]) {
  return useQuery({
    queryKey: ["events", params],
    queryFn: () => eventsAPI.list(params),
  })
}

export function useEvent(id: number) {
  return useQuery({
    queryKey: ["event", id],
    queryFn: () => eventsAPI.get(id),
    enabled: !!id,
  })
}

export function useEventYears() {
  return useQuery({
    queryKey: ["event-years"],
    queryFn: () => eventsAPI.getYears(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useNextEvent() {
  return useQuery({
    queryKey: ["next-event"],
    queryFn: () => eventsAPI.getNext(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Rankings
export function useRankings() {
  return useQuery({
    queryKey: ["rankings"],
    queryFn: () => rankingsAPI.getAll(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useDivisionRankings(division: string) {
  return useQuery({
    queryKey: ["rankings", division],
    queryFn: () => rankingsAPI.getDivision(division),
    enabled: !!division,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// ESPN
export function useEspnNextEvent() {
  return useQuery({
    queryKey: ["espn-next-event"],
    queryFn: () => espnAPI.getNextEvent(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Betting
export function useBettingYears(league = "ufc") {
  return useQuery({
    queryKey: ["betting-years", league],
    queryFn: () => bettingAPI.getYears(league),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useBettingOverview(league = "ufc", year?: string) {
  return useQuery({
    queryKey: ["betting-overview", league, year],
    queryFn: () => bettingAPI.getOverview(league, year),
  })
}

export function useBettingWeightClasses(league = "ufc", year?: string) {
  return useQuery({
    queryKey: ["betting-weight-classes", league, year],
    queryFn: () => bettingAPI.getWeightClasses(league, year),
  })
}

export function useBettingRoundsFormat(league = "ufc", year?: string) {
  return useQuery({
    queryKey: ["betting-rounds-format", league, year],
    queryFn: () => bettingAPI.getRoundsFormat(league, year),
  })
}

export function useBettingFinishTypes(league = "ufc", year?: string) {
  return useQuery({
    queryKey: ["betting-finish-types", league, year],
    queryFn: () => bettingAPI.getFinishTypes(league, year),
  })
}

export function useBettingCards(league = "ufc", year?: string) {
  return useQuery({
    queryKey: ["betting-cards", league, year],
    queryFn: () => bettingAPI.getCards(league, year),
  })
}

// Wordle
export function useWordleDaily() {
  return useQuery({
    queryKey: ["wordle-daily", new Date().toISOString().split('T')[0]], // Cache per day
    queryFn: () => wordleAPI.getDaily(),
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}

// Query
export function useQueryExamples() {
  return useQuery({
    queryKey: ["query-examples"],
    queryFn: () => queryAPI.getExamples(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}
