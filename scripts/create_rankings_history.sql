-- Create rankings history table for tracking rank changes over time
CREATE TABLE IF NOT EXISTS ufc_rankings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    division TEXT NOT NULL,
    fighter_name TEXT NOT NULL,
    rank INTEGER,
    is_champion BOOLEAN DEFAULT FALSE,
    is_interim_champion BOOLEAN DEFAULT FALSE,
    ranking_type TEXT NOT NULL,
    athlete_id TEXT,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(division, fighter_name, snapshot_date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rankings_history_fighter ON ufc_rankings_history(fighter_name, division);
CREATE INDEX IF NOT EXISTS idx_rankings_history_date ON ufc_rankings_history(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_rankings_history_division_date ON ufc_rankings_history(division, snapshot_date);

-- Copy current rankings to history table (initial snapshot)
INSERT OR IGNORE INTO ufc_rankings_history
    (division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, snapshot_date)
SELECT
    division, fighter_name, rank, is_champion, is_interim_champion, ranking_type, athlete_id, last_updated
FROM ufc_rankings;

-- View for getting latest 2 ranking snapshots per division
CREATE VIEW IF NOT EXISTS v_ranking_changes AS
WITH ranked_snapshots AS (
    SELECT
        division,
        fighter_name,
        rank,
        snapshot_date,
        ROW_NUMBER() OVER (PARTITION BY division, fighter_name ORDER BY snapshot_date DESC) as rn
    FROM ufc_rankings_history
    WHERE rank IS NOT NULL
)
SELECT
    curr.division,
    curr.fighter_name,
    curr.rank as current_rank,
    prev.rank as previous_rank,
    CASE
        WHEN prev.rank IS NULL THEN 'NEW'
        WHEN curr.rank < prev.rank THEN 'UP'
        WHEN curr.rank > prev.rank THEN 'DOWN'
        ELSE 'SAME'
    END as movement,
    ABS(COALESCE(curr.rank - prev.rank, 0)) as rank_change
FROM ranked_snapshots curr
LEFT JOIN ranked_snapshots prev ON
    curr.division = prev.division AND
    curr.fighter_name = prev.fighter_name AND
    prev.rn = 2
WHERE curr.rn = 1;
