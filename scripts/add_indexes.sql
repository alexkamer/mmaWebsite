\-- Database Performance Indexes for MMA Website
-- Run this script to add indexes for commonly queried columns

-- Indexes for fights table (most queried table)
CREATE INDEX IF NOT EXISTS idx_fights_fighter_1_id ON fights(fighter_1_id);
CREATE INDEX IF NOT EXISTS idx_fights_fighter_2_id ON fights(fighter_2_id);
CREATE INDEX IF NOT EXISTS idx_fights_event_id ON fights(event_id);
CREATE INDEX IF NOT EXISTS idx_fights_fight_id ON fights(fight_id);
CREATE INDEX IF NOT EXISTS idx_fights_weight_class ON fights(weight_class);
CREATE INDEX IF NOT EXISTS idx_fights_result ON fights(result_display_name);

-- Indexes for cards table (events)
CREATE INDEX IF NOT EXISTS idx_cards_event_id ON cards(event_id);
CREATE INDEX IF NOT EXISTS idx_cards_date ON cards(date);
CREATE INDEX IF NOT EXISTS idx_cards_league ON cards(league);
CREATE INDEX IF NOT EXISTS idx_cards_date_league ON cards(date, league);

-- Indexes for athletes table (fighters)
CREATE INDEX IF NOT EXISTS idx_athletes_id ON athletes(id);
CREATE INDEX IF NOT EXISTS idx_athletes_full_name ON athletes(full_name);
CREATE INDEX IF NOT EXISTS idx_athletes_league ON athletes(default_league);
CREATE INDEX IF NOT EXISTS idx_athletes_weight_class ON athletes(weight_class);

-- Indexes for odds table
CREATE INDEX IF NOT EXISTS idx_odds_fight_id ON odds(fight_id);
CREATE INDEX IF NOT EXISTS idx_odds_home_athlete_id ON odds(home_athlete_id);
CREATE INDEX IF NOT EXISTS idx_odds_away_athlete_id ON odds(away_athlete_id);
CREATE INDEX IF NOT EXISTS idx_odds_provider ON odds(provider_name);

-- Indexes for statistics_for_fights table
CREATE INDEX IF NOT EXISTS idx_stats_event_id ON statistics_for_fights(event_id);
CREATE INDEX IF NOT EXISTS idx_stats_competition_id ON statistics_for_fights(competition_id);
CREATE INDEX IF NOT EXISTS idx_stats_athlete_id ON statistics_for_fights(athlete_id);

-- Indexes for ufc_rankings table
CREATE INDEX IF NOT EXISTS idx_rankings_fighter_name ON ufc_rankings(fighter_name);
CREATE INDEX IF NOT EXISTS idx_rankings_division ON ufc_rankings(division);
CREATE INDEX IF NOT EXISTS idx_rankings_type ON ufc_rankings(ranking_type);
CREATE INDEX IF NOT EXISTS idx_rankings_champion ON ufc_rankings(is_champion);

-- Indexes for linescores table
CREATE INDEX IF NOT EXISTS idx_linescores_fight_id ON linescores(fight_id);
CREATE INDEX IF NOT EXISTS idx_linescores_fighter_id ON linescores(fighter_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fights_event_fighters ON fights(event_id, fighter_1_id, fighter_2_id);
CREATE INDEX IF NOT EXISTS idx_cards_league_date ON cards(league, date DESC);
CREATE INDEX IF NOT EXISTS idx_fights_fighter1_winner ON fights(fighter_1_id, fighter_1_winner);
CREATE INDEX IF NOT EXISTS idx_fights_fighter2_winner ON fights(fighter_2_id, fighter_2_winner);

-- Analyze the database to update statistics for query optimization
ANALYZE;
