"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Calendar, MapPin, Trophy, Zap, Filter } from "lucide-react"
import { eventsAPI, type Event } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [selectedPromotion, setSelectedPromotion] = useState<string>("all")

  useEffect(() => {
    const fetchYears = async () => {
      try {
        const data = await eventsAPI.getYears()
        setAvailableYears(data.years)
        if (data.years.length > 0) {
          setSelectedYear(data.years[0]) // Select most recent year by default
        }
      } catch (error) {
        console.error("Error fetching years:", error)
      }
    }
    fetchYears()
  }, [])

  useEffect(() => {
    const fetchEvents = async () => {
      if (!selectedYear) return

      setLoading(true)
      try {
        const promotion = selectedPromotion === "all" ? undefined : selectedPromotion
        const data = await eventsAPI.list({
          year: selectedYear,
          promotion,
          limit: 200
        })
        setEvents(data.events)
      } catch (error) {
        console.error("Error fetching events:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchEvents()
  }, [selectedYear, selectedPromotion])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Group events by promotion
  const ufcEvents = events.filter(e => e.promotion?.toLowerCase() === 'ufc')
  const otherEvents = events.filter(e => e.promotion?.toLowerCase() !== 'ufc')

  const displayEvents = selectedPromotion === "ufc" ? ufcEvents :
                       selectedPromotion === "other" ? otherEvents :
                       events

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="relative container mx-auto px-4 py-16">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-red-600/10 border border-red-600/20 text-red-500 px-4 py-2 rounded-full text-sm font-semibold mb-4">
              <Zap className="w-4 h-4" />
              MMA EVENTS
            </div>

            {/* Title */}
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4">
              Fight Events
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-400 mb-6">
              Browse and explore MMA events across all promotions
            </p>
          </div>
        </div>
      </section>

      {/* Filters Section */}
      <section className="py-8 bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4">
          {/* Year Selection */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Filter className="w-4 h-4" />
              <span>Filter by Year</span>
            </div>
            <div className="relative">
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
                {availableYears.map((year) => (
                  <button
                    key={year}
                    onClick={() => setSelectedYear(year)}
                    className={`px-6 py-2 rounded-lg font-semibold whitespace-nowrap transition-all ${
                      selectedYear === year
                        ? "bg-red-600 text-white shadow-lg shadow-red-600/20"
                        : "bg-slate-800 text-slate-300 hover:bg-slate-750 border border-slate-700"
                    }`}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>

            {/* Promotion Tabs */}
            <Tabs value={selectedPromotion} onValueChange={setSelectedPromotion}>
              <TabsList className="grid w-full max-w-md grid-cols-3 bg-slate-900 border border-slate-800">
                <TabsTrigger
                  value="all"
                  className="data-[state=active]:bg-red-600 data-[state=active]:text-white"
                >
                  All ({events.length})
                </TabsTrigger>
                <TabsTrigger
                  value="ufc"
                  className="data-[state=active]:bg-red-600 data-[state=active]:text-white"
                >
                  UFC ({ufcEvents.length})
                </TabsTrigger>
                <TabsTrigger
                  value="other"
                  className="data-[state=active]:bg-red-600 data-[state=active]:text-white"
                >
                  Other ({otherEvents.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </section>

      {/* Events List Section */}
      <section className="py-12">
        <div className="container mx-auto px-4">
          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <Card key={i} className="bg-slate-900 border-slate-800">
                  <CardContent className="p-6">
                    <Skeleton className="h-6 w-20 mb-3 bg-slate-800" />
                    <Skeleton className="h-6 w-3/4 mb-3 bg-slate-800" />
                    <Skeleton className="h-4 w-1/2 mb-2 bg-slate-800" />
                    <Skeleton className="h-4 w-2/3 bg-slate-800" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : displayEvents.length === 0 ? (
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-12 text-center">
                <Trophy className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                <h3 className="text-lg font-semibold text-white mb-2">No Events Found</h3>
                <p className="text-slate-400">
                  No events found for {selectedYear} in this category.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Event Count */}
              <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
                <Trophy className="w-4 h-4" />
                <span>
                  {displayEvents.length} event{displayEvents.length !== 1 ? 's' : ''} in {selectedYear}
                </span>
              </div>

              {/* Events Grid */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {displayEvents.map((event) => (
                  <Link
                    key={event.id}
                    href={`/events/${event.id}`}
                    className="group"
                  >
                    <Card className="h-full bg-slate-900 border-slate-800 hover:border-red-600 transition-all hover:shadow-lg hover:shadow-red-600/10">
                      <CardContent className="p-6">
                        {/* Promotion Badge */}
                        {event.promotion && (
                          <Badge
                            className={`mb-3 ${
                              event.promotion.toLowerCase() === 'ufc'
                                ? 'bg-red-600 text-white hover:bg-red-700'
                                : 'bg-slate-800 text-slate-300 border border-slate-700'
                            }`}
                          >
                            {event.promotion.toUpperCase()}
                          </Badge>
                        )}

                        {/* Event Name */}
                        <h3 className="text-lg font-bold text-white mb-3 group-hover:text-red-500 transition-colors line-clamp-2">
                          {event.name}
                        </h3>

                        {/* Event Details */}
                        <div className="space-y-2 text-sm text-slate-400">
                          {event.date && (
                            <div className="flex items-center gap-2">
                              <Calendar className="w-4 h-4 text-slate-500" />
                              <span>{formatDate(event.date)}</span>
                            </div>
                          )}
                          {event.location && (
                            <div className="flex items-center gap-2">
                              <MapPin className="w-4 h-4 text-slate-500" />
                              <span className="line-clamp-1">{event.location}</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  )
}
