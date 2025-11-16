import Link from "next/link"
import { FadeIn } from "@/components/animations/fade-in"
import { StaggerContainer, StaggerItem } from "@/components/animations/stagger-container"

export default function HomePage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <FadeIn duration={0.6}>
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            MMA Fighter Database
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Comprehensive statistics, rankings, and fight analysis for MMA fighters worldwide
          </p>
        </section>
      </FadeIn>

      {/* Quick Links Grid */}
      <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4" staggerDelay={0.1}>
        <StaggerItem>
          <Link
            href="/fighters"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Fighters</h3>
              <p className="text-sm text-muted-foreground">
                Browse fighter profiles, stats, and fight history
              </p>
            </div>
            <div className="absolute bottom-0 right-0 h-24 w-24 -mr-8 -mb-8 opacity-10 group-hover:opacity-20 transition-opacity">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
              </svg>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/events"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Events</h3>
              <p className="text-sm text-muted-foreground">
                Upcoming and past fight cards with results
              </p>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/rankings"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Rankings</h3>
              <p className="text-sm text-muted-foreground">
                Current UFC rankings by division
              </p>
            </div>
          </Link>
        </StaggerItem>

        <StaggerItem>
          <Link
            href="/games"
            className="block group relative overflow-hidden rounded-lg border bg-card p-6 hover:shadow-lg transition-all"
          >
            <div className="space-y-2">
              <h3 className="text-2xl font-semibold">Games</h3>
              <p className="text-sm text-muted-foreground">
                Fighter Wordle, Tale of the Tape, and more
              </p>
            </div>
          </Link>
        </StaggerItem>
      </StaggerContainer>

      {/* Stats Section */}
      <FadeIn delay={0.3} duration={0.6}>
        <section className="grid gap-6 sm:grid-cols-3">
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">36,000+</div>
            <div className="text-sm text-muted-foreground">Fighters</div>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">10,000+</div>
            <div className="text-sm text-muted-foreground">Events</div>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="text-3xl font-bold">Live</div>
            <div className="text-sm text-muted-foreground">UFC Rankings</div>
          </div>
        </section>
      </FadeIn>
    </div>
  )
}
