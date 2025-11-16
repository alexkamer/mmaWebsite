"""Fighter API endpoints."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..database.connection import execute_query, execute_query_one
from ..models.fighter import FighterBase, FighterDetail, FighterListResponse

router = APIRouter()


@router.get("/filters")
async def get_filter_options():
    """
    Get available filter options (weight classes, nationalities).
    """
    # Get weight classes with counts
    weight_class_query = """
        SELECT
            weight_class,
            COUNT(*) as count
        FROM athletes
        WHERE weight_class IS NOT NULL AND weight_class != ''
        GROUP BY weight_class
        ORDER BY count DESC
    """
    weight_classes = execute_query(weight_class_query)

    # Get nationalities with counts
    nationality_query = """
        SELECT
            association as nationality,
            COUNT(*) as count
        FROM athletes
        WHERE association IS NOT NULL AND association != ''
        GROUP BY association
        ORDER BY count DESC
        LIMIT 50
    """
    nationalities = execute_query(nationality_query)

    return {
        "weight_classes": weight_classes,
        "nationalities": nationalities
    }


@router.get("/", response_model=FighterListResponse)
async def list_fighters(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    weight_class: Optional[str] = None,
    weight_classes: Optional[str] = Query(None, description="Comma-separated weight classes"),
    nationality: Optional[str] = Query(None, description="Fighter nationality/country"),
    starts_with: Optional[str] = Query(None, description="Filter by first letter of name"),
):
    """
    Get list of fighters with pagination and optional filtering.
    Supports multiple weight classes via comma-separated values.
    Supports filtering by first letter of name.
    """
    offset = (page - 1) * page_size

    # Build query
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(full_name LIKE ? OR display_name LIKE ? OR nickname LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    # Support both single weight_class and multiple weight_classes
    if weight_classes:
        wc_list = [wc.strip() for wc in weight_classes.split(",")]
        placeholders = ",".join(["?" for _ in wc_list])
        where_clauses.append(f"weight_class IN ({placeholders})")
        params.extend(wc_list)
    elif weight_class:
        where_clauses.append("weight_class = ?")
        params.append(weight_class)

    if nationality:
        where_clauses.append("association = ?")
        params.append(nationality)

    if starts_with:
        # Filter by first letter of display_name or full_name
        letter = starts_with.upper()
        where_clauses.append("(UPPER(SUBSTR(COALESCE(display_name, full_name), 1, 1)) = ?)")
        params.append(letter)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM athletes WHERE {where_sql}"
    count_result = execute_query_one(count_query, tuple(params))
    total = count_result["total"] if count_result else 0

    # Get fighters with records
    query = f"""
        SELECT
            a.id,
            COALESCE(a.display_name, a.full_name, 'Unknown') as name,
            a.nickname,
            a.headshot_url as image_url,
            a.weight_class,
            a.association as nationality,
            (SELECT COUNT(*) FROM fights f
             WHERE (f.fighter_1_id = a.id AND f.fighter_1_winner = 1)
                OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 1)) as wins,
            (SELECT COUNT(*) FROM fights f
             WHERE (f.fighter_1_id = a.id AND f.fighter_1_winner = 0 AND f.fighter_2_winner = 1)
                OR (f.fighter_2_id = a.id AND f.fighter_2_winner = 0 AND f.fighter_1_winner = 1)) as losses,
            (SELECT COUNT(*) FROM fights f
             WHERE (f.fighter_1_id = a.id OR f.fighter_2_id = a.id)
               AND f.fighter_1_winner = 0 AND f.fighter_2_winner = 0) as draws
        FROM athletes a
        WHERE {where_sql} AND (a.display_name IS NOT NULL OR a.full_name IS NOT NULL)
        ORDER BY COALESCE(a.display_name, a.full_name)
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])

    fighters = execute_query(query, tuple(params))

    return {
        "fighters": fighters,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{fighter_id}", response_model=FighterDetail)
async def get_fighter(fighter_id: int):
    """
    Get detailed information about a specific fighter.
    """
    query = """
        SELECT
            id,
            COALESCE(display_name, full_name, 'Unknown') as name,
            nickname,
            headshot_url as image_url,
            weight_class,
            association as nationality,
            display_height as height,
            display_weight as weight,
            reach,
            stance,
            date_of_birth
        FROM athletes
        WHERE id = ?
    """

    fighter = execute_query_one(query, (fighter_id,))

    if not fighter:
        raise HTTPException(status_code=404, detail="Fighter not found")

    # Get fight record
    record_query = """
        SELECT
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 1) OR (fighter_2_id = ? AND fighter_2_winner = 1)
                THEN 1 ELSE 0
            END) as wins,
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 0 AND fighter_2_winner = 1) OR
                     (fighter_2_id = ? AND fighter_2_winner = 0 AND fighter_1_winner = 1)
                THEN 1 ELSE 0
            END) as losses,
            SUM(CASE
                WHEN (fighter_1_id = ? OR fighter_2_id = ?) AND fighter_1_winner = 0 AND fighter_2_winner = 0
                THEN 1 ELSE 0
            END) as draws
        FROM fights
        WHERE fighter_1_id = ? OR fighter_2_id = ?
    """
    record = execute_query_one(record_query, (fighter_id, fighter_id, fighter_id, fighter_id, fighter_id, fighter_id, fighter_id, fighter_id))

    # Add record to fighter data
    fighter_dict = dict(fighter)
    if record:
        fighter_dict.update({
            "wins": record.get("wins", 0),
            "losses": record.get("losses", 0),
            "draws": record.get("draws", 0),
            "no_contests": 0  # Not tracking NC in current schema
        })

    return fighter_dict


@router.get("/{fighter_id}/fights")
async def get_fighter_fights(
    fighter_id: int,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get fight history for a specific fighter.
    """
    query = """
        SELECT
            f.year_league_event_id_fight_id_f1_f2 as id,
            c.event_name,
            c.date,
            f.league as promotion,
            CASE
                WHEN f.fighter_1_id = ? THEN COALESCE(a2.display_name, a2.full_name, 'Unknown')
                ELSE COALESCE(a1.display_name, a1.full_name, 'Unknown')
            END as opponent_name,
            CASE
                WHEN f.fighter_1_id = ? THEN a2.id
                ELSE a1.id
            END as opponent_id,
            f.fighter_1_id,
            f.fighter_2_id,
            f.fighter_1_winner,
            f.fighter_2_winner,
            f.result_display_name as method,
            f.end_round as round,
            f.end_time as time
        FROM fights f
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        LEFT JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE f.fighter_1_id = ? OR f.fighter_2_id = ?
        ORDER BY c.date DESC, f.year_league_event_id_fight_id_f1_f2 DESC
        LIMIT ?
    """

    fights = execute_query(query, (fighter_id, fighter_id, fighter_id, fighter_id, limit))

    # Add win/loss/draw status
    for fight in fights:
        if fight["fighter_1_winner"] == 0 and fight["fighter_2_winner"] == 0:
            fight["result"] = "draw"
        elif (fight["fighter_1_id"] == fighter_id and fight["fighter_1_winner"] == 1) or \
             (fight["fighter_2_id"] == fighter_id and fight["fighter_2_winner"] == 1):
            fight["result"] = "win"
        else:
            fight["result"] = "loss"

    return {"fights": fights}


@router.get("/compare/{fighter1_id}/{fighter2_id}")
async def compare_fighters(fighter1_id: int, fighter2_id: int):
    """
    Compare two fighters side-by-side with detailed stats and head-to-head history.
    """
    # Get both fighters' details
    fighters_query = """
        SELECT
            id,
            COALESCE(display_name, full_name, 'Unknown') as name,
            nickname,
            headshot_url as image_url,
            weight_class,
            association as nationality,
            display_height as height,
            display_weight as weight,
            reach,
            stance,
            date_of_birth,
            age
        FROM athletes
        WHERE id IN (?, ?)
    """
    fighters = execute_query(fighters_query, (fighter1_id, fighter2_id))

    if len(fighters) != 2:
        raise HTTPException(status_code=404, detail="One or both fighters not found")

    # Map fighters to correct positions
    fighter1 = next((f for f in fighters if f['id'] == fighter1_id), None)
    fighter2 = next((f for f in fighters if f['id'] == fighter2_id), None)

    if not fighter1 or not fighter2:
        raise HTTPException(status_code=404, detail="One or both fighters not found")

    # Get fight records for both fighters
    record_query = """
        SELECT
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 1) OR (fighter_2_id = ? AND fighter_2_winner = 1)
                THEN 1 ELSE 0
            END) as wins,
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 0 AND fighter_2_winner = 1) OR
                     (fighter_2_id = ? AND fighter_2_winner = 0 AND fighter_1_winner = 1)
                THEN 1 ELSE 0
            END) as losses,
            SUM(CASE
                WHEN (fighter_1_id = ? OR fighter_2_id = ?) AND fighter_1_winner = 0 AND fighter_2_winner = 0
                THEN 1 ELSE 0
            END) as draws,
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 1) OR (fighter_2_id = ? AND fighter_2_winner = 1)
                THEN
                    CASE
                        WHEN result_display_name LIKE '%KO%' OR result_display_name LIKE '%TKO%' THEN 1
                        ELSE 0
                    END
                ELSE 0
            END) as ko_wins,
            SUM(CASE
                WHEN (fighter_1_id = ? AND fighter_1_winner = 1) OR (fighter_2_id = ? AND fighter_2_winner = 1)
                THEN
                    CASE
                        WHEN result_display_name LIKE '%Submission%' THEN 1
                        ELSE 0
                    END
                ELSE 0
            END) as sub_wins
        FROM fights
        WHERE fighter_1_id = ? OR fighter_2_id = ?
    """

    record1 = execute_query_one(record_query, (
        fighter1_id, fighter1_id, fighter1_id, fighter1_id, fighter1_id, fighter1_id,
        fighter1_id, fighter1_id, fighter1_id, fighter1_id, fighter1_id, fighter1_id
    ))
    record2 = execute_query_one(record_query, (
        fighter2_id, fighter2_id, fighter2_id, fighter2_id, fighter2_id, fighter2_id,
        fighter2_id, fighter2_id, fighter2_id, fighter2_id, fighter2_id, fighter2_id
    ))

    # Get head-to-head fights
    h2h_query = """
        SELECT
            f.year_league_event_id_fight_id_f1_f2 as id,
            c.event_name,
            c.date,
            f.league as promotion,
            f.fighter_1_id,
            f.fighter_2_id,
            f.fighter_1_winner,
            f.fighter_2_winner,
            f.result_display_name as method,
            f.end_round as round,
            f.end_time as time,
            f.weight_class
        FROM fights f
        LEFT JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE (f.fighter_1_id = ? AND f.fighter_2_id = ?) OR (f.fighter_1_id = ? AND f.fighter_2_id = ?)
        ORDER BY c.date DESC
    """
    h2h_fights = execute_query(h2h_query, (fighter1_id, fighter2_id, fighter2_id, fighter1_id))

    # Process head-to-head results
    h2h_summary = {"fighter1_wins": 0, "fighter2_wins": 0, "draws": 0}
    for fight in h2h_fights:
        if fight["fighter_1_winner"] == 0 and fight["fighter_2_winner"] == 0:
            h2h_summary["draws"] += 1
            fight["winner_id"] = None
        elif fight["fighter_1_winner"] == 1:
            if fight["fighter_1_id"] == fighter1_id:
                h2h_summary["fighter1_wins"] += 1
                fight["winner_id"] = fighter1_id
            else:
                h2h_summary["fighter2_wins"] += 1
                fight["winner_id"] = fighter2_id
        else:
            if fight["fighter_2_id"] == fighter1_id:
                h2h_summary["fighter1_wins"] += 1
                fight["winner_id"] = fighter1_id
            else:
                h2h_summary["fighter2_wins"] += 1
                fight["winner_id"] = fighter2_id

    # Get recent fights (last 5) for both fighters
    recent_query = """
        SELECT
            f.year_league_event_id_fight_id_f1_f2 as id,
            c.event_name,
            c.date,
            CASE
                WHEN f.fighter_1_id = ? THEN COALESCE(a2.display_name, a2.full_name, 'Unknown')
                ELSE COALESCE(a1.display_name, a1.full_name, 'Unknown')
            END as opponent_name,
            f.fighter_1_id,
            f.fighter_2_id,
            f.fighter_1_winner,
            f.fighter_2_winner,
            f.result_display_name as method
        FROM fights f
        LEFT JOIN athletes a1 ON f.fighter_1_id = a1.id
        LEFT JOIN athletes a2 ON f.fighter_2_id = a2.id
        LEFT JOIN cards c ON f.event_id = c.event_id AND f.league = c.league
        WHERE f.fighter_1_id = ? OR f.fighter_2_id = ?
        ORDER BY c.date DESC
        LIMIT 5
    """

    recent1 = execute_query(recent_query, (fighter1_id, fighter1_id, fighter1_id))
    recent2 = execute_query(recent_query, (fighter2_id, fighter2_id, fighter2_id))

    # Add win/loss/draw status to recent fights
    for fight in recent1:
        if fight["fighter_1_winner"] == 0 and fight["fighter_2_winner"] == 0:
            fight["result"] = "draw"
        elif (fight["fighter_1_id"] == fighter1_id and fight["fighter_1_winner"] == 1) or \
             (fight["fighter_2_id"] == fighter1_id and fight["fighter_2_winner"] == 1):
            fight["result"] = "win"
        else:
            fight["result"] = "loss"

    for fight in recent2:
        if fight["fighter_1_winner"] == 0 and fight["fighter_2_winner"] == 0:
            fight["result"] = "draw"
        elif (fight["fighter_1_id"] == fighter2_id and fight["fighter_1_winner"] == 1) or \
             (fight["fighter_2_id"] == fighter2_id and fight["fighter_2_winner"] == 1):
            fight["result"] = "win"
        else:
            fight["result"] = "loss"

    return {
        "fighter1": {
            **dict(fighter1),
            "record": {
                "wins": record1.get("wins", 0) if record1 else 0,
                "losses": record1.get("losses", 0) if record1 else 0,
                "draws": record1.get("draws", 0) if record1 else 0,
                "ko_wins": record1.get("ko_wins", 0) if record1 else 0,
                "sub_wins": record1.get("sub_wins", 0) if record1 else 0,
            },
            "recent_fights": recent1
        },
        "fighter2": {
            **dict(fighter2),
            "record": {
                "wins": record2.get("wins", 0) if record2 else 0,
                "losses": record2.get("losses", 0) if record2 else 0,
                "draws": record2.get("draws", 0) if record2 else 0,
                "ko_wins": record2.get("ko_wins", 0) if record2 else 0,
                "sub_wins": record2.get("sub_wins", 0) if record2 else 0,
            },
            "recent_fights": recent2
        },
        "head_to_head": {
            "fights": h2h_fights,
            "summary": h2h_summary
        }
    }
