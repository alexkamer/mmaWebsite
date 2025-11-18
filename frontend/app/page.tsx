"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import Image from "next/image"
import {
  Calendar,
  MapPin,
  Globe,
  Trophy,
  TrendingUp,
  ArrowRight,
  Shield,
  Target,
  Activity,
  BarChart3
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

// Types for our homepage data
interface Event {
  id: string | number
  name: string
  date: string
  venue_name: string
  city: string
  country: string
  promotion: string
}

interface Champion {
  division: string
  full_name: string
  headshot_url: string | null
  athlete_id: number
  position: string
}

interface FeaturedFighter {
  id: number
  full_name: string
  headshot_url: string | null
  weight_class: string
  division: string
  position: string
  rank: number
  fight_count: number
}

interface HomepageData {
  recent_events: Event[]
  upcoming_events: Event[]
  current_champions: Champion[]
  featured_fighters: FeaturedFighter[]
}

export default function HomePage() {
  const [data, setData] = useState<HomepageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchHomepageData = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/homepage/")
        const jsonData = await response.json()
        setData(jsonData)
      } catch (error) {
        console.error("Error fetching homepage data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchHomepageData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-slate-400">Loading Analytics...</p>
        </div>
      </div>
    )
  }

  const menChampions = data?.current_champions.filter(c => !c.division.startsWith("Women's")) || []
  const womenChampions = data?.current_champions.filter(c => c.division.startsWith("Women's")) || []

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero Section - Professional Analytics Style */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>

        <div className="relative container mx-auto px-4 py-20">
          <div className="max-w-6xl mx-auto">
            {/* Top Badge */}
            <div className="flex items-center gap-2 mb-6">
              <div className="h-1 w-12 bg-red-600"></div>
              <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">Professional MMA Intelligence</span>
            </div>

            {/* Main Title */}
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
              Advanced Fight
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-red-700">
                Analytics Platform
              </span>
            </h1>

            {/* Subtitle */}
            <p className="text-xl text-slate-300 mb-10 max-w-3xl leading-relaxed">
              Comprehensive UFC data analysis, real-time rankings, and advanced statistics
              for fighters, events, and betting intelligence.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4 mb-16">
              <Link href="/events">
                <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white">
                  <Calendar className="mr-2 h-5 w-5" />
                  View Events
                </Button>
              </Link>
              <Link href="/fighters">
                <Button size="lg" variant="outline" className="border-slate-700 text-white hover:bg-slate-800">
                  <Shield className="mr-2 h-5 w-5" />
                  Fighter Database
                </Button>
              </Link>
              <Link href="/rankings">
                <Button size="lg" variant="outline" className="border-slate-700 text-white hover:bg-slate-800">
                  <BarChart3 className="mr-2 h-5 w-5" />
                  Rankings
                </Button>
              </Link>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                <div className="text-3xl font-bold text-white mb-1">500+</div>
                <div className="text-sm text-slate-400 uppercase tracking-wide">Active Fighters</div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                <div className="text-3xl font-bold text-white mb-1">1,000+</div>
                <div className="text-sm text-slate-400 uppercase tracking-wide">Fight Records</div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                <div className="text-3xl font-bold text-white mb-1">Real-time</div>
                <div className="text-sm text-slate-400 uppercase tracking-wide">Data Sync</div>
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
                <div className="text-3xl font-bold text-white mb-1">Live</div>
                <div className="text-sm text-slate-400 uppercase tracking-wide">Rankings</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Current Champions Section */}
      <section className="py-20 bg-slate-950 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <Trophy className="h-6 w-6 text-red-600" />
              <h2 className="text-3xl md:text-4xl font-bold text-white">
                Current Champions
              </h2>
            </div>
            <p className="text-slate-400">Title holders across all UFC divisions</p>
          </div>

          {/* Men's Divisions */}
          {menChampions.length > 0 && (
            <div className="mb-12">
              <h3 className="text-xl font-semibold text-white mb-6 uppercase tracking-wide">Men's Divisions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {menChampions.map((champion) => (
                  <Link key={`${champion.division}-${champion.athlete_id}`} href={`/fighters/${champion.athlete_id}`}>
                    <Card className="group overflow-hidden bg-slate-900 border-slate-800 hover:border-red-600 transition-all">
                      <div className="relative">
                        {/* Champion Badge */}
                        <div className="absolute top-3 right-3 z-10">
                          <Badge className="bg-red-600 text-white border-none">
                            {champion.position === 'C' ? 'CHAMPION' : 'INTERIM'}
                          </Badge>
                        </div>

                        {/* Fighter Photo */}
                        {champion.headshot_url ? (
                          <div className="relative h-64 w-full bg-slate-800">
                            <Image
                              src={champion.headshot_url}
                              alt={champion.full_name}
                              fill
                              className="object-cover group-hover:scale-105 transition-transform duration-300"
                              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                            />
                          </div>
                        ) : (
                          <div className="h-64 w-full bg-slate-800 flex items-center justify-center">
                            <Shield className="h-16 w-16 text-slate-600" />
                          </div>
                        )}

                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent"></div>

                        {/* Fighter Info */}
                        <div className="absolute bottom-0 left-0 right-0 p-4">
                          <h3 className="text-white font-bold text-lg mb-1">{champion.full_name}</h3>
                          <p className="text-slate-300 text-sm font-medium">{champion.division}</p>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Women's Divisions */}
          {womenChampions.length > 0 && (
            <div>
              <h3 className="text-xl font-semibold text-white mb-6 uppercase tracking-wide">Women's Divisions</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {womenChampions.map((champion) => (
                  <Link key={`${champion.division}-${champion.athlete_id}`} href={`/fighters/${champion.athlete_id}`}>
                    <Card className="group overflow-hidden bg-slate-900 border-slate-800 hover:border-red-600 transition-all">
                      <div className="relative">
                        {/* Champion Badge */}
                        <div className="absolute top-3 right-3 z-10">
                          <Badge className="bg-red-600 text-white border-none">
                            {champion.position === 'C' ? 'CHAMPION' : 'INTERIM'}
                          </Badge>
                        </div>

                        {/* Fighter Photo */}
                        {champion.headshot_url ? (
                          <div className="relative h-64 w-full bg-slate-800">
                            <Image
                              src={champion.headshot_url}
                              alt={champion.full_name}
                              fill
                              className="object-cover group-hover:scale-105 transition-transform duration-300"
                              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                            />
                          </div>
                        ) : (
                          <div className="h-64 w-full bg-slate-800 flex items-center justify-center">
                            <Shield className="h-16 w-16 text-slate-600" />
                          </div>
                        )}

                        {/* Gradient Overlay */}
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent"></div>

                        {/* Fighter Info */}
                        <div className="absolute bottom-0 left-0 right-0 p-4">
                          <h3 className="text-white font-bold text-lg mb-1">{champion.full_name}</h3>
                          <p className="text-slate-300 text-sm font-medium">{champion.division}</p>
                        </div>
                      </div>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* View Rankings CTA */}
          <div className="text-center mt-12">
            <Link href="/rankings">
              <Button size="lg" variant="outline" className="border-slate-700 text-white hover:bg-slate-800">
                View Complete Rankings
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Upcoming Events Section */}
      <section className="py-20 bg-slate-900 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-12">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="h-6 w-6 text-red-600" />
                <h2 className="text-3xl md:text-4xl font-bold text-white">Upcoming Events</h2>
              </div>
              <p className="text-slate-400">Next scheduled UFC fight cards</p>
            </div>
            <Link href="/events" className="text-red-500 hover:text-red-400 font-medium group hidden md:flex items-center">
              View All
              <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {data?.upcoming_events && data.upcoming_events.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.upcoming_events.map((event) => (
                <Link key={event.id} href={`/events/${event.id}`}>
                  <Card className="group bg-slate-800 border-slate-700 hover:border-red-600 transition-all">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <h3 className="font-semibold text-white flex-1 group-hover:text-red-500 transition-colors">
                          {event.name}
                        </h3>
                        <Badge className="ml-2 bg-red-600 text-white border-none">UPCOMING</Badge>
                      </div>
                      <div className="space-y-3 text-sm">
                        <div className="flex items-center text-slate-300">
                          <Calendar className="w-4 h-4 mr-2 text-slate-500" />
                          <span className="font-medium">{new Date(event.date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center text-slate-400">
                          <MapPin className="w-4 h-4 mr-2 text-slate-500" />
                          {event.venue_name}
                        </div>
                        <div className="flex items-center text-slate-400">
                          <Globe className="w-4 h-4 mr-2 text-slate-500" />
                          {event.city}, {event.country}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-12 text-center">
                <Calendar className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No upcoming events scheduled</p>
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Featured Fighters Section */}
      <section className="py-20 bg-slate-950 border-b border-slate-800">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-12">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-6 w-6 text-red-600" />
                <h2 className="text-3xl md:text-4xl font-bold text-white">Featured Fighters</h2>
              </div>
              <p className="text-slate-400">Top-ranked athletes across divisions</p>
            </div>
            <Link href="/fighters" className="text-red-500 hover:text-red-400 font-medium group hidden md:flex items-center">
              View All
              <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {data?.featured_fighters && data.featured_fighters.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {data.featured_fighters.map((fighter) => (
                <Link key={fighter.id} href={`/fighters/${fighter.id}`}>
                  <Card className="group overflow-hidden bg-slate-900 border-slate-800 hover:border-red-600 transition-all">
                    <div className="relative">
                      {/* Ranking Badge */}
                      <div className="absolute top-3 left-3 z-10">
                        <Badge className="bg-slate-950/90 text-white border border-slate-700">
                          RANK #{fighter.position}
                        </Badge>
                      </div>

                      {/* Fighter Photo */}
                      {fighter.headshot_url ? (
                        <div className="relative h-72 w-full bg-slate-800">
                          <Image
                            src={fighter.headshot_url}
                            alt={fighter.full_name}
                            fill
                            className="object-cover group-hover:scale-105 transition-transform duration-300"
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                          />
                        </div>
                      ) : (
                        <div className="h-72 w-full bg-slate-800 flex items-center justify-center">
                          <Shield className="h-16 w-16 text-slate-600" />
                        </div>
                      )}

                      {/* Gradient Overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/50 to-transparent"></div>

                      {/* Fighter Info */}
                      <div className="absolute bottom-0 left-0 right-0 p-4">
                        <h3 className="text-lg font-bold text-white mb-1">{fighter.full_name}</h3>
                        <p className="text-slate-300 text-sm mb-2">{fighter.division || fighter.weight_class}</p>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs bg-slate-800 border-slate-700 text-slate-300">
                            {fighter.fight_count} Fights
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-12 text-center">
                <Shield className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No featured fighters available</p>
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Recent Events Section */}
      <section className="py-20 bg-slate-900">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center mb-12">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-6 w-6 text-red-600" />
                <h2 className="text-3xl md:text-4xl font-bold text-white">Recent Events</h2>
              </div>
              <p className="text-slate-400">Latest completed fight cards</p>
            </div>
            <Link href="/events" className="text-red-500 hover:text-red-400 font-medium group hidden md:flex items-center">
              View All
              <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {data?.recent_events && data.recent_events.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.recent_events.map((event) => (
                <Link key={event.id} href={`/events/${event.id}`}>
                  <Card className="group bg-slate-800 border-slate-700 hover:border-slate-600 transition-all">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <h3 className="font-semibold text-white flex-1 group-hover:text-slate-300 transition-colors">
                          {event.name}
                        </h3>
                        <Badge variant="secondary" className="ml-2 bg-slate-700 border-slate-600 text-slate-300">
                          COMPLETED
                        </Badge>
                      </div>
                      <div className="space-y-3 text-sm">
                        <div className="flex items-center text-slate-300">
                          <Calendar className="w-4 h-4 mr-2 text-slate-500" />
                          <span className="font-medium">{new Date(event.date).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center text-slate-400">
                          <MapPin className="w-4 h-4 mr-2 text-slate-500" />
                          {event.venue_name}
                        </div>
                        <div className="flex items-center text-slate-400">
                          <Globe className="w-4 h-4 mr-2 text-slate-500" />
                          {event.city}, {event.country}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          ) : (
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-12 text-center">
                <Activity className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No recent events found</p>
              </CardContent>
            </Card>
          )}
        </div>
      </section>
    </div>
  )
}
