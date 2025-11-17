"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Calendar, MapPin, Trophy, TrendingUp } from "lucide-react"
import { eventsAPI, type EventDetail, type EventFight } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"

// Fighter Card Component
function FighterCard({
  fighter,
  isWinner,
  isMainEvent = false
}: {
  fighter: {
    id: number
    name: string
    image?: string
    record?: string
    odds?: string
  }
  isWinner: boolean
  isMainEvent?: boolean
}) {
  const photoSize = isMainEvent ? "w-40 h-40" : "w-20 h-20"
  const nameSize = isMainEvent ? "text-2xl" : "text-lg"

  return (
    <div className="flex flex-col items-center text-center space-y-3">
      <Link href={`/fighters/${fighter.id}`}>
        <Avatar className={`${photoSize} ${isWinner ? 'ring-4 ring-green-500' : ''} cursor-pointer hover:opacity-80 transition-opacity`}>
          <AvatarImage src={fighter.image} alt={fighter.name} />
          <AvatarFallback className="text-2xl font-bold">
            {fighter.name.charAt(0)}
          </AvatarFallback>
        </Avatar>
      </Link>

      <div className="space-y-2">
        <Link
          href={`/fighters/${fighter.id}`}
          className={`${nameSize} font-bold text-blue-600 hover:text-blue-800 hover:underline block`}
        >
          {fighter.name}
        </Link>

        {fighter.record && (
          <div className="text-sm font-mono text-muted-foreground">
            {fighter.record}
          </div>
        )}

        {fighter.odds && (
          <div className={`text-sm font-bold font-mono ${
            fighter.odds.startsWith('-') ? 'text-blue-600' : 'text-orange-600'
          }`}>
            {fighter.odds}
          </div>
        )}

        {isWinner !== null && (
          <Badge variant={isWinner ? "default" : "destructive"} className="font-bold">
            {isWinner ? "✓ WINNER" : "LOST"}
          </Badge>
        )}
      </div>
    </div>
  )
}

// Main Event Card Component
function MainEventCard({ fight }: { fight: EventFight }) {
  const isTitleFight = fight.is_title_fight

  return (
    <Card className={`${isTitleFight ? 'border-yellow-500 border-4' : ''}`}>
      <CardHeader className={`${isTitleFight ? 'bg-gradient-to-r from-yellow-50 to-orange-50' : 'bg-gradient-to-r from-red-50 to-orange-50'}`}>
        <CardTitle className="flex items-center gap-3">
          <Trophy className="w-8 h-8" />
          <span>Main Event</span>
          {isTitleFight && (
            <Badge variant="default" className="bg-yellow-500 text-white">
              CHAMPIONSHIP
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
          {/* Fighter 1 */}
          <FighterCard
            fighter={{
              id: fight.fighter1_id,
              name: fight.fighter1_name,
              image: fight.fighter1_image,
              record: fight.fighter1_record,
              odds: fight.fighter1_odds
            }}
            isWinner={fight.winner === 'fighter1'}
            isMainEvent={true}
          />

          {/* VS Section */}
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="text-5xl font-black text-muted-foreground">VS</div>

            {fight.method && (
              <Card className="w-full">
                <CardContent className="p-4 text-center">
                  <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                    Result
                  </div>
                  <div className="text-lg font-bold">{fight.method}</div>
                  {fight.round && (
                    <div className="text-sm text-muted-foreground mt-1">
                      Round {fight.round} {fight.time && `• ${fight.time}`}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {fight.weight_class && (
              <Badge variant="secondary" className="px-4 py-2">
                {fight.weight_class}
              </Badge>
            )}
          </div>

          {/* Fighter 2 */}
          <FighterCard
            fighter={{
              id: fight.fighter2_id,
              name: fight.fighter2_name,
              image: fight.fighter2_image,
              record: fight.fighter2_record,
              odds: fight.fighter2_odds
            }}
            isWinner={fight.winner === 'fighter2'}
            isMainEvent={true}
          />
        </div>
      </CardContent>
    </Card>
  )
}

// Regular Fight Card Component
function FightCard({ fight, isMainCard = false }: { fight: EventFight, isMainCard?: boolean }) {
  const photoSize = isMainCard ? "w-20 h-20" : "w-16 h-16"

  return (
    <Card className={`hover:shadow-lg transition-shadow ${fight.is_title_fight ? 'border-l-4 border-yellow-400' : ''}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <Link href={`/fighters/${fight.fighter1_id}`}>
              <Avatar className={`${photoSize} ${fight.winner === 'fighter1' ? 'ring-2 ring-green-500' : ''} cursor-pointer hover:opacity-80 transition-opacity`}>
                <AvatarImage src={fight.fighter1_image} alt={fight.fighter1_name} />
                <AvatarFallback>{fight.fighter1_name.charAt(0)}</AvatarFallback>
              </Avatar>
            </Link>

            <div>
              <Link
                href={`/fighters/${fight.fighter1_id}`}
                className="text-base font-bold text-blue-600 hover:text-blue-800 hover:underline block"
              >
                {fight.fighter1_name}
              </Link>
              {fight.fighter1_record && (
                <div className="text-xs font-mono text-muted-foreground">{fight.fighter1_record}</div>
              )}
              <div className="flex items-center gap-2 mt-1">
                {fight.fighter1_odds && (
                  <span className={`text-xs font-mono font-bold ${
                    fight.fighter1_odds.startsWith('-') ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    {fight.fighter1_odds}
                  </span>
                )}
                {fight.winner === 'fighter1' && (
                  <Badge variant="default" className="text-xs">Won</Badge>
                )}
                {fight.winner === 'fighter2' && (
                  <Badge variant="destructive" className="text-xs">Lost</Badge>
                )}
              </div>
            </div>
          </div>

          <div className="text-xl font-bold text-muted-foreground px-4">VS</div>

          <div className="flex items-center gap-3 flex-1 flex-row-reverse">
            <Link href={`/fighters/${fight.fighter2_id}`}>
              <Avatar className={`${photoSize} ${fight.winner === 'fighter2' ? 'ring-2 ring-green-500' : ''} cursor-pointer hover:opacity-80 transition-opacity`}>
                <AvatarImage src={fight.fighter2_image} alt={fight.fighter2_name} />
                <AvatarFallback>{fight.fighter2_name.charAt(0)}</AvatarFallback>
              </Avatar>
            </Link>

            <div className="text-right">
              <Link
                href={`/fighters/${fight.fighter2_id}`}
                className="text-base font-bold text-blue-600 hover:text-blue-800 hover:underline block"
              >
                {fight.fighter2_name}
              </Link>
              {fight.fighter2_record && (
                <div className="text-xs font-mono text-muted-foreground">{fight.fighter2_record}</div>
              )}
              <div className="flex items-center justify-end gap-2 mt-1">
                {fight.fighter2_odds && (
                  <span className={`text-xs font-mono font-bold ${
                    fight.fighter2_odds.startsWith('-') ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    {fight.fighter2_odds}
                  </span>
                )}
                {fight.winner === 'fighter2' && (
                  <Badge variant="default" className="text-xs">Won</Badge>
                )}
                {fight.winner === 'fighter1' && (
                  <Badge variant="destructive" className="text-xs">Lost</Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Fight Details */}
        <div className="mt-4 flex flex-col items-center gap-2">
          <div className="flex items-center gap-3">
            <Badge variant="secondary">{fight.weight_class}</Badge>
            {fight.is_title_fight && (
              <Badge className="bg-yellow-500 text-white">Title Fight</Badge>
            )}
          </div>
          {fight.method && (
            <div className="text-sm text-muted-foreground">
              {fight.method}
              {fight.round && ` • Round ${fight.round}`}
              {fight.time && ` • ${fight.time}`}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default function EventDetailPage() {
  const params = useParams()
  const eventId = parseInt(params.id as string)

  const [event, setEvent] = useState<EventDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchEvent = async () => {
      setLoading(true)
      try {
        const data = await eventsAPI.get(eventId)
        setEvent(data)
      } catch (error) {
        console.error("Error fetching event:", error)
      } finally {
        setLoading(false)
      }
    }

    if (eventId) {
      fetchEvent()
    }
  }, [eventId])

  if (loading) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 rounded-lg" />
        <Skeleton className="h-96 rounded-lg" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-4">Event not found</h1>
        <Link href="/events" className="text-blue-500 hover:underline">
          Back to events
        </Link>
      </div>
    )
  }

  // Group fights by card segment
  // Main event has the lowest match_number (typically 1)
  const mainEventFight = event.fights?.reduce((prev, curr) =>
    (curr.match_number < prev.match_number) ? curr : prev
  )
  const mainEvent = mainEventFight ? [mainEventFight] : []
  const mainCard = event.fights?.filter(f =>
    f.card_segment?.toLowerCase().includes('main') &&
    f.match_number !== mainEventFight?.match_number
  ) || []
  const prelims = event.fights?.filter(f =>
    f.card_segment?.toLowerCase().includes('prelim') &&
    !f.card_segment?.toLowerCase().includes('early')
  ) || []
  const earlyPrelims = event.fights?.filter(f =>
    f.card_segment?.toLowerCase().includes('early')
  ) || []

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <Link
        href="/events"
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to events
      </Link>

      {/* Event Header */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-br from-red-700 via-red-600 to-orange-600 text-white p-8 relative">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0" style={{
              backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.1) 35px, rgba(255,255,255,.1) 70px)'
            }} />
          </div>

          <div className="relative z-10">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 drop-shadow-lg">
              {event.name}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-red-50">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                <span className="text-lg font-semibold">{event.date}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                <span className="text-lg">
                  {event.venue && `${event.venue}, `}
                  {event.location}
                </span>
              </div>
              {event.fights && (
                <Badge variant="secondary" className="bg-white/20 text-white backdrop-blur-sm">
                  {event.fights.length} Fights
                </Badge>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Main Event */}
      {mainEvent.length > 0 && (
        <div className="space-y-4">
          <MainEventCard fight={mainEvent[0]} />
        </div>
      )}

      {/* Main Card */}
      {mainCard.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <TrendingUp className="w-6 h-6" />
            Main Card
          </h2>
          <div className="space-y-4">
            {mainCard.map((fight) => (
              <FightCard key={fight.id} fight={fight} isMainCard={true} />
            ))}
          </div>
        </div>
      )}

      {/* Prelims */}
      {prelims.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-muted-foreground">Prelims</h2>
          <div className="space-y-3">
            {prelims.map((fight) => (
              <FightCard key={fight.id} fight={fight} />
            ))}
          </div>
        </div>
      )}

      {/* Early Prelims */}
      {earlyPrelims.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-muted-foreground">Early Prelims</h2>
          <div className="space-y-3">
            {earlyPrelims.map((fight) => (
              <FightCard key={fight.id} fight={fight} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
