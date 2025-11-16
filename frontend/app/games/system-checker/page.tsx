"use client"

import { useState, useEffect } from "react"
import { TrendingUp, TrendingDown, BarChart3, PieChart } from "lucide-react"
import {
  bettingAPI,
  type BettingOverview,
  type WeightClassStats,
  type RoundsFormatStats,
  type FinishTypeStats,
  type CardStats,
} from "@/lib/api"

export default function SystemCheckerPage() {
  const [selectedLeague, setSelectedLeague] = useState("ufc")
  const [selectedYear, setSelectedYear] = useState<string>("")
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [overview, setOverview] = useState<BettingOverview | null>(null)
  const [weightClasses, setWeightClasses] = useState<WeightClassStats[]>([])
  const [roundsFormats, setRoundsFormats] = useState<RoundsFormatStats[]>([])
  const [finishTypes, setFinishTypes] = useState<FinishTypeStats[]>([])
  const [cards, setCards] = useState<CardStats[]>([])
  const [loading, setLoading] = useState(true)

  // Fetch available years when league changes
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const data = await bettingAPI.getYears(selectedLeague)
        setAvailableYears(data.years)
        if (data.years.length > 0 && !selectedYear) {
          setSelectedYear(data.years[0].toString())
        }
      } catch (error) {
        console.error("Error fetching years:", error)
      }
    }
    fetchYears()
  }, [selectedLeague])

  // Fetch all data when league or year changes
  useEffect(() => {
    const fetchData = async () => {
      if (!selectedYear) return

      setLoading(true)
      try {
        const [overviewData, weightClassData, roundsData, finishData, cardsData] =
          await Promise.all([
            bettingAPI.getOverview(selectedLeague, selectedYear),
            bettingAPI.getWeightClasses(selectedLeague, selectedYear),
            bettingAPI.getRoundsFormat(selectedLeague, selectedYear),
            bettingAPI.getFinishTypes(selectedLeague, selectedYear),
            bettingAPI.getCards(selectedLeague, selectedYear),
          ])

        setOverview(overviewData)
        setWeightClasses(weightClassData.weight_classes)
        setRoundsFormats(roundsData.formats)
        setFinishTypes(finishData.finish_types)
        setCards(cardsData.cards)
      } catch (error) {
        console.error("Error fetching betting data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [selectedLeague, selectedYear])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-64 animate-pulse rounded bg-gray-700" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-700" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <h1 className="text-4xl font-bold flex items-center gap-3">
          <TrendingUp className="h-10 w-10" />
          MMA Betting Analytics
        </h1>
        <p className="text-muted-foreground">
          Card-by-Card Favorite vs Underdog Performance
        </p>
      </div>

      {/* League & Year Selector */}
      <div className="rounded-lg border bg-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* League Selection */}
          <div>
            <h2 className="text-lg font-bold mb-3">Select League</h2>
            <div className="flex gap-2">
              {["ufc", "pfl", "bellator"].map((league) => (
                <button
                  key={league}
                  onClick={() => setSelectedLeague(league)}
                  className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all text-sm ${
                    selectedLeague === league
                      ? "bg-primary text-primary-foreground shadow-lg"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  {league.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Year Selection */}
          <div>
            <h2 className="text-lg font-bold mb-3">Select Year</h2>
            <div className="flex gap-2 flex-wrap">
              {availableYears.map((year) => (
                <button
                  key={year}
                  onClick={() => setSelectedYear(year.toString())}
                  className={`px-4 py-3 rounded-lg font-semibold transition-all text-sm ${
                    selectedYear === year.toString()
                      ? "bg-primary text-primary-foreground shadow-lg"
                      : "bg-muted hover:bg-muted/80"
                  }`}
                >
                  {year}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Overview Stats */}
      {overview && overview.total_fights > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-bold mb-4">
            {selectedLeague.toUpperCase()} {selectedYear} - Quick Stats
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="text-center p-6 bg-green-500/10 rounded-lg border-2 border-green-500/20">
              <div className="text-5xl font-bold text-green-500 mb-2">
                {overview.favorite_win_pct}%
              </div>
              <div className="font-medium mb-1">Favorites Win Rate (Overall)</div>
              <div className="text-sm text-muted-foreground">
                {overview.favorite_wins.toLocaleString()} wins
              </div>
            </div>

            <div className="text-center p-6 bg-red-500/10 rounded-lg border-2 border-red-500/20">
              <div className="text-5xl font-bold text-red-500 mb-2">
                {overview.underdog_win_pct}%
              </div>
              <div className="font-medium mb-1">Underdogs Win Rate (Overall)</div>
              <div className="text-sm text-muted-foreground">
                {overview.underdog_wins.toLocaleString()} upsets
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Weight Class Breakdown */}
      {weightClasses.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Weight Class Performance
          </h2>
          <p className="text-sm text-muted-foreground mb-6">
            How favorites and underdogs perform across different weight classes
            (minimum 3 fights)
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {weightClasses.map((wc) => (
              <div
                key={wc.weight_class}
                className="border-2 rounded-lg p-4 hover:border-primary/50 transition-colors"
              >
                {/* Header */}
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-bold text-lg">{wc.weight_class}</h3>
                  <span className="text-sm bg-muted px-3 py-1 rounded-full font-medium">
                    {wc.total_fights} fights
                  </span>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="bg-green-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-500">
                      {wc.favorite_win_pct}%
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">Favorites</div>
                    <div className="text-xs text-muted-foreground">
                      {wc.favorite_wins} wins
                    </div>
                  </div>

                  <div className="bg-red-500/10 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-red-500">
                      {wc.underdog_win_pct}%
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">Underdogs</div>
                    <div className="text-xs text-muted-foreground">
                      {wc.underdog_wins} upsets
                    </div>
                  </div>
                </div>

                {/* Visual Bar */}
                <div className="flex h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-green-500"
                    style={{ width: `${wc.favorite_win_pct}%` }}
                  />
                  <div
                    className="bg-red-500"
                    style={{ width: `${wc.underdog_win_pct}%` }}
                  />
                </div>

                {/* Insights */}
                <div className="mt-2 text-xs text-center">
                  {wc.underdog_win_pct > 55
                    ? "🔥 Upset-heavy division"
                    : wc.favorite_win_pct > 65
                    ? "✅ Favorites dominate"
                    : "⚖️ Balanced competition"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rounds Format & Finish Types */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 3-Round vs 5-Round */}
        {roundsFormats.length > 0 && (
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-bold mb-4">⏱️ Rounds Format Analysis</h2>
            <p className="text-sm text-muted-foreground mb-6">
              How favorites perform in 3-round vs 5-round fights
            </p>

            <div className="space-y-4">
              {roundsFormats.map((rf) => (
                <div
                  key={rf.rounds_format}
                  className="border-2 rounded-lg p-4 hover:border-primary/50 transition-colors"
                >
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-bold text-lg">
                      {rf.rounds_format === 3
                        ? "🥊 3-Round Fights"
                        : "👑 5-Round Fights (Title/Main Events)"}
                    </h3>
                    <span className="text-sm bg-muted px-3 py-1 rounded-full font-medium">
                      {rf.total_fights} fights
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-green-500/10 rounded-lg p-3 text-center">
                      <div className="text-3xl font-bold text-green-500">
                        {rf.favorite_win_pct}%
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Favorites
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {rf.favorite_wins} wins
                      </div>
                    </div>
                    <div className="bg-red-500/10 rounded-lg p-3 text-center">
                      <div className="text-3xl font-bold text-red-500">
                        {rf.underdog_win_pct}%
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Underdogs
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {rf.underdog_wins} upsets
                      </div>
                    </div>
                  </div>

                  {/* Visual Bar */}
                  <div className="flex h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-green-500"
                      style={{ width: `${rf.favorite_win_pct}%` }}
                    />
                    <div
                      className="bg-red-500"
                      style={{ width: `${rf.underdog_win_pct}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Finish Types */}
        {finishTypes.length > 0 && (
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Fight Finish Analysis
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Decision rates and finish types by weight class
            </p>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {finishTypes.map((ft) => (
                <div
                  key={ft.weight_class}
                  className="border rounded-lg p-3 hover:border-primary/50 transition-colors"
                >
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-sm">{ft.weight_class}</h3>
                    <span className="text-xs bg-muted px-2 py-1 rounded">
                      {ft.total_fights} fights
                    </span>
                  </div>

                  {/* Finish Type Breakdown */}
                  <div className="grid grid-cols-3 gap-2 text-center text-xs mb-2">
                    <div>
                      <div className="font-bold text-blue-500">
                        {ft.decision_pct}%
                      </div>
                      <div className="text-muted-foreground">Decisions</div>
                    </div>
                    <div>
                      <div className="font-bold text-red-500">
                        {ft.knockout_pct}%
                      </div>
                      <div className="text-muted-foreground">KO/TKO</div>
                    </div>
                    <div>
                      <div className="font-bold text-purple-500">
                        {ft.submission_pct}%
                      </div>
                      <div className="text-muted-foreground">Subs</div>
                    </div>
                  </div>

                  {/* Finish Rate */}
                  <div className="text-center py-1 bg-muted rounded text-xs">
                    <span className="font-semibold">
                      {ft.finish_pct}% Finish Rate
                    </span>
                    {ft.finish_pct > 60
                      ? " 🔥"
                      : ft.finish_pct < 40
                      ? " ⏱️"
                      : ""}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Card-by-Card Breakdown */}
      {cards.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-2xl font-bold mb-6">
            Card-by-Card Results ({cards.length} events)
          </h2>

          <div className="space-y-4">
            {cards.map((card) => (
              <div
                key={card.event_id}
                className="border-2 rounded-lg p-5 hover:border-primary/50 hover:shadow-xl transition-all"
              >
                {/* Card Header */}
                <div className="mb-4">
                  <h3 className="text-lg font-bold">{card.event_name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {new Date(card.date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })}{" "}
                    • {card.fights_with_odds} fights with odds
                  </p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Total Fights */}
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <div className="text-3xl font-bold">{card.fights_with_odds}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Total Fights
                    </div>
                  </div>

                  {/* Favorites */}
                  <div className="text-center p-4 bg-green-500/10 rounded-lg">
                    <div className="text-3xl font-bold text-green-500">
                      {card.favorite_wins}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Favorites Won
                    </div>
                    <div className="text-sm font-semibold text-green-500 mt-1">
                      {card.favorite_win_pct}%
                    </div>
                  </div>

                  {/* Underdogs */}
                  <div className="text-center p-4 bg-red-500/10 rounded-lg">
                    <div className="text-3xl font-bold text-red-500">
                      {card.underdog_wins}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Underdogs Won
                    </div>
                    <div className="text-sm font-semibold text-red-500 mt-1">
                      {card.underdog_win_pct}%
                    </div>
                  </div>

                  {/* Insight */}
                  <div
                    className={`text-center p-4 rounded-lg ${
                      card.underdog_wins > card.favorite_wins
                        ? "bg-yellow-500/10"
                        : "bg-blue-500/10"
                    }`}
                  >
                    {card.underdog_wins > card.favorite_wins ? (
                      <>
                        <div className="text-2xl mb-1">🔥</div>
                        <div className="text-xs font-bold">Upset Heavy</div>
                      </>
                    ) : card.favorite_wins > card.underdog_wins * 2 ? (
                      <>
                        <div className="text-2xl mb-1">✅</div>
                        <div className="text-xs font-bold">Chalk Night</div>
                      </>
                    ) : (
                      <>
                        <div className="text-2xl mb-1">⚖️</div>
                        <div className="text-xs font-bold">Balanced</div>
                      </>
                    )}
                  </div>
                </div>

                {/* Visual Bar */}
                <div className="mt-4">
                  <div className="flex h-3 rounded-full overflow-hidden">
                    <div
                      className="bg-green-500"
                      style={{ width: `${card.favorite_win_pct}%` }}
                    />
                    <div
                      className="bg-red-500"
                      style={{ width: `${card.underdog_win_pct}%` }}
                    />
                    <div
                      className="bg-muted"
                      style={{
                        width: `${
                          100 - card.favorite_win_pct - card.underdog_win_pct
                        }%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Favorites: {card.favorite_win_pct}%</span>
                    <span>Underdogs: {card.underdog_win_pct}%</span>
                  </div>
                </div>

                {/* Finish Types */}
                <div className="mt-4 pt-4 border-t">
                  <div className="text-xs font-semibold mb-2">Fight Finishes:</div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-blue-500/10 rounded p-2">
                      <div className="font-bold text-blue-500">
                        {card.decision_pct}%
                      </div>
                      <div className="text-muted-foreground text-xs">Decisions</div>
                      <div className="text-muted-foreground text-xs">
                        ({card.decisions})
                      </div>
                    </div>
                    <div className="bg-red-500/10 rounded p-2">
                      <div className="font-bold text-red-500">
                        {card.knockout_pct}%
                      </div>
                      <div className="text-muted-foreground text-xs">KO/TKO</div>
                      <div className="text-muted-foreground text-xs">
                        ({card.knockouts})
                      </div>
                    </div>
                    <div className="bg-purple-500/10 rounded p-2">
                      <div className="font-bold text-purple-500">
                        {card.submission_pct}%
                      </div>
                      <div className="text-muted-foreground text-xs">Subs</div>
                      <div className="text-muted-foreground text-xs">
                        ({card.submissions})
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {cards.length > 0 && (
        <div className="bg-blue-500/10 border-l-4 border-blue-500 rounded-lg p-6">
          <h3 className="font-bold mb-3">
            💡 Insights from {selectedLeague.toUpperCase()} {selectedYear}
          </h3>
          <div className="space-y-2">
            <p>
              • Analyzed <strong>{cards.length} events</strong> with betting odds
            </p>
            <p>
              • Total upsets:{" "}
              <strong>
                {cards.reduce((sum, card) => sum + card.underdog_wins, 0)}
              </strong>
            </p>
            <p>
              • Total favorite wins:{" "}
              <strong>
                {cards.reduce((sum, card) => sum + card.favorite_wins, 0)}
              </strong>
            </p>
            {cards.filter((card) => card.underdog_wins > card.favorite_wins)
              .length > 0 && (
              <p className="pt-2 font-semibold text-blue-400">
                🔥{" "}
                {
                  cards.filter((card) => card.underdog_wins > card.favorite_wins)
                    .length
                }{" "}
                events had more upsets than favorites!
              </p>
            )}
          </div>
        </div>
      )}

      {/* No Data */}
      {!loading && cards.length === 0 && (
        <div className="bg-yellow-500/10 border-l-4 border-yellow-500 rounded-lg p-6">
          <h3 className="font-bold text-yellow-400 mb-2">
            ⚠️ No Data Available
          </h3>
          <p className="text-muted-foreground">
            We don't have betting odds data for {selectedLeague.toUpperCase()} in{" "}
            {selectedYear}. Try selecting a different year or league.
          </p>
        </div>
      )}
    </div>
  )
}
