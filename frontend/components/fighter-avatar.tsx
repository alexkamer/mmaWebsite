"use client"

import { useState } from "react"
import Image from "next/image"
import { User } from "lucide-react"

interface FighterAvatarProps {
  src?: string | null
  alt: string
  size?: "sm" | "md" | "lg" | "xl"
  className?: string
}

const sizeClasses = {
  sm: "w-12 h-12",
  md: "w-16 h-16",
  lg: "w-24 h-24",
  xl: "w-32 h-32",
}

const iconSizes = {
  sm: "h-6 w-6",
  md: "h-8 w-8",
  lg: "h-12 w-12",
  xl: "h-16 w-16",
}

export function FighterAvatar({
  src,
  alt,
  size = "md",
  className = ""
}: FighterAvatarProps) {
  const [imageError, setImageError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  const shouldShowFallback = !src || imageError

  if (shouldShowFallback) {
    return (
      <div
        className={`${sizeClasses[size]} ${className} rounded-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border-2 border-primary/20`}
      >
        <User className={`${iconSizes[size]} text-primary/40`} />
      </div>
    )
  }

  return (
    <div className={`${sizeClasses[size]} ${className} relative rounded-full overflow-hidden`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gradient-to-br from-muted to-muted/50 animate-pulse" />
      )}
      <Image
        src={src}
        alt={alt}
        fill
        className={`object-cover transition-opacity duration-300 ${
          isLoading ? "opacity-0" : "opacity-100"
        }`}
        onError={() => setImageError(true)}
        onLoadingComplete={() => setIsLoading(false)}
        unoptimized
      />
    </div>
  )
}
