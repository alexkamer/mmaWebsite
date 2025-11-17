"use client"

import { useState, useEffect, useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Scale, Search, Weight, Ruler, Maximize2, Activity, Users, Flag, Calendar, TrendingUp, TrendingDown, Minus, Target, Clock, Zap } from "lucide-react"
import { fightersAPI, type FighterDetail, type Fight, type FighterBase } from "@/lib/api"

export default function FighterProfilePage() {
  const params = useParams()
  const router = useRouter()
  const fighterId = parseInt(params.id as string)

  const [fighter, setFighter] = useState<FighterDetail | null>(null)
  const [fights, setFights] = useState<Fight[]>([])
  const [loading, setLoading] = useState(true)
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<FighterBase[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [resultFilter, setResultFilter] = useState<'all' | 'win' | 'loss' | 'draw'>('all')
  const [promotionFilter, setPromotionFilter] = useState<string>('all')

  useEffect(() => {
    const fetchFighter = async () => {
      setLoading(true)
      try {
        const [fighterData, fightsData] = await Promise.all([
          fightersAPI.get(fighterId),
          fightersAPI.getFights(fighterId),
        ])
        setFighter(fighterData)
        setFights(fightsData.fights)
      } catch (error) {
        console.error("Error fetching fighter:", error)
      } finally {
        setLoading(false)
      }
    }

    if (fighterId) {
      fetchFighter()
    }
  }, [fighterId])

  useEffect(() => {
    const searchFighters = async () => {
      if (searchQuery.length < 2) {
        setSearchResults([])
        return
      }

      setSearchLoading(true)
      try {
        const data = await fightersAPI.list({ search: searchQuery, page_size: 10 })
        // Filter out current fighter
        setSearchResults(data.fighters.filter(f => f.id !== fighterId))
      } catch (error) {
        console.error("Error searching fighters:", error)
      } finally {
        setSearchLoading(false)
      }
    }

    const debounce = setTimeout(() => {
      searchFighters()
    }, 300)

    return () => clearTimeout(debounce)
  }, [searchQuery, fighterId])

  const handleCompare = (opponentId: number) => {
    router.push(`/fighters/compare?fighter1=${fighterId}&fighter2=${opponentId}`)
  }

  // Get unique promotions from fights - must be called before any early returns
  const promotions = useMemo(() => {
    const uniquePromotions = new Set<string>()
    fights.forEach(fight => {
      if (fight.event_name) {
        // Extract promotion name (e.g., "UFC", "Bellator", "PFL" from event names)
        const eventName = fight.event_name
        if (eventName.startsWith('UFC')) uniquePromotions.add('UFC')
        else if (eventName.startsWith('Bellator')) uniquePromotions.add('Bellator')
        else if (eventName.startsWith('PFL')) uniquePromotions.add('PFL')
        else if (eventName.startsWith('Strikeforce')) uniquePromotions.add('Strikeforce')
        else if (eventName.startsWith('Pride')) uniquePromotions.add('Pride')
        else if (eventName.startsWith('ONE')) uniquePromotions.add('ONE Championship')
        else uniquePromotions.add('Other')
      }
    })
    return Array.from(uniquePromotions).sort()
  }, [fights])

  // Calculate win streak - must be called before any early returns
  const calculateStreak = () => {
    if (fights.length === 0) return { type: 'none', count: 0 }

    let streak = 0
    const firstResult = fights[0].result

    for (const fight of fights) {
      if (fight.result === firstResult) {
        streak++
      } else {
        break
      }
    }

    return { type: firstResult, count: streak }
  }

  const streak = calculateStreak()

  // Filter fights based on active filters
  const filteredFights = useMemo(() => {
    return fights.filter(fight => {
      // Filter by result
      if (resultFilter !== 'all' && fight.result !== resultFilter) return false

      // Filter by promotion
      if (promotionFilter !== 'all' && fight.event_name) {
        const eventName = fight.event_name
        let fightPromotion = 'Other'
        if (eventName.startsWith('UFC')) fightPromotion = 'UFC'
        else if (eventName.startsWith('Bellator')) fightPromotion = 'Bellator'
        else if (eventName.startsWith('PFL')) fightPromotion = 'PFL'
        else if (eventName.startsWith('Strikeforce')) fightPromotion = 'Strikeforce'
        else if (eventName.startsWith('Pride')) fightPromotion = 'Pride'
        else if (eventName.startsWith('ONE')) fightPromotion = 'ONE Championship'

        if (fightPromotion !== promotionFilter) return false
      }

      return true
    })
  }, [fights, resultFilter, promotionFilter])

  // Calculate fight statistics based on filtered fights
  const fightStats = useMemo(() => {
    if (filteredFights.length === 0) return null

    const stats = {
      totalFights: filteredFights.length,
      finishes: 0,
      decisions: 0,
      koTko: 0,
      submissions: 0,
      avgFightTime: 0,
      firstRoundFinishes: 0,
      wentDistance: 0
    }

    let totalMinutes = 0
    let fightsCounted = 0

    filteredFights.forEach(fight => {
      const method = fight.method?.toLowerCase() || ''

      // Count finish types
      if (method.includes('ko') || method.includes('tko')) {
        stats.koTko++
        stats.finishes++
      } else if (method.includes('submission')) {
        stats.submissions++
        stats.finishes++
      } else if (method.includes('decision')) {
        stats.decisions++
      }

      // Count first round finishes
      if (fight.round === 1 && !method.includes('decision')) {
        stats.firstRoundFinishes++
      }

      // Count fights that went the distance (decision)
      if (method.includes('decision')) {
        stats.wentDistance++
      }

      // Calculate average fight time
      if (fight.round && fight.time) {
        const [minutes, seconds] = fight.time.split(':').map(Number)
        const roundTime = (fight.round - 1) * 5 + minutes + (seconds || 0) / 60
        totalMinutes += roundTime
        fightsCounted++
      }
    })

    if (fightsCounted > 0) {
      stats.avgFightTime = totalMinutes / fightsCounted
    }

    return stats
  }, [filteredFights])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-700" />
        <div className="h-64 animate-pulse rounded-lg bg-gray-700" />
        <div className="h-96 animate-pulse rounded-lg bg-gray-700" />
      </div>
    )
  }

  if (!fighter) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">Fighter not found</h1>
        <Link href="/fighters" className="text-blue-500 hover:underline">
          Back to fighters
        </Link>
      </div>
    )
  }

  const record = `${fighter.wins || 0}-${fighter.losses || 0}-${fighter.draws || 0}`

  return (
    <div className="space-y-8 pb-8">
      {/* Back Button */}
      <Link
        href="/fighters"
        className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to fighters
      </Link>

      {/* Hero Section - Split Screen Design */}
      <div className="relative overflow-hidden rounded-2xl border border-gray-800 bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 shadow-2xl">
        <div className="grid md:grid-cols-5 gap-0">
          {/* Left Side - Fighter Image */}
          <div className="md:col-span-2 relative bg-gradient-to-br from-blue-900/20 to-purple-900/20">
            {/* Background Flag - Subtle */}
            {fighter.flag_url && !fighter.flag_url.includes('blank.png') && (
              <div className="absolute inset-0 overflow-hidden opacity-10">
                <img
                  src={fighter.flag_url}
                  alt={fighter.nationality || 'Country flag'}
                  className="h-full w-full object-cover scale-150 blur-sm"
                />
              </div>
            )}

            {/* Fighter Image */}
            <div className="relative h-full min-h-[400px] md:min-h-[500px] flex items-end justify-center p-8">
              {fighter.image_url ? (
                <img
                  src={fighter.image_url}
                  alt={fighter.name}
                  className="relative h-full w-full object-contain object-bottom"
                />
              ) : (
                <div className="flex h-64 w-64 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-8xl font-bold shadow-2xl">
                  {fighter.name.charAt(0)}
                </div>
              )}
            </div>
          </div>

          {/* Right Side - Fighter Info */}
          <div className="md:col-span-3 p-8 md:p-12 space-y-6">
            {/* Header with Compare Button */}
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="space-y-2">
                <div className="flex items-center gap-3 flex-wrap">
                  <h1 className="text-4xl md:text-5xl font-bold tracking-tight">{fighter.name}</h1>
                  {fighter.flag_url && !fighter.flag_url.includes('blank.png') && (
                    <img
                      src={fighter.flag_url}
                      alt={fighter.nationality || 'Country flag'}
                      className="h-8 w-12 rounded shadow-md object-cover"
                    />
                  )}
                </div>
                {fighter.nickname && (
                  <p className="text-xl md:text-2xl text-gray-400 italic">"{fighter.nickname}"</p>
                )}
              </div>

              {/* Compare Button */}
              <button
                onClick={() => setShowCompareModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-all hover:shadow-lg hover:shadow-blue-600/50"
              >
                <Scale className="h-4 w-4" />
                Compare
              </button>
            </div>

            {/* Record - Large and Prominent */}
            <div className="flex items-baseline gap-3 flex-wrap">
              <span className="text-lg text-gray-400">Record:</span>
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-green-400">{fighter.wins || 0}</span>
                <span className="text-3xl text-gray-500">-</span>
                <span className="text-5xl font-bold text-red-400">{fighter.losses || 0}</span>
                {(fighter.draws || 0) > 0 && (
                  <>
                    <span className="text-3xl text-gray-500">-</span>
                    <span className="text-5xl font-bold text-gray-400">{fighter.draws}</span>
                  </>
                )}
              </div>

              {/* Win Streak Badge */}
              {streak.count > 1 && (
                <div className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${
                  streak.type === 'win'
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : streak.type === 'loss'
                    ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                    : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                }`}>
                  {streak.type === 'win' ? <TrendingUp className="h-3.5 w-3.5" /> : streak.type === 'loss' ? <TrendingDown className="h-3.5 w-3.5" /> : <Minus className="h-3.5 w-3.5" />}
                  {streak.count} {streak.type} streak
                </div>
              )}
            </div>

            {/* Quick Stats - Icon-Based Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 pt-4">
              {fighter.weight_class && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Weight className="h-3.5 w-3.5" />
                    <span>Weight Class</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.weight_class}</div>
                </div>
              )}

              {fighter.height && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Ruler className="h-3.5 w-3.5" />
                    <span>Height</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.height}</div>
                </div>
              )}

              {fighter.weight && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Weight className="h-3.5 w-3.5" />
                    <span>Weight</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.weight}</div>
                </div>
              )}

              {fighter.reach && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Maximize2 className="h-3.5 w-3.5" />
                    <span>Reach</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.reach}"</div>
                </div>
              )}

              {fighter.stance && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Activity className="h-3.5 w-3.5" />
                    <span>Stance</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.stance}</div>
                </div>
              )}

              {fighter.nationality && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Flag className="h-3.5 w-3.5" />
                    <span>Nationality</span>
                  </div>
                  <div className="font-bold text-lg text-white">{fighter.nationality}</div>
                </div>
              )}

              {fighter.team && (
                <div className="group rounded-xl border border-gray-800 bg-gray-900/50 p-4 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10 sm:col-span-2 lg:col-span-1">
                  <div className="flex items-center gap-2 text-gray-400 text-xs mb-1.5">
                    <Users className="h-3.5 w-3.5" />
                    <span>Team</span>
                  </div>
                  <div className="font-bold text-lg text-white truncate">{fighter.team}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Compare Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-lg border bg-gray-900 p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Compare {fighter.name} with...</h2>
              <button
                onClick={() => {
                  setShowCompareModal(false)
                  setSearchQuery("")
                  setSearchResults([])
                }}
                className="text-2xl text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            {/* Search Input */}
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a fighter..."
                className="w-full rounded-lg border bg-gray-800 py-2 pl-10 pr-4 text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
                autoFocus
              />
            </div>

            {/* Search Results */}
            <div className="max-h-96 overflow-y-auto">
              {searchLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 animate-pulse rounded bg-gray-800" />
                  ))}
                </div>
              ) : searchResults.length > 0 ? (
                <div className="space-y-2">
                  {searchResults.map((result) => (
                    <button
                      key={result.id}
                      onClick={() => handleCompare(result.id)}
                      className="flex w-full items-center gap-3 rounded-lg border border-transparent bg-gray-800 p-3 text-left hover:border-blue-500 hover:bg-gray-700 transition-colors"
                    >
                      {result.image_url ? (
                        <img
                          src={result.image_url}
                          alt={result.name}
                          className="h-12 w-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-700 text-lg font-bold">
                          {result.name.charAt(0)}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold truncate">{result.name}</div>
                        <div className="text-sm text-gray-400">
                          {result.weight_class || "Unknown weight class"}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ) : searchQuery.length >= 2 ? (
                <div className="py-8 text-center text-gray-400">
                  No fighters found
                </div>
              ) : (
                <div className="py-8 text-center text-gray-400">
                  Type at least 2 characters to search
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Fight Statistics */}
      {fightStats && fights.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold">Fight Statistics</h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Finish Rate */}
            <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-blue-600/50 hover:shadow-lg hover:shadow-blue-600/10">
              <div className="flex items-center gap-3 mb-3">
                <div className="rounded-lg bg-blue-500/20 p-2">
                  <Target className="h-5 w-5 text-blue-400" />
                </div>
                <div className="text-sm font-medium text-gray-400">Finish Rate</div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">
                {((fightStats.finishes / fightStats.totalFights) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">
                {fightStats.finishes} of {fightStats.totalFights} fights
              </div>
            </div>

            {/* KO/TKO */}
            <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-red-600/50 hover:shadow-lg hover:shadow-red-600/10">
              <div className="flex items-center gap-3 mb-3">
                <div className="rounded-lg bg-red-500/20 p-2">
                  <Zap className="h-5 w-5 text-red-400" />
                </div>
                <div className="text-sm font-medium text-gray-400">KO/TKO Wins</div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">
                {fightStats.koTko}
              </div>
              <div className="text-xs text-gray-500">
                {fightStats.koTko > 0 ? `${((fightStats.koTko / fightStats.totalFights) * 100).toFixed(0)}% of fights` : 'No KO/TKO wins'}
              </div>
            </div>

            {/* Submissions */}
            <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-purple-600/50 hover:shadow-lg hover:shadow-purple-600/10">
              <div className="flex items-center gap-3 mb-3">
                <div className="rounded-lg bg-purple-500/20 p-2">
                  <Activity className="h-5 w-5 text-purple-400" />
                </div>
                <div className="text-sm font-medium text-gray-400">Submissions</div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">
                {fightStats.submissions}
              </div>
              <div className="text-xs text-gray-500">
                {fightStats.submissions > 0 ? `${((fightStats.submissions / fightStats.totalFights) * 100).toFixed(0)}% of fights` : 'No submission wins'}
              </div>
            </div>

            {/* Decisions */}
            <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-green-600/50 hover:shadow-lg hover:shadow-green-600/10">
              <div className="flex items-center gap-3 mb-3">
                <div className="rounded-lg bg-green-500/20 p-2">
                  <Clock className="h-5 w-5 text-green-400" />
                </div>
                <div className="text-sm font-medium text-gray-400">Decisions</div>
              </div>
              <div className="text-3xl font-bold text-white mb-1">
                {fightStats.decisions}
              </div>
              <div className="text-xs text-gray-500">
                {fightStats.decisions > 0 ? `${((fightStats.decisions / fightStats.totalFights) * 100).toFixed(0)}% went the distance` : 'No decisions'}
              </div>
            </div>

            {/* Avg Fight Time */}
            {fightStats.avgFightTime > 0 && (
              <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-yellow-600/50 hover:shadow-lg hover:shadow-yellow-600/10">
                <div className="flex items-center gap-3 mb-3">
                  <div className="rounded-lg bg-yellow-500/20 p-2">
                    <Clock className="h-5 w-5 text-yellow-400" />
                  </div>
                  <div className="text-sm font-medium text-gray-400">Avg Fight Time</div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {Math.floor(fightStats.avgFightTime)}:{String(Math.round((fightStats.avgFightTime % 1) * 60)).padStart(2, '0')}
                </div>
                <div className="text-xs text-gray-500">Minutes per fight</div>
              </div>
            )}

            {/* First Round Finishes */}
            {fightStats.firstRoundFinishes > 0 && (
              <div className="group rounded-xl border border-gray-800 bg-gradient-to-br from-gray-900 to-gray-800 p-6 transition-all hover:border-orange-600/50 hover:shadow-lg hover:shadow-orange-600/10">
                <div className="flex items-center gap-3 mb-3">
                  <div className="rounded-lg bg-orange-500/20 p-2">
                    <Zap className="h-5 w-5 text-orange-400" />
                  </div>
                  <div className="text-sm font-medium text-gray-400">R1 Finishes</div>
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {fightStats.firstRoundFinishes}
                </div>
                <div className="text-xs text-gray-500">
                  {((fightStats.firstRoundFinishes / fightStats.finishes) * 100).toFixed(0)}% of finishes
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fight History */}
      <div className="space-y-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <h2 className="text-3xl font-bold">Fight History</h2>

          {/* Filters */}
          {fights.length > 0 && (
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              {/* Result Filter */}
              <div className="flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 p-1">
                {(['all', 'win', 'loss', 'draw'] as const).map((filter) => (
                  <button
                    key={filter}
                    onClick={() => setResultFilter(filter)}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                      resultFilter === filter
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    {filter === 'all' ? 'All' : filter === 'win' ? 'Wins' : filter === 'loss' ? 'Losses' : 'Draws'}
                  </button>
                ))}
              </div>

              {/* Promotion Filter */}
              {promotions.length > 1 && (
                <select
                  value={promotionFilter}
                  onChange={(e) => setPromotionFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg border border-gray-800 bg-gray-900 text-sm font-medium text-white hover:border-gray-700 focus:outline-none focus:border-blue-600"
                >
                  <option value="all">All Promotions</option>
                  {promotions.map((promo) => (
                    <option key={promo} value={promo}>
                      {promo}
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}
        </div>

        {fights.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-gray-800 shadow-xl">
            <table className="w-full">
              <thead className="border-b border-gray-800 bg-gray-900/80 backdrop-blur sticky top-0">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Result
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Opponent
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Method
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Round
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Event
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Odds
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-400">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filteredFights.map((fight, idx) => (
                  <tr
                    key={fight.id}
                    className="bg-gray-900/40 hover:bg-gray-800/60 transition-colors group"
                  >
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center rounded-full px-3 py-1.5 text-xs font-bold uppercase tracking-wide ${
                          fight.result === "win"
                            ? "bg-green-500/20 text-green-400 border border-green-500/30"
                            : fight.result === "loss"
                            ? "bg-red-500/20 text-red-400 border border-red-500/30"
                            : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                        }`}
                      >
                        {fight.result === 'win' ? 'W' : fight.result === 'loss' ? 'L' : 'D'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/fighters/${fight.opponent_id}`}
                        className="font-semibold text-white hover:text-blue-400 transition-colors flex items-center gap-2"
                      >
                        {fight.opponent_name}
                        <ArrowLeft className="h-3 w-3 rotate-180 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      <div className="font-medium">{fight.method}</div>
                      {fight.method_detail && (
                        <div className="text-xs text-gray-500">({fight.method_detail})</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-300">
                      {fight.round && fight.time
                        ? `R${fight.round} ${fight.time}`
                        : fight.round
                        ? `R${fight.round}`
                        : "-"}
                    </td>
                    <td className="px-6 py-4 text-sm max-w-xs">
                      <div className="flex items-center gap-2 flex-wrap">
                        {fight.event_id ? (
                          <Link
                            href={`/events/${fight.event_id}`}
                            className="text-gray-300 hover:text-blue-400 transition-colors truncate"
                          >
                            {fight.event_name}
                          </Link>
                        ) : (
                          <span className="text-gray-300 truncate">{fight.event_name}</span>
                        )}
                        {fight.is_title_fight && (
                          <span
                            className="inline-flex items-center rounded-md bg-yellow-500/20 px-2 py-1 text-xs font-bold text-yellow-400 border border-yellow-500/30"
                            title={fight.is_title_fight}
                          >
                            TITLE
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {fight.fighter_odds ? (
                        <span className={`font-bold ${
                          fight.fighter_odds.startsWith('-')
                            ? 'text-blue-400'
                            : 'text-orange-400'
                        }`}>
                          {fight.fighter_odds}
                        </span>
                      ) : (
                        <span className="text-gray-600">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium text-gray-400">
                      {fight.date
                        ? new Date(fight.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-12 text-center">
            <p className="text-lg text-gray-400">No fight history available</p>
          </div>
        )}
      </div>
    </div>
  )
}
