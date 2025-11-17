export function FighterCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      {/* Avatar skeleton */}
      <div className="w-16 h-16 rounded-full bg-muted animate-pulse" />

      {/* Name skeleton */}
      <div className="space-y-2">
        <div className="h-5 bg-muted rounded animate-pulse w-3/4" />
        <div className="h-4 bg-muted rounded animate-pulse w-1/2" />
      </div>
    </div>
  )
}

export function FighterListSkeleton({ count = 24 }: { count?: number }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {[...Array(count)].map((_, i) => (
        <FighterCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function EventCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4">
      {/* Event title */}
      <div className="h-6 bg-muted rounded animate-pulse w-3/4" />

      {/* Date and location */}
      <div className="flex gap-4">
        <div className="h-4 bg-muted rounded animate-pulse w-32" />
        <div className="h-4 bg-muted rounded animate-pulse w-40" />
      </div>

      {/* Badge */}
      <div className="h-6 bg-muted rounded-full animate-pulse w-16" />
    </div>
  )
}

export function EventListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {[...Array(count)].map((_, i) => (
        <EventCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function FinishCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      {/* Badge and time */}
      <div className="flex items-center justify-between">
        <div className="h-6 bg-muted rounded-full animate-pulse w-24" />
        <div className="h-4 bg-muted rounded animate-pulse w-16" />
      </div>

      {/* Fighter info */}
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-muted animate-pulse" />
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
          <div className="h-3 bg-muted rounded animate-pulse w-1/2" />
        </div>
      </div>

      {/* Event name */}
      <div className="h-4 bg-muted rounded animate-pulse w-full" />
    </div>
  )
}

export function SearchSkeleton() {
  return (
    <div className="space-y-2 py-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-3 py-2">
          <div className="w-10 h-10 rounded-full bg-muted animate-pulse" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-muted rounded animate-pulse w-2/3" />
            <div className="h-3 bg-muted rounded animate-pulse w-1/3" />
          </div>
        </div>
      ))}
    </div>
  )
}
