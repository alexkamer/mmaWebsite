from typing import Any, Optional, Union, Dict, List, Tuple, Callable
import re
from datetime import datetime

def validate_int(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None, default: Optional[int] = None) -> Optional[int]:
    """
    Validate that a value is an integer within an optional range
    
    Args:
        value: The value to validate
        min_value: Optional minimum value
        max_value: Optional maximum value
        default: Default value to return if validation fails
        
    Returns:
        The validated integer or default if validation fails
    """
    try:
        # Convert to int if it's not already
        if not isinstance(value, int):
            value = int(value)
            
        # Check range if specified
        if min_value is not None and value < min_value:
            return default
        if max_value is not None and value > max_value:
            return default
            
        return value
    except (ValueError, TypeError):
        return default

def validate_string(value: Any, min_length: int = 0, max_length: Optional[int] = None, 
                   pattern: Optional[str] = None, default: str = '') -> str:
    """
    Validate that a value is a string meeting specified criteria
    
    Args:
        value: The value to validate
        min_length: Minimum string length
        max_length: Optional maximum string length
        pattern: Optional regex pattern to match
        default: Default value to return if validation fails
        
    Returns:
        The validated string or default if validation fails
    """
    if value is None:
        return default
        
    try:
        # Convert to string if it's not already
        value = str(value).strip()
        
        # Check length constraints
        if len(value) < min_length:
            return default
        if max_length is not None and len(value) > max_length:
            return default
            
        # Check pattern if specified
        if pattern is not None and not re.match(pattern, value):
            return default
            
        return value
    except Exception:
        return default

def validate_date(value: Any, format_str: str = '%Y-%m-%d', 
                 min_date: Optional[datetime] = None, 
                 max_date: Optional[datetime] = None,
                 default: Optional[str] = None) -> Optional[str]:
    """
    Validate that a value is a valid date string
    
    Args:
        value: The date string to validate
        format_str: The expected date format
        min_date: Optional minimum date
        max_date: Optional maximum date
        default: Default value to return if validation fails
        
    Returns:
        The validated date string or default if validation fails
    """
    if value is None:
        return default
        
    try:
        # Parse the date
        date = datetime.strptime(str(value), format_str)
        
        # Check range if specified
        if min_date is not None and date < min_date:
            return default
        if max_date is not None and date > max_date:
            return default
            
        return value
    except Exception:
        return default

def validate_choice(value: Any, choices: List[Any], default: Optional[Any] = None) -> Optional[Any]:
    """
    Validate that a value is one of the allowed choices
    
    Args:
        value: The value to validate
        choices: List of allowed values
        default: Default value to return if validation fails
        
    Returns:
        The validated value or default if validation fails
    """
    if value is None:
        return default
        
    try:
        # Convert value to string for comparison if it's not already
        str_value = str(value).strip()
        str_choices = [str(choice) for choice in choices]
        
        if str_value in str_choices:
            # Return the original typed value from choices
            return choices[str_choices.index(str_value)]
        else:
            return default
    except Exception:
        return default

def validate_fighter_id(fighter_id: Any) -> Optional[int]:
    """
    Validate a fighter ID
    
    Args:
        fighter_id: The fighter ID to validate
        
    Returns:
        The validated fighter ID or None if invalid
    """
    return validate_int(fighter_id, min_value=1)

def validate_event_id(event_id: Any) -> Optional[int]:
    """
    Validate an event ID
    
    Args:
        event_id: The event ID to validate
        
    Returns:
        The validated event ID or None if invalid
    """
    return validate_int(event_id, min_value=1)

def validate_fight_id(fight_id: Any) -> Optional[str]:
    """
    Validate a fight ID (format: event_id_fight_id)
    
    Args:
        fight_id: The fight ID to validate
        
    Returns:
        The validated fight ID or None if invalid
    """
    # Check if the fight_id is in the correct format
    if not isinstance(fight_id, str):
        return None
        
    parts = fight_id.split('_')
    if len(parts) != 2:
        return None
        
    # Validate that both parts are integers
    try:
        event_id = int(parts[0])
        competition_id = int(parts[1])
        if event_id <= 0 or competition_id <= 0:
            return None
        return fight_id
    except (ValueError, TypeError):
        return None