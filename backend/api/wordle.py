"""Fighter Wordle game endpoints."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException
import hashlib

from ..database.connection import execute_query, execute_query_one

router = APIRouter()


def get_daily_fighter_id() -> int:
    """
    Get the fighter ID for today's Wordle.
    Uses a deterministic hash based on the date to select the same fighter all day.
    """
    # Get today's date as seed
    today = date.today().isoformat()

    # Get count of UFC fighters
    count_result = execute_query_one("""
        SELECT COUNT(*) as total
        FROM athletes
        WHERE weight_class IS NOT NULL
        AND weight_class LIKE '%UFC%'
        AND (display_name IS NOT NULL OR full_name IS NOT NULL)
    """)

    if not count_result or count_result['total'] == 0:
        raise HTTPException(status_code=500, detail="No fighters available")

    total_fighters = count_result['total']

    # Use hash of date to deterministically select a fighter
    hash_value = int(hashlib.sha256(today.encode()).hexdigest(), 16)
    fighter_index = hash_value % total_fighters

    # Get the fighter at that index
    fighter = execute_query_one(f"""
        SELECT id
        FROM athletes
        WHERE weight_class IS NOT NULL
        AND weight_class LIKE '%UFC%'
        AND (display_name IS NOT NULL OR full_name IS NOT NULL)
        ORDER BY id
        LIMIT 1 OFFSET {fighter_index}
    """)

    if not fighter:
        raise HTTPException(status_code=500, detail="Failed to select daily fighter")

    return fighter['id']


def get_weight_class_category(weight_class: Optional[str]) -> str:
    """Categorize weight classes into groups."""
    if not weight_class:
        return "unknown"

    wc = weight_class.lower()

    if 'flyweight' in wc or 'straw' in wc:
        return "flyweight"
    elif 'bantam' in wc:
        return "bantamweight"
    elif 'feather' in wc:
        return "featherweight"
    elif 'light' in wc and 'heavy' not in wc:
        return "lightweight"
    elif 'welter' in wc:
        return "welterweight"
    elif 'middle' in wc:
        return "middleweight"
    elif 'light heavy' in wc or 'light-heavy' in wc:
        return "light_heavyweight"
    elif 'heavy' in wc and 'light' not in wc:
        return "heavyweight"
    else:
        return "unknown"


@router.get("/daily")
async def get_daily_wordle():
    """Get information about today's Fighter Wordle (without revealing the answer)."""
    fighter_id = get_daily_fighter_id()

    # Get basic stats without revealing identity
    fighter = execute_query_one("""
        SELECT weight_class, age
        FROM athletes
        WHERE id = ?
    """, (fighter_id,))

    if not fighter:
        raise HTTPException(status_code=404, detail="Fighter not found")

    return {
        "date": date.today().isoformat(),
        "hint": f"This fighter competes in the {fighter['weight_class'] or 'UFC'} division",
    }


@router.post("/guess")
async def submit_guess(guess_id: int):
    """
    Submit a guess for today's Fighter Wordle.
    Returns hints about how close the guess is.
    """
    target_id = get_daily_fighter_id()

    # Get target fighter info
    target = execute_query_one("""
        SELECT
            id,
            COALESCE(display_name, full_name) as name,
            weight_class,
            association as nationality,
            age,
            headshot_url as image_url
        FROM athletes
        WHERE id = ?
    """, (target_id,))

    # Get guessed fighter info
    guess = execute_query_one("""
        SELECT
            id,
            COALESCE(display_name, full_name) as name,
            weight_class,
            association as nationality,
            age,
            headshot_url as image_url
        FROM athletes
        WHERE id = ?
    """, (guess_id,))

    if not guess:
        raise HTTPException(status_code=404, detail="Guessed fighter not found")

    if not target:
        raise HTTPException(status_code=500, detail="Daily fighter not found")

    # Check if correct
    is_correct = guess_id == target_id

    # Calculate hints
    hints = {
        "weight_class": "⬜",  # wrong
        "nationality": "⬜",
        "age": "⬜",
    }

    # Weight class hint
    guess_wc_cat = get_weight_class_category(guess.get('weight_class'))
    target_wc_cat = get_weight_class_category(target.get('weight_class'))

    if guess_wc_cat == target_wc_cat:
        hints["weight_class"] = "🟩"  # exact match
    elif guess_wc_cat != "unknown" and target_wc_cat != "unknown":
        # Check if adjacent weight classes
        wc_order = ["flyweight", "bantamweight", "featherweight", "lightweight",
                    "welterweight", "middleweight", "light_heavyweight", "heavyweight"]
        try:
            guess_idx = wc_order.index(guess_wc_cat)
            target_idx = wc_order.index(target_wc_cat)
            if abs(guess_idx - target_idx) <= 1:
                hints["weight_class"] = "🟨"  # close
        except ValueError:
            pass

    # Nationality hint
    if guess.get('nationality') and target.get('nationality'):
        if guess['nationality'].lower() == target['nationality'].lower():
            hints["nationality"] = "🟩"

    # Age hint
    if guess.get('age') and target.get('age'):
        age_diff = abs(int(guess['age']) - int(target['age']))
        if age_diff == 0:
            hints["age"] = "🟩"
        elif age_diff <= 3:
            hints["age"] = "🟨"

    response = {
        "correct": is_correct,
        "guess": {
            "id": guess['id'],
            "name": guess['name'],
            "weight_class": guess.get('weight_class'),
            "nationality": guess.get('nationality'),
            "age": guess.get('age'),
            "image_url": guess.get('image_url'),
        },
        "hints": hints,
    }

    # If correct, reveal the target
    if is_correct:
        response["target"] = {
            "id": target['id'],
            "name": target['name'],
            "weight_class": target.get('weight_class'),
            "nationality": target.get('nationality'),
            "age": target.get('age'),
            "image_url": target.get('image_url'),
        }

    return response


@router.get("/reveal")
async def reveal_answer():
    """
    Reveal today's Fighter Wordle answer.
    Use this when the player has used all attempts or given up.
    """
    target_id = get_daily_fighter_id()

    target = execute_query_one("""
        SELECT
            id,
            COALESCE(display_name, full_name) as name,
            weight_class,
            association as nationality,
            age,
            headshot_url as image_url
        FROM athletes
        WHERE id = ?
    """, (target_id,))

    if not target:
        raise HTTPException(status_code=500, detail="Daily fighter not found")

    return {
        "id": target['id'],
        "name": target['name'],
        "weight_class": target.get('weight_class'),
        "nationality": target.get('nationality'),
        "age": target.get('age'),
        "image_url": target.get('image_url'),
    }
