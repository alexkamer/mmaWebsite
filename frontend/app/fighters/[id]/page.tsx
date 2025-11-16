"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { fightersAPI, type FighterDetail, type Fight } from "@/lib/api"

export default function FighterProfilePage() {
  const params = useParams()
  const fighterId = parseInt(params.id as string)

  const [fighter, setFighter] = useState<FighterDetail | null>(null)
  const [fights, setFights] = useState<Fight[]>([])
  const [loading, setLoading] = useState(true)

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
          <div className="flex-shrink-0">
            {fighter.image_url ? (
              <img
                src={fighter.image_url}
                alt={fighter.name}
                className="h-48 w-48 rounded-lg object-cover"
              />
            ) : (
              <div className="flex h-48 w-48 items-center justify-center rounded-lg bg-gray-800 text-6xl font-bold">
                {fighter.name.charAt(0)}
              </div>
            )}
          </div>

          {/* Fighter Info */}
          <div className="flex-1 space-y-4">
            <div>
              <h1 className="text-4xl font-bold">{fighter.name}</h1>
              {fighter.nickname && (
                <p className="text-xl text-gray-400">"{fighter.nickname}"</p>
              )}
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
            </div>
          </div>
        </div>
      </div>

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
