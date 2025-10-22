from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from mma_website import db
from mma_website.utils.text_utils import row_to_dict
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

# Configure logging
logger = logging.getLogger(__name__)

def execute_query(query_text: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a SQL query and return the results as a list of dictionaries
    
    Args:
        query_text: The SQL query text
        params: Query parameters
        
    Returns:
        List of dictionaries representing the query results
    """
    try:
        db_session = db.session
        result = db_session.execute(text(query_text), params or {})
        return [row_to_dict(row) for row in result]
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        logger.error(f"Query: {query_text}")
        logger.error(f"Params: {params}")
        raise

def execute_scalar(query_text: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Execute a SQL query and return a single scalar result
    
    Args:
        query_text: The SQL query text
        params: Query parameters
        
    Returns:
        The scalar result of the query
    """
    try:
        db_session = db.session
        return db_session.execute(text(query_text), params or {}).scalar()
    except Exception as e:
        logger.error(f"Database scalar query error: {str(e)}")
        logger.error(f"Query: {query_text}")
        logger.error(f"Params: {params}")
        raise

def get_record_by_id(table: str, id_column: str, record_id: Union[int, str]) -> Optional[Dict[str, Any]]:
    """
    Get a record by its ID
    
    Args:
        table: The table name
        id_column: The ID column name
        record_id: The ID value
        
    Returns:
        Dictionary representing the record or None if not found
    """
    try:
        query = f"SELECT * FROM {table} WHERE {id_column} = :id"
        result = execute_query(query, {"id": record_id})
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting record by ID: {str(e)}")
        logger.error(f"Table: {table}, ID column: {id_column}, ID: {record_id}")
        return None

def get_fighter_basic_info(fighter_id: int) -> Optional[Dict[str, Any]]:
    """
    Get basic fighter information
    
    Args:
        fighter_id: The fighter ID
        
    Returns:
        Dictionary with fighter basic info
    """
    try:
        query = """
            SELECT id, full_name, nickname, weight_class, headshot_url, 
                   height, weight, reach, gender, association
            FROM athletes
            WHERE id = :fighter_id
        """
        result = execute_query(query, {"fighter_id": fighter_id})
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting fighter basic info: {str(e)}")
        logger.error(f"Fighter ID: {fighter_id}")
        return None

def get_fighter_record(fighter_id: int) -> Dict[str, int]:
    """
    Get a fighter's win/loss/draw record
    
    Args:
        fighter_id: The fighter ID
        
    Returns:
        Dictionary with wins, losses, draws counts
    """
    try:
        wins_query = """
            SELECT COUNT(*) as wins
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 1)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 1)
        """
        
        losses_query = """
            SELECT COUNT(*) as losses
            FROM fights
            WHERE (fighter_1_id = :fighter_id AND fighter_1_winner = 0)
            OR (fighter_2_id = :fighter_id AND fighter_2_winner = 0)
            AND NOT (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """
        
        draws_query = """
            SELECT COUNT(*) as draws
            FROM fights
            WHERE (fighter_1_id = :fighter_id OR fighter_2_id = :fighter_id)
            AND (result_display_name LIKE '%Draw%' OR result_display_name LIKE '%No Contest%')
        """
        
        params = {"fighter_id": fighter_id}
        wins = execute_scalar(wins_query, params) or 0
        losses = execute_scalar(losses_query, params) or 0
        draws = execute_scalar(draws_query, params) or 0
        
        return {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "total": wins + losses + draws
        }
    except Exception as e:
        logger.error(f"Error getting fighter record: {str(e)}")
        logger.error(f"Fighter ID: {fighter_id}")
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0}

def get_upcoming_events(league: str = 'ufc', limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get upcoming events
    
    Args:
        league: League name (default: 'ufc')
        limit: Maximum number of events to return
        
    Returns:
        List of upcoming events
    """
    try:
        query = """
            SELECT event_id, event_name, date, venue_name, city, country
            FROM cards
            WHERE league = :league
            AND date > date('now')
            ORDER BY date ASC
            LIMIT :limit
        """
        events = execute_query(query, {"league": league, "limit": limit})
        
        # Format dates
        for event in events:
            if 'date' in event and event['date']:
                try:
                    from datetime import datetime
                    date = datetime.strptime(str(event['date']), '%Y-%m-%d %H:%M:%S.%f')
                    event['date'] = date.strftime('%m-%d-%Y')
                except Exception:
                    pass
                    
        return events
    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        logger.error(f"League: {league}, Limit: {limit}")
        return []

def add_to_db(data: Union[Dict[str, Any], List[Dict[str, Any]]], model_class: type) -> None:
    """
    Add one or more records to the database from a dictionary or list of dictionaries.
    Skips any records that would cause integrity errors.

    Args:
        data: A dictionary or list of dictionaries containing the data to insert
        model_class: The SQLAlchemy model class to use for insertion

    Example:
        # Add a single league
        league_data = {
            "id": 1,
            "name": "UFC",
            "displayName": "UFC",
            "logo": "https://example.com/logo.png"
        }
        add_to_db(league_data, League)

        # Add multiple leagues
        leagues_data = [
            {"id": 1, "name": "UFC", "displayName": "UFC", "logo": "https://example.com/logo1.png"},
            {"id": 2, "name": "Bellator", "displayName": "Bellator", "logo": "https://example.com/logo2.png"}
        ]
        add_to_db(leagues_data, League)
    """
    try:
        if isinstance(data, dict):
            # Single record
            try:
                record = model_class(**data)
                db.session.add(record)
                db.session.commit()
                # print(f"Successfully added record to {model_class.__tablename__}")
            except IntegrityError as e:
                db.session.rollback()
                print(f"Skipping duplicate record in {model_class.__tablename__}: {str(e)}")
        else:
            # Multiple records
            successful = 0
            for item in data:
                try:
                    record = model_class(**item)
                    db.session.add(record)
                    db.session.commit()
                    successful += 1
                except IntegrityError as e:
                    db.session.rollback()
                    print(f"Skipping duplicate record in {model_class.__tablename__}: {str(e)}")
                    continue
            print(f"Successfully added {successful} out of {len(data)} records to {model_class.__tablename__}")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding records to {model_class.__tablename__}: {str(e)}")
        raise