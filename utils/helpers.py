import httpx
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_league_urls():
    league_urls_response = httpx.get("https://sports.core.api.espn.com/v2/sports/mma/leagues?lang=en&region=us&limit=100")

    league_urls_response.raise_for_status()

    league_urls_data = league_urls_response.json().get('items',[])

    league_urls = [x.get('$ref') for x in league_urls_data]

    return league_urls

# print(get_league_urls())

def fetch_league_json(url: str) -> dict:
    resp = httpx.get(url)
    resp.raise_for_status()
    return resp.json()

def map_league(f: dict) -> dict:
    return {
        "id":                 int(f.get("id")),
        "name":               f.get('name'),
        "displayName":        f.get('displayName'),
        "logo" :              f.get('logos',[{}])[0].get('href')
    }

def fetch_and_map_league(url: str) -> dict:
    raw = fetch_league_json(url)
    season_url = raw.get('seasons',{}).get('$ref')
    return map_league(raw), season_url


def fetch_league_seasons(league_url: str) -> dict[str, list[str]]:
    """
    Fetch the seasons JSON for one league URL and return a mapping:
       { league_name: [season_id, …] }
    """
    resp = httpx.get(league_url)
    resp.raise_for_status()
    data = resp.json()

    # Extract the league name from the URL path
    # e.g. "https://…/leagues/1234/seasons?lang=…"
    league_name = league_url.split('?')[0].split('/')[-2]

    # Pull each season ID out of the '$ref' field in items
    seasons = [
        item.get('$ref', '')
            .split('?')[0]
            .split('/')[-1]
        for item in data.get('items', [])
        if item.get('$ref')
    ]

    return {league_name: seasons}

def fetch_all_league_seasons(all_season_urls: list[str], max_workers: int = 25) -> list[dict[str, list[str]]]:

    urls = all_season_urls
    urls = [x + "&limit=100" for x in urls]
    results: list[dict[str, list[str]]] = []

    with ThreadPoolExecutor(max_workers=min(max_workers, len(urls))) as executor:
        # Schedule all tasks
        future_to_url = {
            executor.submit(fetch_league_seasons, url): url
            for url in urls
        }

        # As each finishes, gather its result or log errors
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                league_dict = future.result()
                results.append(league_dict)
            except Exception as exc:
                print(f"⚠️ Failed to fetch seasons for {url}: {exc!r}")

    return results


def get_athlete_info(athlete_url: str) -> dict:
    resp = httpx.get(athlete_url)
    resp.raise_for_status()
    try:
        f = resp.json()
        return {
        "id":                 int(f["id"]),
        "uid":                f.get("uid"),
        "guid":               f.get("guid"),
        "first_name":         f.get("firstName"),
        "last_name":          f.get("lastName"),
        "full_name":          f.get("fullName"),
        "display_name":       f.get("displayName"),
        "nickname":           f.get("nickname"),
        "short_name":         f.get("shortName"),
        "weight":             f.get("weight"),
        "display_weight":     f.get("displayWeight"),
        "height":             f.get("height"),
        "display_height":     f.get("displayHeight"),
        "age":                f.get("age"),
        "date_of_birth":      f.get("dateOfBirth"),
        "gender":             f.get("gender"),
        "is_active":          f.get("active"),
        "status":             f.get("status", {}).get("name"),
        "stance":             f.get("stance", {}).get("text"),
        "reach":              f.get("reach"),
        "weight_class":       f.get("weightClass", {}).get("text"),
        "weight_class_slug":  f.get("weightClass", {}).get("slug"),
        "association":        f.get("association", {}).get("name"),
        "association_city":   f.get("association", {}).get("location", {}).get("city"),
        "default_league":     f.get("defaultLeague", {}).get("$ref", "")
                                        .rstrip("/").split("/")[-1],
        "flag_url":           f.get("flag", {}).get("href"),
        "headshot_url":       f.get("headshot", {}).get("href")
    }
    except:
        return {}


def fetch_events_for_league_season(league: str, season: str) -> list[str]:
    """
    Fetches all event '$ref' URLs for one league/season combo.
    """
    all_urls = []
    url = (
        f"https://sports.core.api.espn.com/v2/"
        f"sports/mma/leagues/{league}/events/"
        f"?lang=en&region=us&dates={season}&limit=1000"
    )
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()

    if data.get('pageCount') > 1:
        all_urls.extend([item.get('$ref') for item in data.get('items', []) if item.get('$ref')])
        for page in range(2, data.get('pageCount') + 1):
            url = (
                f"https://sports.core.api.espn.com/v2/"
                f"sports/mma/leagues/{league}/events/"
                f"?lang=en&region=us&dates={season}&limit=1000&page={page}"
            )
            resp = httpx.get(url)
            resp.raise_for_status()
            data = resp.json()
            all_urls.extend([item.get('$ref') for item in data.get('items', []) if item.get('$ref')])
    else:
        all_urls.extend([item.get('$ref') for item in data.get('items', []) if item.get('$ref')])
    # if len(all_urls) >  900:
    #     print(f"Fetched {len(all_urls)} events for {league} {season}")
    # Pull out non-None '$ref' fields
    return all_urls



def process_event(url: str):
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()

    # parse date & id
    raw_date = data.get("date", "").split("T")[0]
    try:
        target = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except:
        return None, []
    eid = int(url.split("?")[0].split("/")[-1])
    if date.today() <= target or not data.get("competitions"):
        return None, []

    league = url.split("/events")[0].split("/")[-1]
    base   = data["competitions"][0].get("venue", {})
    year = target.year
    card = {
        "year_league_event_id_event_name": f"{year}_{league}_{eid}_{data.get('name')}",
        "league":      league,
        "event_name":  data.get("name"),
        "event_id":    eid,
        "date":        target,
        "venue_id":    base.get("id"),
        "venue_name":  base.get("fullName"),
        "country":     base.get("address", {}).get("country"),
        "state":       base.get("address", {}).get("state"),
        "city":        base.get("address", {}).get("city"),
    }

    evs = []
    for comp in data["competitions"]:
        event_status_url = f"https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/{eid}/competitions/{comp.get('id')}/status?lang=en&region=us"
        event_status_response = httpx.get(event_status_url)
        event_status_response.raise_for_status()
        event_status_data = event_status_response.json()

        ed = {
            "year_league_event_id_fight_id_f1_f2": f"{year}_{league}_{eid}_{comp.get('id')}_{comp.get('competitors')[0].get('id')}_{comp.get('competitors')[1].get('id')}",
            "fight_title" : comp.get('types',[{}])[0].get('text'),
            "boxscoreAvailable" : comp.get('boxscoreAvailable'),
            "playByPlayAvailable" : comp.get('playByPlayAvailable'),
            "summaryAvailable" : comp.get('summaryAvailable'),
            "league":            league,
            "event_id_fight_id" : f"{eid}_{comp.get('id')}",
            "event_id":          eid,
            "fight_id":          comp.get("id"),
            "odds_url":          comp.get("odds", {}).get("$ref"),
            "officials_url":     comp.get("officials", {}).get("$ref"),
            "rounds_format":     comp.get("format", {}).get("regulation", {}).get("periods"),
            "seconds_per_round": comp.get("format", {}).get("regulation", {}).get("clock"),
            "match_number":      comp.get("matchNumber"),
            "card_segment":      comp.get("cardSegment", {}).get("description"),
            "weight_class_id":   comp.get("type", {}).get("id"),
            "weight_class":      comp.get("type", {}).get("text"),
            "end_round" :        event_status_data.get("period"),
            "end_time" :         event_status_data.get("displayClock"),
            "result_display_name" : event_status_data.get("result",{}).get('displayName')
        }
        for i, c in enumerate(comp.get("competitors", []), start=1):
            ed[f"fighter_{i}_id"]         = c.get("id")
            ed[f"fighter_{i}_winner"]     = c.get("winner")
            ed[f"fighter_{i}_linescore"]  = c.get("linescores", {}).get("$ref")
            ed[f"fighter_{i}_statistics"] = c.get("statistics", {}).get("$ref")
        evs.append(ed)

    return card, evs

def get_odds_data(odds_url: str):
    all_odds = []
    response = httpx.get(odds_url)
    response.raise_for_status()
    try:
        odds_data = response.json()
        # print(odds_data)
        for provider in odds_data.get('items',[]):
            fight_dict = {}
            fight_dict['provider_id_fight_id'] = f"{provider.get('provider',{}).get('id')}_{odds_url.split('?')[0].split('/')[-2]}"
            fight_dict['fight_id'] = odds_url.split('?')[0].split('/')[-2]
            fight_dict['provider_id'] = provider.get('provider',{}).get('id')
            fight_dict['provider_name'] = provider.get('provider',{}).get('name')
            fight_dict['details'] = provider.get('details')

            # Away Athlete
            fight_dict['away_athlete_id'] = provider.get('awayAthleteOdds',{}).get('athlete',{}).get('$ref').split('?')[0].split('/')[-1]
            fight_dict['away_favorite'] = provider.get('awayAthleteOdds',{}).get('favorite')
            fight_dict['away_underdog'] = provider.get('awayAthleteOdds',{}).get('underdog')
            fight_dict['away_moneyLine_odds'] = provider.get('awayAthleteOdds',{}).get('moneyLine')
            fight_dict['away_moneyLine_odds_current_american'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('american')
            fight_dict['away_moneyLine_odds_current_decimal'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('decimal')
            fight_dict['away_moneyLine_odds_current_fractional'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('fraction')
            fight_dict['away_moneyLine_odds_current_value'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('value')

            fight_dict['away_victoryMethod_koTkoDq_value'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('value')
            fight_dict['away_victoryMethod_koTkoDq_american'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('american')
            fight_dict['away_victoryMethod_koTkoDq_decimal'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('decimal')
            fight_dict['away_victoryMethod_koTkoDq_fractional'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('fraction')
            
            fight_dict['away_victoryMethod_submission_value'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('value')
            fight_dict['away_victoryMethod_submission_american'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('american')
            fight_dict['away_victoryMethod_submission_decimal'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('decimal')
            fight_dict['away_victoryMethod_submission_fractional'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('fraction')

            fight_dict['away_victoryMethod_points_value'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('value')
            fight_dict['away_victoryMethod_points_american'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('american')
            fight_dict['away_victoryMethod_points_decimal'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('decimal')
            fight_dict['away_victoryMethod_points_fractional'] = provider.get('awayAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('fraction')

            # Home Athlete
            fight_dict['home_athlete_id'] = provider.get('homeAthleteOdds',{}).get('athlete',{}).get('$ref').split('?')[0].split('/')[-1]
            fight_dict['home_favorite'] = provider.get('homeAthleteOdds',{}).get('favorite')
            fight_dict['home_underdog'] = provider.get('homeAthleteOdds',{}).get('underdog')
            fight_dict['home_moneyLine_odds'] = provider.get('homeAthleteOdds',{}).get('moneyLine')
            fight_dict['home_moneyLine_odds_current_american'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('american')
            fight_dict['home_moneyLine_odds_current_decimal'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('decimal')
            fight_dict['home_moneyLine_odds_current_fractional'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('fraction')
            fight_dict['home_moneyLine_odds_current_value'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('moneyLine',{}).get('value')

            fight_dict['home_victoryMethod_koTkoDq_value'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('value')
            fight_dict['home_victoryMethod_koTkoDq_american'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('american')
            fight_dict['home_victoryMethod_koTkoDq_decimal'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('decimal')
            fight_dict['home_victoryMethod_koTkoDq_fractional'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('koTkoDq',{}).get('fraction')
            
            fight_dict['home_victoryMethod_submission_value'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('value')
            fight_dict['home_victoryMethod_submission_american'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('american')
            fight_dict['home_victoryMethod_submission_decimal'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('decimal')
            fight_dict['home_victoryMethod_submission_fractional'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('submission',{}).get('fraction')  
            
            fight_dict['home_victoryMethod_points_value'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('value')
            fight_dict['home_victoryMethod_points_american'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('american')
            fight_dict['home_victoryMethod_points_decimal'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('decimal')
            fight_dict['home_victoryMethod_points_fractional'] = provider.get('homeAthleteOdds',{}).get('current',{}).get('victoryMethod',{}).get('points',{}).get('fraction')
            
            fight_dict['rounds_over_under_value'] = provider.get('current',{}).get('total',{}).get('american')
            fight_dict['rounds_over_decimal'] = provider.get('current',{}).get('over',{}).get('decimal')
            fight_dict['rounds_over_fractional'] = provider.get('current',{}).get('over',{}).get('fraction')
            fight_dict['rounds_over_american'] = provider.get('current',{}).get('over',{}).get('american')
            fight_dict['rounds_under_decimal'] = provider.get('current',{}).get('under',{}).get('decimal')
            fight_dict['rounds_under_fractional'] = provider.get('current',{}).get('under',{}).get('fraction')
            fight_dict['rounds_under_american'] = provider.get('current',{}).get('under',{}).get('american')
            all_odds.append(fight_dict)


        return all_odds

    except:
        return {}
    




def get_stat_data(stat_url):
    stat_response = httpx.get(stat_url)
    stat_response.raise_for_status()
    try:
        stat_data = stat_response.json()
        event_id = stat_url.split('events/')[-1].split('/')[0]
        competition_id = stat_url.split('competitions/')[-1].split('/')[0]
        athlete_id = stat_url.split('competitors/')[-1].split('/')[0]

        stat_dict = {
            'event_competition_athlete_id': f"{event_id}_{competition_id}_{athlete_id}",
            'event_id': event_id,
            'competition_id': competition_id,
            'athlete_id': athlete_id
        }
        
        for stat in stat_data.get('splits',{}).get('categories',[{}])[0].get('stats',[]):

            stat_dict[stat['name']] = stat['value']

        return stat_dict
    except:
        print(f"Error fetching statistics for {stat_url}")

def process_next_event(url: str):
    resp = httpx.get(url)
    resp.raise_for_status()
    data = resp.json()

    # parse date & id
    raw_date = data.get("date", "").split("T")[0]
    try:
        target = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except:
        return None, []
    eid = int(url.split("?")[0].split("/")[-1])

    league = url.split("/events")[0].split("/")[-1]
    base   = data["competitions"][0].get("venue", {})

    card = {
        "league_event_id": f"{league}_{eid}",
        "league":      league,
        "event_name":  data.get("name"),
        "event_id":    eid,
        "date":        target,
        "venue_id":    base.get("id"),
        "venue_name":  base.get("fullName"),
        "country":     base.get("address", {}).get("country"),
        "state":       base.get("address", {}).get("state"),
        "city":        base.get("address", {}).get("city"),
    }

    # Batch fetch all competition statuses
    status_urls = []
    for comp in data["competitions"]:
        status_url = f"https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/{eid}/competitions/{comp.get('id')}/status?lang=en&region=us"
        status_urls.append((comp.get('id'), status_url))
    
    # Use ThreadPoolExecutor to fetch statuses concurrently
    status_data = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {
            executor.submit(httpx.get, url): (comp_id, url) 
            for comp_id, url in status_urls
        }
        for future in as_completed(future_to_url):
            comp_id, url = future_to_url[future]
            try:
                response = future.result()
                response.raise_for_status()
                status_data[comp_id] = response.json()
            except Exception as e:
                print(f"Error fetching status for competition {comp_id}: {e}")
                status_data[comp_id] = {}

    evs = []
    for comp in data["competitions"]:
        comp_id = comp.get('id')
        event_status_data = status_data.get(comp_id, {})

        ed = {
            "league_event_id_fight_id": f"{league}_{eid}_{comp_id}",
            "fight_title" : comp.get('types',[{}])[0].get('text'),
            "boxscoreAvailable" : comp.get('boxscoreAvailable'),
            "playByPlayAvailable" : comp.get('playByPlayAvailable'),
            "summaryAvailable" : comp.get('summaryAvailable'),
            "league":            league,
            "event_id_fight_id" : f"{eid}_{comp_id}",
            "event_id":          eid,
            "fight_id":          comp_id,
            "odds_url":          comp.get("odds", {}).get("$ref"),
            "officials_url":     comp.get("officials", {}).get("$ref"),
            "rounds_format":     comp.get("format", {}).get("regulation", {}).get("periods"),
            "seconds_per_round": comp.get("format", {}).get("regulation", {}).get("clock"),
            "match_number":      comp.get("matchNumber"),
            "card_segment":      comp.get("cardSegment", {}).get("description"),
            "weight_class_id":   comp.get("type", {}).get("id"),
            "weight_class":      comp.get("type", {}).get("text"),
            "end_round" :        event_status_data.get("period"),
            "end_time" :         event_status_data.get("displayClock"),
            "result_display_name" : event_status_data.get("result",{}).get('displayName')
        }
        for i, c in enumerate(comp.get("competitors", []), start=1):
            ed[f"fighter_{i}_id"]         = c.get("id")
            ed[f"fighter_{i}_winner"]     = c.get("winner")
            ed[f"fighter_{i}_linescore"]  = c.get("linescores", {}).get("$ref")
            ed[f"fighter_{i}_statistics"] = c.get("statistics", {}).get("$ref")
        evs.append(ed)

    return card, evs
