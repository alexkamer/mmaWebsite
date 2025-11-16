-- Performance indexes for system_checker queries
-- These indexes will speed up the card-by-card betting analytics queries

-- Index for joining fights to cards by event_id
CREATE INDEX IF NOT EXISTS idx_fights_event_id ON fights(event_id);

-- Index for joining odds to fights by fight_id
CREATE INDEX IF NOT EXISTS idx_odds_fight_id ON odds(fight_id);

-- Index for selecting first provider (MIN(provider_id))
CREATE INDEX IF NOT EXISTS idx_odds_provider_id ON odds(provider_id);

-- Composite index for filtering cards by league and date
CREATE INDEX IF NOT EXISTS idx_cards_league_date ON cards(league, date);

-- Index for filtering fights by winner status
CREATE INDEX IF NOT EXISTS idx_fights_winner ON fights(fighter_1_winner, fighter_2_winner);

-- Index for odds favorite/underdog flags
CREATE INDEX IF NOT EXISTS idx_odds_favorites ON odds(home_favorite, away_favorite, home_underdog, away_underdog);

-- Verify indexes were created
SELECT name, tbl_name
FROM sqlite_master
WHERE type = 'index'
AND name LIKE 'idx_%'
ORDER BY tbl_name, name;
