-- Add missing columns to ufc_rankings table

-- Add athlete_id column if it doesn't exist
ALTER TABLE ufc_rankings ADD COLUMN athlete_id TEXT;

-- Add last_updated column if it doesn't exist
ALTER TABLE ufc_rankings ADD COLUMN last_updated TEXT;

-- Create index on athlete_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_rankings_athlete_id ON ufc_rankings(athlete_id);

-- Create index on last_updated
CREATE INDEX IF NOT EXISTS idx_rankings_last_updated ON ufc_rankings(last_updated);
