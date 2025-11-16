"""ESPN API integration endpoints."""
import httpx
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

from ..database.connection import execute_query, execute_query_one

router = APIRouter()


@router.get("/next-event")
async def get_next_ufc_event():
    """Get the next UFC event with fighter details and odds from ESPN API."""
    try:
        # Fetch next UFC event from ESPN
        ufc_events_url = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/?lang=en&region=us"
        async with httpx.AsyncClient(timeout=30.0) as client:
            ufc_event_response = await client.get(ufc_events_url)
            ufc_event_response.raise_for_status()
            ufc_event_data = ufc_event_response.json()

        if not ufc_event_data.get('items'):
            raise HTTPException(status_code=404, detail="No upcoming UFC events found")

        next_ufc_event_url = ufc_event_data['items'][0]['$ref']

        # Process the next event
        async with httpx.AsyncClient(timeout=30.0) as client:
            event_response = await client.get(next_ufc_event_url)
            event_response.raise_for_status()
            event_data = event_response.json()

        # Parse event details
        raw_date = event_data.get("date", "").split("T")[0]
        try:
            target = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except:
            raise HTTPException(status_code=500, detail="Invalid event date format")

        event_id = int(next_ufc_event_url.split("?")[0].split("/")[-1])
        venue = event_data.get("competitions", [{}])[0].get("venue", {})

        # Build event card
        card = {
            "event_id": event_id,
            "event_name": event_data.get("name"),
            "date": str(target),
            "venue_name": venue.get("fullName"),
            "city": venue.get("address", {}).get("city"),
            "state": venue.get("address", {}).get("state"),
            "country": venue.get("address", {}).get("country"),
        }

        # Process fights
        fights = []
        for comp in event_data.get("competitions", []):
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            fight = {
                "fight_id": comp.get("id"),
                "fighter_1_id": competitors[0].get("id"),
                "fighter_2_id": competitors[1].get("id"),
                "weight_class": comp.get("type", {}).get("text"),
                "rounds_format": comp.get("format", {}).get("regulation", {}).get("periods"),
                "match_number": comp.get("matchNumber"),
                "odds_url": comp.get("odds", {}).get("$ref"),
            }
            fights.append(fight)

        # Get all fighter IDs
        fighter_ids = set()
        for fight in fights:
            fighter_ids.add(str(fight['fighter_1_id']))
            fighter_ids.add(str(fight['fighter_2_id']))

        # Fetch fighter details from database
        fighter_lookup = {}
        record_lookup = {}

        if fighter_ids:
            fighter_ids_str = ','.join(f"'{fid}'" for fid in fighter_ids)

            # Get fighter details
            fighters = execute_query(f"""
                SELECT id, full_name, headshot_url
                FROM athletes
                WHERE id IN ({fighter_ids_str})
            """)
            fighter_lookup = {str(f['id']): f for f in fighters}

            # Get fighter records
            fighter_records = execute_query(f"""
                WITH fighter_results AS (
                    SELECT
                        fighter_id,
                        SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN won = 0 AND result_type NOT IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN result_type IN ('Draw', 'No Contest') THEN 1 ELSE 0 END) as draws
                    FROM (
                        SELECT
                            fighter_1_id as fighter_id,
                            fighter_1_winner as won,
                            result_display_name as result_type
                        FROM fights
                        UNION ALL
                        SELECT
                            fighter_2_id as fighter_id,
                            fighter_2_winner as won,
                            result_display_name as result_type
                        FROM fights
                    ) combined
                    WHERE fighter_id IN ({fighter_ids_str})
                    GROUP BY fighter_id
                )
                SELECT
                    fighter_id,
                    COALESCE(wins, 0) as wins,
                    COALESCE(losses, 0) as losses,
                    COALESCE(draws, 0) as draws
                FROM fighter_results
            """)
            record_lookup = {str(r['fighter_id']): f"{r['wins']}-{r['losses']}-{r['draws']}" for r in fighter_records}

        # Enrich fights with fighter details and odds
        for fight in fights:
            # Fighter 1
            fighter1 = fighter_lookup.get(str(fight['fighter_1_id']))
            if fighter1:
                fight['fighter_1_name'] = fighter1['full_name']
                fight['fighter_1_image'] = fighter1['headshot_url']
                fight['fighter_1_record'] = record_lookup.get(str(fight['fighter_1_id']), "0-0-0")
            else:
                fight['fighter_1_name'] = f"Fighter {fight['fighter_1_id']}"
                fight['fighter_1_image'] = None
                fight['fighter_1_record'] = "TBD"

            # Fighter 2
            fighter2 = fighter_lookup.get(str(fight['fighter_2_id']))
            if fighter2:
                fight['fighter_2_name'] = fighter2['full_name']
                fight['fighter_2_image'] = fighter2['headshot_url']
                fight['fighter_2_record'] = record_lookup.get(str(fight['fighter_2_id']), "0-0-0")
            else:
                fight['fighter_2_name'] = f"Fighter {fight['fighter_2_id']}"
                fight['fighter_2_image'] = None
                fight['fighter_2_record'] = "TBD"

            # Fetch odds if available
            if fight.get('odds_url'):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        odds_response = await client.get(fight['odds_url'])
                        odds_response.raise_for_status()
                        odds_data = odds_response.json()

                    # Get first provider's odds
                    if odds_data.get('items'):
                        provider = odds_data['items'][0]
                        home_athlete_id = provider.get('homeAthleteOdds', {}).get('athlete', {}).get('$ref', '').split('/')[-1].split('?')[0]
                        away_athlete_id = provider.get('awayAthleteOdds', {}).get('athlete', {}).get('$ref', '').split('/')[-1].split('?')[0]

                        # Match odds to fighters
                        if str(fight['fighter_1_id']) == home_athlete_id:
                            fight['fighter_1_odds'] = provider.get('homeAthleteOdds', {}).get('current', {}).get('moneyLine', {}).get('american')
                            fight['fighter_2_odds'] = provider.get('awayAthleteOdds', {}).get('current', {}).get('moneyLine', {}).get('american')
                        else:
                            fight['fighter_1_odds'] = provider.get('awayAthleteOdds', {}).get('current', {}).get('moneyLine', {}).get('american')
                            fight['fighter_2_odds'] = provider.get('homeAthleteOdds', {}).get('current', {}).get('moneyLine', {}).get('american')
                except Exception as e:
                    print(f"Error fetching odds: {e}")
                    fight['fighter_1_odds'] = None
                    fight['fighter_2_odds'] = None

            # Clean up - remove odds_url from response
            fight.pop('odds_url', None)

        # Sort fights by match number
        fights.sort(key=lambda x: x.get('match_number') or 999)

        return {
            "event": card,
            "fights": fights,
            "total_fights": len(fights)
        }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"ESPN API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
