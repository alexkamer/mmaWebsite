"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Search, Scale, Check } from "lucide-react"
import { fightersAPI, type FighterBase } from "@/lib/api"

export default function FightersPage() {
  const router = useRouter()
  const [fighters, setFighters] = useState<FighterBase[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [compareMode, setCompareMode] = useState(false)
  const [selectedFighters, setSelectedFighters] = useState<number[]>([])
  const pageSize = 24

  useEffect(() => {
    const fetchFighters = async () => {
      setLoading(true)
      try {
        const data = await fightersAPI.list({
          page,
          page_size: pageSize,
          search: search || undefined,
        })
        setFighters(data.fighters)
        setTotal(data.total)
      } catch (error) {
        console.error("Error fetching fighters:", error)
      } finally {
        setLoading(false)
      }
    }

    const debounce = setTimeout(() => {
      fetchFighters()
    }, 300)

    return () => clearTimeout(debounce)
  }, [search, page])

  const totalPages = Math.ceil(total / pageSize)

  const toggleFighterSelection = (fighterId: number) => {
    setSelectedFighters(prev => {
      if (prev.includes(fighterId)) {
        return prev.filter(id => id !== fighterId)
      }
      if (prev.length < 2) {
        return [...prev, fighterId]
      }
      return prev
    })
  }

  const handleCompare = () => {
    if (selectedFighters.length === 2) {
      router.push(`/fighters/compare?fighter1=${selectedFighters[0]}&fighter2=${selectedFighters[1]}`)
    }
  }

  const handleCancelCompare = () => {
    setCompareMode(false)
    setSelectedFighters([])
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">Fighters</h1>
          <p className="text-muted-foreground">
            Browse {total.toLocaleString()} fighters from around the world
          </p>
        </div>

        {!compareMode ? (
          <button
            onClick={() => setCompareMode(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
          >
            <Scale className="h-4 w-4" />
            Compare Fighters
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <div className="text-sm text-muted-foreground">
              {selectedFighters.length}/2 selected
            </div>
            <button
              onClick={handleCompare}
              disabled={selectedFighters.length !== 2}
              className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Scale className="h-4 w-4" />
              Compare
            </button>
            <button
              onClick={handleCancelCompare}
              className="rounded-lg border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search fighters..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(1)
          }}
          className="w-full rounded-lg border bg-background px-10 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-lg border bg-muted"
            />
          ))}
        </div>
      ) : (
        <>
          {/* Fighters Grid */}
          {fighters.length > 0 ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {fighters.map((fighter) => {
                const isSelected = selectedFighters.includes(fighter.id)
                const isSelectable = compareMode && (isSelected || selectedFighters.length < 2)

                if (compareMode) {
                  return (
                    <button
                      key={fighter.id}
                      onClick={() => toggleFighterSelection(fighter.id)}
                      disabled={!isSelectable}
                      className={`group relative overflow-hidden rounded-lg border bg-card text-left transition-all hover:shadow-lg ${
                        isSelected ? 'ring-2 ring-blue-500' : ''
                      } ${!isSelectable ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {/* Selection Indicator */}
                      {isSelected && (
                        <div className="absolute top-2 right-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-white">
                          <Check className="h-4 w-4" />
                        </div>
                      )}

                      {/* Fighter Image */}
                      <div className="relative aspect-square overflow-hidden bg-muted">
                        {fighter.image_url ? (
                          <Image
                            src={fighter.image_url}
                            alt={fighter.name}
                            fill
                            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1280px) 33vw, 25vw"
                            className="object-cover transition-transform group-hover:scale-105"
                            priority={false}
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center text-6xl font-bold text-muted-foreground">
                            {fighter.name.charAt(0)}
                          </div>
                        )}
                      </div>

                      {/* Fighter Info */}
                      <div className="p-4 space-y-1">
                        <h3 className="font-semibold line-clamp-1">
                          {fighter.name}
                        </h3>
                        {fighter.nickname && (
                          <p className="text-sm text-muted-foreground line-clamp-1">
                            "{fighter.nickname}"
                          </p>
                        )}
                        {fighter.weight_class && (
                          <p className="text-xs text-muted-foreground">
                            {fighter.weight_class}
                          </p>
                        )}
                      </div>
                    </button>
                  )
                }

                return (
                  <Link
                    key={fighter.id}
                    href={`/fighters/${fighter.id}`}
                    className="group relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-lg"
                  >
                    {/* Fighter Image */}
                    <div className="relative aspect-square overflow-hidden bg-muted">
                      {fighter.image_url ? (
                        <Image
                          src={fighter.image_url}
                          alt={fighter.name}
                          fill
                          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, (max-width: 1280px) 33vw, 25vw"
                          className="object-cover transition-transform group-hover:scale-105"
                          priority={false}
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center text-6xl font-bold text-muted-foreground">
                          {fighter.name.charAt(0)}
                        </div>
                      )}
                    </div>

                    {/* Fighter Info */}
                    <div className="p-4 space-y-1">
                      <h3 className="font-semibold line-clamp-1">
                        {fighter.name}
                      </h3>
                      {fighter.nickname && (
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          "{fighter.nickname}"
                        </p>
                      )}
                      {fighter.weight_class && (
                        <p className="text-xs text-muted-foreground">
                          {fighter.weight_class}
                        </p>
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-12 text-center">
              <p className="text-muted-foreground">
                No fighters found matching "{search}"
              </p>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="rounded-lg border bg-background px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="rounded-lg border bg-background px-4 py-2 text-sm font-medium disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
