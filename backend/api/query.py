"""Natural language query endpoints for MMA data."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
import sqlite3
import re
from datetime import datetime

router = APIRouter()

DATABASE_PATH = "data/mma.db"


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_fighter_record_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions about fighter records like 'What is Conor McGregor's record?'"""
    patterns = [
        r"what(?:'s| is) (?:the record (?:of|for) )?(.+?)(?:'s)? record",
        r"how many (?:wins|fights) (?:does|has) (.+?)(?: have| had)?",
        r"(.+?)(?:'s)? (?:fight )?record",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            fighter_name = match.group(1).strip()
            return {"type": "fighter_record", "fighter_name": fighter_name}
    return None


def parse_fighter_comparison_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions comparing fighters like 'Who is taller, X or Y?'"""
    patterns = [
        r"who (?:is|has) (?:a )?(?:taller|bigger|heavier|longer reach|better record).+?(?:between )?(.+?) (?:or|and|vs) (.+?)(?:\?|$)",
        r"compare (.+?) (?:to|and|vs) (.+)",
        r"(?:is|does) (.+?) (?:taller|heavier|better).+? (?:than|vs) (.+?)(?:\?|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            fighter1 = match.group(1).strip()
            fighter2 = match.group(2).strip()
            return {"type": "fighter_comparison", "fighter1": fighter1, "fighter2": fighter2}
    return None


def parse_event_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions about events like 'When is the next UFC event?'"""
    patterns = [
        r"when (?:is|was) (?:the )?(next|last|upcoming) (?:ufc|bellator|pfl)? ?event",
        r"what(?:'s| is) (?:the )?(next|upcoming|last) (?:ufc|bellator|pfl)? ?(?:event|card)",
        r"(?:next|upcoming) (?:ufc|bellator|pfl) (?:event|card|fight)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            # Safely handle case where match.lastindex is None or no groups captured
            timing = match.group(1).lower() if match.lastindex and match.lastindex >= 1 else "next"
            return {"type": "event_query", "timing": timing}
    return None


def parse_fighter_fights_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions about fighter's fights like 'Who did X fight last?'"""
    patterns = [
        r"who did (.+?) (?:fight|beat|lose to)(?: last| recently)?",
        r"(?:who(?:'s| is)|what(?:'s| is)) (.+?)(?:'s)? (?:last|most recent|next) (?:fight|opponent)",
        r"(.+?)(?:'s)? (?:last|most recent|next) (?:fight|opponent|match)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            fighter_name = match.group(1).strip()
            return {"type": "fighter_fights", "fighter_name": fighter_name}
    return None


def parse_rankings_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions about UFC rankings."""
    patterns = [
        r"who (?:is|are) (?:the )?(?:ufc )?([\w\s]+?) champion",
        r"(?:ufc )?([\w\s]+?) (?:champion|rankings)",
        r"what (?:are|is) (?:the )?(?:ufc )?([\w\s]+?) rankings",
        r"who(?:'s| is) (?:ranked|number|#) ?(\d+) (?:at|in) ([\w\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            # Safely handle case where match.lastindex is None or no groups captured
            division = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else None
            return {"type": "rankings", "division": division}
    return None


def parse_stats_query(question: str) -> Optional[Dict[str, Any]]:
    """Parse questions about fighter statistics."""
    patterns = [
        r"how (?:tall|heavy|old) (?:is|was) (.+?)(?:\?|$)",
        r"what(?:'s| is) (.+?)(?:'s)? (?:height|weight|age|reach|stance)(?:\?|$)",
        r"(.+?)(?:'s)? (?:height|weight|age|reach|stance)",
    ]

    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            fighter_name = match.group(1).strip()
            return {"type": "fighter_stats", "fighter_name": fighter_name}
    return None


def execute_fighter_record_query(fighter_name: str) -> Dict[str, Any]:
    """Get fighter's record."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Search for fighter
    cursor.execute("""
        SELECT id, full_name, nickname, headshot_url, weight_class
        FROM athletes
        WHERE LOWER(full_name) LIKE LOWER(?)
           OR LOWER(display_name) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{fighter_name}%", f"%{fighter_name}%"))

    fighter = cursor.fetchone()
    if not fighter:
        conn.close()
        return {"answer": f"I couldn't find a fighter named '{fighter_name}'.", "data": None}

    fighter_id = fighter["id"]

    # Get fight record
    cursor.execute("""
        SELECT
            SUM(CASE WHEN fighter_1_winner = 1 THEN 1 WHEN fighter_2_winner = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN (fighter_1_id = ? AND fighter_1_winner = 0 AND fighter_2_winner = 1)
                      OR (fighter_2_id = ? AND fighter_2_winner = 0 AND fighter_1_winner = 1) THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN fighter_1_winner = 0 AND fighter_2_winner = 0 THEN 1 ELSE 0 END) as draws,
            COUNT(*) as total_fights,
            SUM(CASE WHEN LOWER(result_display_name) LIKE '%ko%' OR LOWER(result_display_name) LIKE '%tko%' THEN 1 ELSE 0 END) as ko_wins,
            SUM(CASE WHEN LOWER(result_display_name) LIKE '%submission%' THEN 1 ELSE 0 END) as sub_wins
        FROM fights
        WHERE fighter_1_id = ? OR fighter_2_id = ?
    """, (fighter_id, fighter_id, fighter_id, fighter_id))

    record = cursor.fetchone()
    conn.close()

    wins = record["wins"] or 0
    losses = record["losses"] or 0
    draws = record["draws"] or 0

    fighter_display = fighter["full_name"]
    if fighter["nickname"]:
        fighter_display += f' "{fighter["nickname"]}"'

    answer = f"{fighter_display} has a record of {wins}-{losses}-{draws}"
    if fighter["weight_class"]:
        answer += f" in the {fighter['weight_class']} division"
    answer += "."

    return {
        "answer": answer,
        "data": {
            "fighter": dict(fighter),
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "ko_wins": record["ko_wins"] or 0,
            "sub_wins": record["sub_wins"] or 0,
        }
    }


def execute_fighter_stats_query(fighter_name: str) -> Dict[str, Any]:
    """Get fighter's stats."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name, nickname, headshot_url, weight_class,
               height, display_height, weight, display_weight,
               reach, stance, age, date_of_birth, association
        FROM athletes
        WHERE LOWER(full_name) LIKE LOWER(?)
           OR LOWER(display_name) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{fighter_name}%", f"%{fighter_name}%"))

    fighter = cursor.fetchone()
    conn.close()

    if not fighter:
        return {"answer": f"I couldn't find a fighter named '{fighter_name}'.", "data": None}

    fighter_display = fighter["full_name"]
    if fighter["nickname"]:
        fighter_display += f' "{fighter["nickname"]}"'

    stats = []
    if fighter["display_height"]:
        stats.append(f"Height: {fighter['display_height']}")
    if fighter["display_weight"]:
        stats.append(f"Weight: {fighter['display_weight']}")
    if fighter["reach"]:
        stats.append(f"Reach: {fighter['reach']}\"")
    if fighter["stance"]:
        stats.append(f"Stance: {fighter['stance']}")
    if fighter["age"]:
        stats.append(f"Age: {fighter['age']}")
    if fighter["weight_class"]:
        stats.append(f"Division: {fighter['weight_class']}")
    if fighter["association"]:
        stats.append(f"Nationality: {fighter['association']}")

    answer = f"{fighter_display}: " + ", ".join(stats) if stats else f"Limited stats available for {fighter_display}."

    return {
        "answer": answer,
        "data": dict(fighter)
    }


def execute_event_query(timing: str) -> Dict[str, Any]:
    """Get upcoming or recent event."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if timing in ["next", "upcoming"]:
        cursor.execute("""
            SELECT event_id, event_name, date, venue_name, city, state, country
            FROM cards
            WHERE date >= datetime('now')
            ORDER BY date ASC
            LIMIT 1
        """)
    else:  # last
        cursor.execute("""
            SELECT event_id, event_name, date, venue_name, city, state, country
            FROM cards
            WHERE date < datetime('now')
            ORDER BY date DESC
            LIMIT 1
        """)

    event = cursor.fetchone()
    conn.close()

    if not event:
        return {"answer": f"I couldn't find the {timing} event.", "data": None}

    event_date = datetime.fromisoformat(event["date"].replace('Z', '+00:00'))
    formatted_date = event_date.strftime("%B %d, %Y")

    location = []
    if event["city"]:
        location.append(event["city"])
    if event["state"]:
        location.append(event["state"])
    if event["country"]:
        location.append(event["country"])
    location_str = ", ".join(location)

    answer = f"The {timing} event is {event['event_name']} on {formatted_date}"
    if location_str:
        answer += f" in {location_str}"
    if event["venue_name"]:
        answer += f" at {event['venue_name']}"
    answer += "."

    return {
        "answer": answer,
        "data": dict(event)
    }


def execute_rankings_query(division: Optional[str]) -> Dict[str, Any]:
    """Get UFC rankings."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if division:
        cursor.execute("""
            SELECT r.rank, r.fighter_name, r.division, r.is_champion, r.is_interim_champion,
                   a.id as fighter_id, a.headshot_url
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(r.fighter_name) = LOWER(a.full_name)
            WHERE LOWER(r.division) LIKE LOWER(?)
            ORDER BY r.rank ASC
            LIMIT 11
        """, (f"%{division}%",))

        rankings = cursor.fetchall()
        conn.close()

        if not rankings:
            return {"answer": f"I couldn't find rankings for '{division}'.", "data": None}

        champion = next((r for r in rankings if r["is_champion"]), None)

        if champion:
            answer = f"The {rankings[0]['division']} champion is {champion['fighter_name']}. "
            top_contenders = [r["fighter_name"] for r in rankings if r["rank"] >= 1 and r["rank"] <= 3]
            if top_contenders:
                answer += f"Top contenders: {', '.join(top_contenders)}."
        else:
            answer = f"Top ranked fighters in {rankings[0]['division']}: " + ", ".join(
                [f"#{r['rank']} {r['fighter_name']}" for r in rankings[:5]]
            )

        return {
            "answer": answer,
            "data": [dict(r) for r in rankings]
        }
    else:
        # Get all champions
        cursor.execute("""
            SELECT r.division, r.fighter_name, r.is_interim_champion,
                   a.id as fighter_id, a.headshot_url
            FROM ufc_rankings r
            LEFT JOIN athletes a ON LOWER(r.fighter_name) = LOWER(a.full_name)
            WHERE r.is_champion = 1
            ORDER BY r.division
        """)

        champions = cursor.fetchall()
        conn.close()

        if not champions:
            return {"answer": "I couldn't find current UFC champions.", "data": None}

        champ_list = [f"{c['division']}: {c['fighter_name']}" for c in champions]
        answer = "Current UFC Champions: " + ", ".join(champ_list)

        return {
            "answer": answer,
            "data": [dict(c) for c in champions]
        }


def execute_fighter_fights_query(fighter_name: str) -> Dict[str, Any]:
    """Get fighter's recent fights."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Find fighter
    cursor.execute("""
        SELECT id, full_name, nickname
        FROM athletes
        WHERE LOWER(full_name) LIKE LOWER(?)
           OR LOWER(display_name) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{fighter_name}%", f"%{fighter_name}%"))

    fighter = cursor.fetchone()
    if not fighter:
        conn.close()
        return {"answer": f"I couldn't find a fighter named '{fighter_name}'.", "data": None}

    fighter_id = fighter["id"]

    # Get recent fights
    cursor.execute("""
        SELECT f.*, c.event_name, c.date,
               a1.full_name as fighter1_name, a2.full_name as fighter2_name
        FROM fights f
        JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        JOIN athletes a1 ON f.fighter_1_id = a1.id
        JOIN athletes a2 ON f.fighter_2_id = a2.id
        WHERE f.fighter_1_id = ? OR f.fighter_2_id = ?
        ORDER BY c.date DESC
        LIMIT 5
    """, (fighter_id, fighter_id))

    fights = cursor.fetchall()
    conn.close()

    if not fights:
        return {"answer": f"I couldn't find recent fights for {fighter['full_name']}.", "data": None}

    last_fight = fights[0]
    opponent_name = last_fight["fighter2_name"] if last_fight["fighter_1_id"] == fighter_id else last_fight["fighter1_name"]

    result = "won" if (
        (last_fight["fighter_1_id"] == fighter_id and last_fight["fighter_1_winner"]) or
        (last_fight["fighter_2_id"] == fighter_id and last_fight["fighter_2_winner"])
    ) else "lost"

    fight_date = datetime.fromisoformat(last_fight["date"].replace('Z', '+00:00'))
    formatted_date = fight_date.strftime("%B %d, %Y")

    answer = f"{fighter['full_name']} {result} against {opponent_name} at {last_fight['event_name']} on {formatted_date}"
    if last_fight["result_display_name"]:
        answer += f" by {last_fight['result_display_name']}"
    answer += "."

    return {
        "answer": answer,
        "data": [dict(f) for f in fights]
    }


@router.post("/")
async def process_query(question: str = Query(..., description="Natural language question about MMA data")):
    """
    Process a natural language query and return an answer.

    Supports queries like:
    - "What is Conor McGregor's record?"
    - "How tall is Jon Jones?"
    - "When is the next UFC event?"
    - "Who is the UFC heavyweight champion?"
    - "Who did Khabib fight last?"
    """
    question = question.strip()

    # Try to parse and execute the query
    parsers = [
        (parse_fighter_record_query, execute_fighter_record_query),
        (parse_stats_query, execute_fighter_stats_query),
        (parse_event_query, execute_event_query),
        (parse_rankings_query, execute_rankings_query),
        (parse_fighter_fights_query, execute_fighter_fights_query),
    ]

    for parser, executor in parsers:
        parsed = parser(question)
        if parsed:
            query_type = parsed.pop("type")
            try:
                result = executor(**parsed)
                result["query_type"] = query_type
                result["question"] = question
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")

    # No matching pattern found
    return {
        "question": question,
        "answer": "I'm not sure how to answer that question. Try asking about fighter records, stats, upcoming events, or UFC rankings.",
        "data": None,
        "query_type": "unknown",
        "suggestions": [
            "What is [fighter name]'s record?",
            "How tall is [fighter name]?",
            "When is the next UFC event?",
            "Who is the UFC [division] champion?",
            "Who did [fighter name] fight last?",
        ]
    }


@router.get("/examples")
async def get_example_queries():
    """Get example queries that the system can handle."""
    return {
        "examples": [
            {
                "category": "Fighter Records",
                "queries": [
                    "What is Conor McGregor's record?",
                    "How many wins does Jon Jones have?",
                    "What is Khabib Nurmagomedov's fight record?",
                ]
            },
            {
                "category": "Fighter Stats",
                "queries": [
                    "How tall is Jon Jones?",
                    "What is Israel Adesanya's reach?",
                    "How old is Amanda Nunes?",
                ]
            },
            {
                "category": "Events",
                "queries": [
                    "When is the next UFC event?",
                    "What is the upcoming UFC card?",
                    "When was the last UFC event?",
                ]
            },
            {
                "category": "Rankings",
                "queries": [
                    "Who is the UFC heavyweight champion?",
                    "What are the lightweight rankings?",
                    "Who are the UFC champions?",
                ]
            },
            {
                "category": "Fight History",
                "queries": [
                    "Who did Khabib fight last?",
                    "What was Conor McGregor's last fight?",
                    "Who did Jon Jones beat recently?",
                ]
            },
        ]
    }
