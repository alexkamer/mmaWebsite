"use client"

import { useState } from "react"
import { Swords, Search, TrendingUp, User, X } from "lucide-react"
import { fightersAPI, type FighterBase, type FighterComparison } from "@/lib/api"
import Image from "next/image"

export default function TaleOfTapePage() {
  const [searchTerm1, setSearchTerm1] = useState("")
  const [searchTerm2, setSearchTerm2] = useState("")
  const [searchResults1, setSearchResults1] = useState<FighterBase[]>([])
  const [searchResults2, setSearchResults2] = useState<FighterBase[]>([])
  const [selectedFighter1, setSelectedFighter1] = useState<FighterBase | null>(null)
  const [selectedFighter2, setSelectedFighter2] = useState<FighterBase | null>(null)
  const [comparison, setComparison] = useState<FighterComparison | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const searchFighters = async (term: string, setResults: (results: FighterBase[]) => void) => {
    if (term.length < 2) {
      setResults([])
      return
    }

    try {
      const data = await fightersAPI.list({ search: term, page_size: 10 })
      setResults(data.fighters)
    } catch (err) {
      console.error("Error searching fighters:", err)
    }
  }

  const handleFighterSelect = (
    fighter: FighterBase,
    setSelected: (fighter: FighterBase | null) => void,
    setSearch: (term: string) => void,
    setResults: (results: FighterBase[]) => void
  ) => {
    setSelected(fighter)
    setSearch("")
    setResults([])
  }

  const handleCompare = async () => {
    if (!selectedFighter1 || !selectedFighter2) return

    setLoading(true)
    setError(null)

    try {
      const data = await fightersAPI.compare(selectedFighter1.id, selectedFighter2.id)
      setComparison(data)
    } catch (err) {
      console.error("Error comparing fighters:", err)
      setError("Failed to compare fighters. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSelectedFighter1(null)
    setSelectedFighter2(null)
    setComparison(null)
    setError(null)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="flex items-center gap-3 text-4xl font-bold">
          <Swords className="h-10 w-10" />
          Tale of the Tape
        </h1>
        <p className="text-muted-foreground">
          Compare two fighters side-by-side with detailed stats and head-to-head history
        </p>
      </div>

      {/* Fighter Selection */}
      {!comparison && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Fighter 1 Selection */}
          <FighterSelector
            label="Fighter 1"
            searchTerm={searchTerm1}
            setSearchTerm={setSearchTerm1}
            searchResults={searchResults1}
            selectedFighter={selectedFighter1}
            onSearch={(term) => searchFighters(term, setSearchResults1)}
            onSelect={(fighter) => handleFighterSelect(fighter, setSelectedFighter1, setSearchTerm1, setSearchResults1)}
            onClear={() => setSelectedFighter1(null)}
          />

          {/* Fighter 2 Selection */}
          <FighterSelector
            label="Fighter 2"
            searchTerm={searchTerm2}
            setSearchTerm={setSearchTerm2}
            searchResults={searchResults2}
            selectedFighter={selectedFighter2}
            onSearch={(term) => searchFighters(term, setSearchResults2)}
            onSelect={(fighter) => handleFighterSelect(fighter, setSelectedFighter2, setSearchTerm2, setSearchResults2)}
            onClear={() => setSelectedFighter2(null)}
          />
        </div>
      )}

      {/* Compare Button */}
      {selectedFighter1 && selectedFighter2 && !comparison && (
        <div className="flex justify-center">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="rounded-lg bg-primary px-8 py-3 font-bold text-primary-foreground transition-all hover:scale-105 disabled:opacity-50"
          >
            {loading ? "Comparing..." : "Compare Fighters"}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
          <h3 className="mb-2 font-bold text-red-500">Error</h3>
          <p className="text-muted-foreground">{error}</p>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-8">
          <div className="flex justify-end">
            <button
              onClick={handleReset}
              className="rounded-lg border bg-card px-4 py-2 transition-all hover:bg-muted"
            >
              Compare Different Fighters
            </button>
          </div>

          <ComparisonView comparison={comparison} />
        </div>
      )}
    </div>
  )
}

interface FighterSelectorProps {
  label: string
  searchTerm: string
  setSearchTerm: (term: string) => void
  searchResults: FighterBase[]
  selectedFighter: FighterBase | null
  onSearch: (term: string) => void
  onSelect: (fighter: FighterBase) => void
  onClear: () => void
}

function FighterSelector({
  label,
  searchTerm,
  setSearchTerm,
  searchResults,
  selectedFighter,
  onSearch,
  onSelect,
  onClear,
}: FighterSelectorProps) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-4 text-xl font-bold">{label}</h3>

      {!selectedFighter ? (
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                onSearch(e.target.value)
              }}
              placeholder="Search fighters..."
              className="w-full rounded-lg border bg-background px-10 py-3 focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          {searchResults.length > 0 && (
            <div className="absolute z-10 mt-2 w-full rounded-lg border bg-card shadow-lg">
              {searchResults.map((fighter) => (
                <button
                  key={fighter.id}
                  onClick={() => onSelect(fighter)}
                  className="flex w-full items-center gap-3 border-b p-3 transition-all hover:bg-muted last:border-b-0"
                >
                  <div className="relative h-12 w-12 overflow-hidden rounded-full">
                    {fighter.image_url ? (
                      <Image
                        src={fighter.image_url}
                        alt={fighter.name}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-muted">
                        <User className="h-6 w-6 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                  <div className="text-left">
                    <div className="font-semibold">{fighter.name}</div>
                    {fighter.weight_class && (
                      <div className="text-sm text-muted-foreground">{fighter.weight_class}</div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-between rounded-lg border bg-muted p-4">
          <div className="flex items-center gap-3">
            <div className="relative h-16 w-16 overflow-hidden rounded-full">
              {selectedFighter.image_url ? (
                <Image
                  src={selectedFighter.image_url}
                  alt={selectedFighter.name}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-card">
                  <User className="h-8 w-8 text-muted-foreground" />
                </div>
              )}
            </div>
            <div>
              <div className="font-bold">{selectedFighter.name}</div>
              {selectedFighter.weight_class && (
                <div className="text-sm text-muted-foreground">{selectedFighter.weight_class}</div>
              )}
            </div>
          </div>
          <button
            onClick={onClear}
            className="rounded-full p-2 transition-all hover:bg-card"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  )
}

function ComparisonView({ comparison }: { comparison: FighterComparison }) {
  const { fighter1, fighter2, head_to_head } = comparison

  return (
    <div className="space-y-8">
      {/* Fighter Cards */}
      <div className="grid gap-6 md:grid-cols-[1fr_auto_1fr]">
        <FighterCard fighter={fighter1} side="left" />

        <div className="flex items-center justify-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-2xl font-bold">
            VS
          </div>
        </div>

        <FighterCard fighter={fighter2} side="right" />
      </div>

      {/* Physical Comparison */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="mb-6 text-2xl font-bold">Physical Stats</h2>
        <div className="space-y-4">
          <StatComparison
            label="Height"
            value1={fighter1.height}
            value2={fighter2.height}
          />
          <StatComparison
            label="Weight"
            value1={fighter1.weight}
            value2={fighter2.weight}
          />
          <StatComparison
            label="Reach"
            value1={fighter1.reach}
            value2={fighter2.reach}
            unit="in"
          />
          <StatComparison
            label="Age"
            value1={fighter1.age?.toString()}
            value2={fighter2.age?.toString()}
          />
        </div>
      </div>

      {/* Record Comparison */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="mb-6 text-2xl font-bold">Fight Record</h2>
        <div className="space-y-4">
          <RecordComparison
            label="Record"
            value1={`${fighter1.record.wins}-${fighter1.record.losses}-${fighter1.record.draws}`}
            value2={`${fighter2.record.wins}-${fighter2.record.losses}-${fighter2.record.draws}`}
          />
          <BarComparison
            label="Total Wins"
            value1={fighter1.record.wins}
            value2={fighter2.record.wins}
          />
          <BarComparison
            label="KO/TKO Wins"
            value1={fighter1.record.ko_wins}
            value2={fighter2.record.ko_wins}
          />
          <BarComparison
            label="Submission Wins"
            value1={fighter1.record.sub_wins}
            value2={fighter2.record.sub_wins}
          />
        </div>
      </div>

      {/* Head to Head */}
      {head_to_head.fights.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="mb-6 text-2xl font-bold">Head to Head</h2>

          <div className="mb-6 flex items-center justify-center gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-green-500">{head_to_head.summary.fighter1_wins}</div>
              <div className="text-sm text-muted-foreground">{fighter1.name}</div>
            </div>
            <div className="text-2xl font-bold">-</div>
            <div>
              <div className="text-4xl font-bold text-red-500">{head_to_head.summary.fighter2_wins}</div>
              <div className="text-sm text-muted-foreground">{fighter2.name}</div>
            </div>
            {head_to_head.summary.draws > 0 && (
              <>
                <div className="text-2xl font-bold">-</div>
                <div>
                  <div className="text-4xl font-bold text-gray-500">{head_to_head.summary.draws}</div>
                  <div className="text-sm text-muted-foreground">Draws</div>
                </div>
              </>
            )}
          </div>

          <div className="space-y-4">
            {head_to_head.fights.map((fight) => (
              <div key={fight.id} className="rounded-lg border bg-muted p-4">
                <div className="mb-2 flex items-center justify-between">
                  <div className="font-semibold">{fight.event_name}</div>
                  <div className="text-sm text-muted-foreground">
                    {new Date(fight.date).toLocaleDateString()}
                  </div>
                </div>
                <div className="text-sm">
                  <span className={fight.winner_id === fighter1.id ? "font-bold text-green-500" : ""}>
                    {fighter1.name}
                  </span>
                  {" vs "}
                  <span className={fight.winner_id === fighter2.id ? "font-bold text-green-500" : ""}>
                    {fighter2.name}
                  </span>
                </div>
                <div className="mt-2 text-sm text-muted-foreground">
                  {fight.method}
                  {fight.round && ` - Round ${fight.round}`}
                  {fight.time && ` (${fight.time})`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Fights */}
      <div className="grid gap-6 md:grid-cols-2">
        <RecentFights fighter={fighter1} />
        <RecentFights fighter={fighter2} />
      </div>
    </div>
  )
}

function FighterCard({ fighter, side }: { fighter: any; side: "left" | "right" }) {
  return (
    <div className={`rounded-lg border bg-card p-6 ${side === "right" ? "md:text-right" : ""}`}>
      <div className={`flex items-center gap-4 ${side === "right" ? "md:flex-row-reverse" : ""}`}>
        <div className="relative h-24 w-24 overflow-hidden rounded-full border-4 border-primary/20">
          {fighter.image_url ? (
            <Image
              src={fighter.image_url}
              alt={fighter.name}
              fill
              className="object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-muted">
              <User className="h-12 w-12 text-muted-foreground" />
            </div>
          )}
        </div>
        <div>
          <h3 className="text-2xl font-bold">{fighter.name}</h3>
          {fighter.nickname && (
            <p className="text-sm text-muted-foreground">"{fighter.nickname}"</p>
          )}
          <p className="mt-2 text-xl font-bold text-primary">
            {fighter.record.wins}-{fighter.record.losses}-{fighter.record.draws}
          </p>
        </div>
      </div>
    </div>
  )
}

function StatComparison({ label, value1, value2, unit }: { label: string; value1?: string; value2?: string; unit?: string }) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
      <div className="text-right font-semibold">{value1 ? `${value1}${unit ? ` ${unit}` : ""}` : "N/A"}</div>
      <div className="text-muted-foreground">{label}</div>
      <div className="font-semibold">{value2 ? `${value2}${unit ? ` ${unit}` : ""}` : "N/A"}</div>
    </div>
  )
}

function RecordComparison({ label, value1, value2 }: { label: string; value1: string; value2: string }) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
      <div className="text-right text-xl font-bold text-primary">{value1}</div>
      <div className="text-muted-foreground">{label}</div>
      <div className="text-xl font-bold text-primary">{value2}</div>
    </div>
  )
}

function BarComparison({ label, value1, value2 }: { label: string; value1: number; value2: number }) {
  const max = Math.max(value1, value2)
  const percent1 = max > 0 ? (value1 / max) * 100 : 0
  const percent2 = max > 0 ? (value2 / max) * 100 : 0

  return (
    <div>
      <div className="mb-2 text-center text-sm font-semibold text-muted-foreground">{label}</div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="flex-1">
            <div className="h-8 overflow-hidden rounded bg-muted">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${percent1}%`, marginLeft: "auto" }}
              />
            </div>
          </div>
          <div className="w-8 text-right font-bold">{value1}</div>
        </div>
        <TrendingUp className="h-5 w-5 text-muted-foreground" />
        <div className="flex items-center gap-2">
          <div className="w-8 font-bold">{value2}</div>
          <div className="flex-1">
            <div className="h-8 overflow-hidden rounded bg-muted">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${percent2}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function RecentFights({ fighter }: { fighter: any }) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-4 text-xl font-bold">Recent Fights - {fighter.name}</h3>
      <div className="space-y-3">
        {fighter.recent_fights.map((fight: any) => (
          <div key={fight.id} className="rounded-lg border bg-muted p-3">
            <div className="mb-1 flex items-center justify-between">
              <span
                className={`font-semibold ${
                  fight.result === "win"
                    ? "text-green-500"
                    : fight.result === "loss"
                    ? "text-red-500"
                    : "text-gray-500"
                }`}
              >
                {fight.result.toUpperCase()}
              </span>
              <span className="text-sm text-muted-foreground">
                {new Date(fight.date).toLocaleDateString()}
              </span>
            </div>
            <div className="text-sm">vs {fight.opponent_name}</div>
            {fight.method && (
              <div className="text-xs text-muted-foreground">{fight.method}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
