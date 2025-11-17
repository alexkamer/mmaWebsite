"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Calendar, MapPin, Trophy } from "lucide-react"
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
        // Deduplicate events by ID to fix React key warnings
        const uniqueEvents = data.events.filter((event, index, self) =>
          index === self.findIndex((e) => e.id === event.id)
        )
        setEvents(uniqueEvents)
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
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <h1 className="text-4xl font-bold">Fight Events</h1>
        <p className="text-muted-foreground">Browse MMA events by year and promotion</p>
      </div>

      {/* Year Selection - Horizontal Scrollable */}
      <div className="space-y-2">
        <h2 className="text-sm font-medium text-muted-foreground">Select Year</h2>
        <div className="relative">
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {availableYears.map((year) => (
              <button
                key={year}
                onClick={() => setSelectedYear(year)}
                className={`px-6 py-2 rounded-lg font-semibold whitespace-nowrap transition-all ${
                  selectedYear === year
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "bg-muted hover:bg-muted/80"
                }`}
              >
                {year}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Promotion Tabs */}
      <Tabs value={selectedPromotion} onValueChange={setSelectedPromotion}>
        <TabsList className="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="all">All Events</TabsTrigger>
          <TabsTrigger value="ufc">
            UFC ({ufcEvents.length})
          </TabsTrigger>
          <TabsTrigger value="other">
            Other ({otherEvents.length})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Events List */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-3/4 mb-3" />
                <Skeleton className="h-4 w-1/2 mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : displayEvents.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Events Found</h3>
            <p className="text-muted-foreground">
              No events found for {selectedYear} in this category.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Event Count */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
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
                <Card className="h-full transition-all hover:shadow-lg hover:border-primary/50">
                  <CardContent className="p-6">
                    {/* Promotion Badge */}
                    {event.promotion && (
                      <Badge
                        variant={event.promotion.toLowerCase() === 'ufc' ? 'default' : 'secondary'}
                        className="mb-3"
                      >
                        {event.promotion.toUpperCase()}
                      </Badge>
                    )}

                    {/* Event Name */}
                    <h3 className="text-lg font-bold mb-3 group-hover:text-primary transition-colors line-clamp-2">
                      {event.name}
                    </h3>

                    {/* Event Details */}
                    <div className="space-y-2 text-sm text-muted-foreground">
                      {event.date && (
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(event.date)}</span>
                        </div>
                      )}
                      {event.location && (
                        <div className="flex items-center gap-2">
                          <MapPin className="w-4 h-4" />
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
  )
}
