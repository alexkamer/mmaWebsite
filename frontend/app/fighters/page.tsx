"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import Link from "next/link"
import Image from "next/image"
import { useRouter, useSearchParams } from "next/navigation"
import { Scale, Check } from "lucide-react"
import { fightersAPI, type FighterBase } from "@/lib/api"
import { FighterSearch } from "@/components/fighter-search"
import { FighterAvatar } from "@/components/fighter-avatar"
import { FighterListSkeleton } from "@/components/skeletons"
import { FighterFilters } from "@/components/fighter-filters"

export default function FightersPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [fighters, setFighters] = useState<FighterBase[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [compareMode, setCompareMode] = useState(false)
  const [selectedFighters, setSelectedFighters] = useState<number[]>([])
  const [selectedLetter, setSelectedLetter] = useState<string>("")

  // Filter state
  const [filterOptions, setFilterOptions] = useState<{
    weightClasses: Array<{ value: string; label: string; count: number }>
    countries: Array<{ value: string; label: string; count: number }>
  }>({ weightClasses: [], countries: [] })
  const [selectedWeightClasses, setSelectedWeightClasses] = useState<string[]>([])
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])

  const pageSize = 24
  const observerTarget = useRef<HTMLDivElement>(null)

  // Load filter options on mount
  useEffect(() => {
    const fetchFilterOptions = async () => {
      try {
        const data = await fightersAPI.getFilters()
        setFilterOptions({
          weightClasses: data.weight_classes.map(wc => ({
            value: wc.weight_class || '',
            label: wc.weight_class || '',
            count: wc.count
          })),
          countries: data.nationalities.map(nat => ({
            value: nat.nationality || '',
            label: nat.nationality || '',
            count: nat.count
          }))
        })
      } catch (error) {
        console.error("Error fetching filter options:", error)
      }
    }
    fetchFilterOptions()
  }, [])

  // Load filters from URL on mount
  useEffect(() => {
    const wcParam = searchParams.get('weight_classes')
    const countryParam = searchParams.get('nationality')

    if (wcParam) {
      setSelectedWeightClasses(wcParam.split(','))
    }
    if (countryParam) {
      setSelectedCountries([countryParam])
    }
  }, [searchParams])

  // Fetch fighters when page or filters change
  useEffect(() => {
    const fetchFighters = async () => {
      setLoading(true)
      try {
        const data = await fightersAPI.list({
          page,
          page_size: pageSize,
          weight_classes: selectedWeightClasses.length > 0 ? selectedWeightClasses : undefined,
          nationality: selectedCountries.length > 0 ? selectedCountries[0] : undefined,
          starts_with: selectedLetter || undefined,
        })

        // For infinite scroll: append if page > 1, replace if page === 1
        if (page === 1) {
          setFighters(data.fighters)
        } else {
          setFighters(prev => [...prev, ...data.fighters])
        }

        setTotal(data.total)
        setHasMore(data.fighters.length === pageSize)
      } catch (error) {
        console.error("Error fetching fighters:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchFighters()
  }, [page, selectedWeightClasses, selectedCountries, selectedLetter])

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams()
    if (selectedWeightClasses.length > 0) {
      params.set('weight_classes', selectedWeightClasses.join(','))
    }
    if (selectedCountries.length > 0) {
      params.set('nationality', selectedCountries[0])
    }

    const newUrl = params.toString() ? `/fighters?${params}` : '/fighters'
    router.replace(newUrl, { scroll: false })
  }, [selectedWeightClasses, selectedCountries, router])

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          setPage(prev => prev + 1)
        }
      },
      { threshold: 0.1 }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [hasMore, loading])

  const totalPages = Math.ceil(total / pageSize)

  const handleLetterClick = (letter: string) => {
    setSelectedLetter(letter === selectedLetter ? "" : letter)
    setPage(1)
    setFighters([])
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

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

  const handleClearFilters = () => {
    setSelectedWeightClasses([])
    setSelectedCountries([])
    setSelectedLetter("")
    setPage(1)
    setFighters([])
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
      {!compareMode && <FighterSearch />}

      {/* Filters */}
      {!compareMode && (
        <FighterFilters
          weightClasses={filterOptions.weightClasses}
          promotions={[]}
          countries={filterOptions.countries}
          selectedWeightClasses={selectedWeightClasses}
          selectedPromotions={[]}
          selectedCountries={selectedCountries}
          onWeightClassChange={setSelectedWeightClasses}
          onPromotionChange={() => {}}
          onCountryChange={setSelectedCountries}
          onClearAll={handleClearFilters}
        />
      )}

      {/* Alphabet Navigation */}
      {!compareMode && (
        <div className="flex flex-wrap gap-1 justify-center">
          {Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZ').map((letter) => (
            <button
              key={letter}
              onClick={() => handleLetterClick(letter)}
              className={`h-9 w-9 rounded-lg text-sm font-medium transition-colors ${
                selectedLetter === letter
                  ? 'bg-blue-600 text-white'
                  : 'border bg-background hover:bg-muted'
              }`}
            >
              {letter}
            </button>
          ))}
          {selectedLetter && (
            <button
              onClick={() => handleLetterClick("")}
              className="px-4 py-2 rounded-lg border bg-background hover:bg-muted text-sm font-medium transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Loading State - Only show on initial load */}
      {loading && page === 1 && fighters.length === 0 ? (
        <FighterListSkeleton count={24} />
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
                        <div className="flex items-center gap-2 text-xs">
                          {fighter.weight_class && (
                            <span className="text-muted-foreground">
                              {fighter.weight_class}
                            </span>
                          )}
                          {(fighter.wins !== undefined || fighter.losses !== undefined) && (
                            <>
                              {fighter.weight_class && (
                                <span className="text-muted-foreground">•</span>
                              )}
                              <span className="font-medium">
                                {fighter.wins || 0}-{fighter.losses || 0}
                                {fighter.draws ? `-${fighter.draws}` : ''}
                              </span>
                            </>
                          )}
                        </div>
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
                      <div className="flex items-center gap-2 text-xs">
                        {fighter.weight_class && (
                          <span className="text-muted-foreground">
                            {fighter.weight_class}
                          </span>
                        )}
                        {(fighter.wins !== undefined || fighter.losses !== undefined) && (
                          <>
                            {fighter.weight_class && (
                              <span className="text-muted-foreground">•</span>
                            )}
                            <span className="font-medium">
                              {fighter.wins || 0}-{fighter.losses || 0}
                              {fighter.draws ? `-${fighter.draws}` : ''}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-12 text-center">
              <p className="text-muted-foreground">
                No fighters found
              </p>
            </div>
          )}

          {/* Infinite Scroll Loader */}
          {hasMore && (
            <div ref={observerTarget} className="flex items-center justify-center py-8">
              {loading && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  <span className="text-sm">Loading more fighters...</span>
                </div>
              )}
            </div>
          )}
          {!hasMore && fighters.length > 0 && (
            <div className="text-center py-8 text-sm text-muted-foreground">
              Showing all {fighters.length} fighters
            </div>
          )}
        </>
      )}
    </div>
  )
}
