"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Scale, Search } from "lucide-react"
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
    <div className="space-y-8">
      {/* Back Button */}
      <Link
        href="/fighters"
        className="inline-flex items-center gap-2 text-sm hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to fighters
      </Link>

      {/* Fighter Header */}
      <div className="rounded-lg border bg-gray-900 p-8">
        <div className="flex flex-col gap-8 md:flex-row md:items-start">
          {/* Fighter Image */}
          <div className="flex-shrink-0 relative">
            {/* Country Flag Background */}
            {fighter.flag_url && !fighter.flag_url.includes('blank.png') && (
              <div className="absolute inset-0 rounded-lg overflow-hidden opacity-30">
                <img
                  src={fighter.flag_url}
                  alt={fighter.nationality || 'Country flag'}
                  className="h-full w-full object-cover scale-150"
                />
              </div>
            )}

            {/* Fighter Image */}
            {fighter.image_url ? (
              <img
                src={fighter.image_url}
                alt={fighter.name}
                className="relative h-48 w-48 rounded-lg object-cover"
              />
            ) : (
              <div className="relative flex h-48 w-48 items-center justify-center rounded-lg bg-gray-800 text-6xl font-bold">
                {fighter.name.charAt(0)}
              </div>
            )}
          </div>

          {/* Fighter Info */}
          <div className="flex-1 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-4xl font-bold">{fighter.name}</h1>
                {fighter.nickname && (
                  <p className="text-xl text-gray-400">"{fighter.nickname}"</p>
                )}
              </div>

              {/* Compare Button */}
              <button
                onClick={() => setShowCompareModal(true)}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
              >
                <Scale className="h-4 w-4" />
                Compare Fighter
              </button>
            </div>

            {/* Record */}
            <div className="text-2xl font-semibold">
              Record: <span className="text-green-400">{record}</span>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {fighter.weight_class && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Weight Class</div>
                  <div className="font-semibold">{fighter.weight_class}</div>
                </div>
              )}
              {fighter.height && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Height</div>
                  <div className="font-semibold">{fighter.height}</div>
                </div>
              )}
              {fighter.weight && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Weight</div>
                  <div className="font-semibold">{fighter.weight}</div>
                </div>
              )}
              {fighter.reach && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Reach</div>
                  <div className="font-semibold">{fighter.reach}</div>
                </div>
              )}
              {fighter.stance && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Stance</div>
                  <div className="font-semibold">{fighter.stance}</div>
                </div>
              )}
              {fighter.nationality && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Nationality</div>
                  <div className="font-semibold">{fighter.nationality}</div>
                </div>
              )}
              {fighter.team && (
                <div className="rounded border bg-gray-800 p-3">
                  <div className="text-sm text-gray-400">Team</div>
                  <div className="font-semibold">{fighter.team}</div>
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

      {/* Fight History */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Fight History</h2>

        {fights.length > 0 ? (
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full">
              <thead className="border-b bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Result
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Opponent
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Method
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Round
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Event
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody>
                {fights.map((fight, idx) => (
                  <tr
                    key={fight.id}
                    className={`border-b ${
                      idx % 2 === 0 ? "bg-gray-900/50" : ""
                    }`}
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded px-2 py-1 text-xs font-semibold ${
                          fight.result === "win"
                            ? "bg-green-900 text-green-300"
                            : fight.result === "loss"
                            ? "bg-red-900 text-red-300"
                            : "bg-gray-700 text-gray-300"
                        }`}
                      >
                        {fight.result.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/fighters/${fight.opponent_id}`}
                        className="hover:underline"
                      >
                        {fight.opponent_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {fight.method}
                      {fight.method_detail && ` (${fight.method_detail})`}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {fight.round && fight.time
                        ? `R${fight.round} ${fight.time}`
                        : fight.round
                        ? `R${fight.round}`
                        : "-"}
                    </td>
                    <td className="px-4 py-3 text-sm">{fight.event_name}</td>
                    <td className="px-4 py-3 text-sm">
                      {fight.date
                        ? new Date(fight.date).toLocaleDateString()
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-lg border bg-gray-900 p-8 text-center text-gray-400">
            No fight history available
          </div>
        )}
      </div>
    </div>
  )
}
