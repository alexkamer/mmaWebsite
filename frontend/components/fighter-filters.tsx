"use client"

import { useState } from "react"
import { Filter, X, ChevronDown } from "lucide-react"

interface FilterOption {
  value: string
  label: string
  count?: number
}

interface FighterFiltersProps {
  weightClasses?: FilterOption[]
  promotions?: FilterOption[]
  countries?: FilterOption[]
  selectedWeightClasses: string[]
  selectedPromotions: string[]
  selectedCountries: string[]
  onWeightClassChange: (values: string[]) => void
  onPromotionChange: (values: string[]) => void
  onCountryChange: (values: string[]) => void
  onClearAll: () => void
}

export function FighterFilters({
  weightClasses = [],
  promotions = [],
  countries = [],
  selectedWeightClasses,
  selectedPromotions,
  selectedCountries,
  onWeightClassChange,
  onPromotionChange,
  onCountryChange,
  onClearAll,
}: FighterFiltersProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [expandedSection, setExpandedSection] = useState<string | null>(null)

  const totalFilters =
    selectedWeightClasses.length +
    selectedPromotions.length +
    selectedCountries.length

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  const handleCheckboxChange = (
    value: string,
    selected: string[],
    onChange: (values: string[]) => void
  ) => {
    if (selected.includes(value)) {
      onChange(selected.filter((v) => v !== value))
    } else {
      onChange([...selected, value])
    }
  }

  const removeFilter = (value: string, selected: string[], onChange: (values: string[]) => void) => {
    onChange(selected.filter((v) => v !== value))
  }

  return (
    <div className="space-y-4">
      {/* Filter Button and Active Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
        >
          <Filter className="h-4 w-4" />
          Filters
          {totalFilters > 0 && (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
              {totalFilters}
            </span>
          )}
        </button>

        {/* Active Filter Badges */}
        {selectedWeightClasses.map((wc) => (
          <div
            key={wc}
            className="inline-flex items-center gap-1 rounded-full bg-blue-600/10 px-3 py-1 text-sm text-blue-600 dark:text-blue-400"
          >
            <span>{wc}</span>
            <button
              onClick={() => removeFilter(wc, selectedWeightClasses, onWeightClassChange)}
              className="hover:bg-blue-600/20 rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {selectedPromotions.map((promo) => (
          <div
            key={promo}
            className="inline-flex items-center gap-1 rounded-full bg-green-600/10 px-3 py-1 text-sm text-green-600 dark:text-green-400"
          >
            <span>{promo}</span>
            <button
              onClick={() => removeFilter(promo, selectedPromotions, onPromotionChange)}
              className="hover:bg-green-600/20 rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {selectedCountries.map((country) => (
          <div
            key={country}
            className="inline-flex items-center gap-1 rounded-full bg-purple-600/10 px-3 py-1 text-sm text-purple-600 dark:text-purple-400"
          >
            <span>{country}</span>
            <button
              onClick={() => removeFilter(country, selectedCountries, onCountryChange)}
              className="hover:bg-purple-600/20 rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {totalFilters > 0 && (
          <button
            onClick={onClearAll}
            className="text-sm text-muted-foreground hover:text-foreground underline"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {isOpen && (
        <div className="rounded-lg border bg-card p-4 space-y-4">
          {/* Weight Classes */}
          {weightClasses.length > 0 && (
            <div className="space-y-2">
              <button
                onClick={() => toggleSection("weightClasses")}
                className="flex w-full items-center justify-between text-sm font-semibold"
              >
                <span>Weight Class</span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    expandedSection === "weightClasses" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedSection === "weightClasses" && (
                <div className="space-y-2 pl-2">
                  {weightClasses.map((wc) => (
                    <label
                      key={wc.value}
                      className="flex items-center gap-2 cursor-pointer hover:bg-muted p-2 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={selectedWeightClasses.includes(wc.value)}
                        onChange={() =>
                          handleCheckboxChange(
                            wc.value,
                            selectedWeightClasses,
                            onWeightClassChange
                          )
                        }
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm flex-1">{wc.label}</span>
                      {wc.count !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          {wc.count}
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Promotions */}
          {promotions.length > 0 && (
            <div className="space-y-2">
              <button
                onClick={() => toggleSection("promotions")}
                className="flex w-full items-center justify-between text-sm font-semibold"
              >
                <span>Promotion</span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    expandedSection === "promotions" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedSection === "promotions" && (
                <div className="space-y-2 pl-2">
                  {promotions.map((promo) => (
                    <label
                      key={promo.value}
                      className="flex items-center gap-2 cursor-pointer hover:bg-muted p-2 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={selectedPromotions.includes(promo.value)}
                        onChange={() =>
                          handleCheckboxChange(
                            promo.value,
                            selectedPromotions,
                            onPromotionChange
                          )
                        }
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm flex-1">{promo.label}</span>
                      {promo.count !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          {promo.count}
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Countries */}
          {countries.length > 0 && (
            <div className="space-y-2">
              <button
                onClick={() => toggleSection("countries")}
                className="flex w-full items-center justify-between text-sm font-semibold"
              >
                <span>Country</span>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    expandedSection === "countries" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedSection === "countries" && (
                <div className="space-y-2 pl-2 max-h-64 overflow-y-auto">
                  {countries.map((country) => (
                    <label
                      key={country.value}
                      className="flex items-center gap-2 cursor-pointer hover:bg-muted p-2 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={selectedCountries.includes(country.value)}
                        onChange={() =>
                          handleCheckboxChange(
                            country.value,
                            selectedCountries,
                            onCountryChange
                          )
                        }
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm flex-1">{country.label}</span>
                      {country.count !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          {country.count}
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
