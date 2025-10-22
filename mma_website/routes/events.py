from flask import Blueprint, render_template, request, jsonify
from mma_website.services.events_service import (
    get_event_years, 
    get_event_year_for_event, 
    get_events_for_year, 
    get_event_details,
    get_fight_stats
)

bp = Blueprint('events', __name__, url_prefix='/events')

@bp.route('/')
def events():
    """Events listing page"""
    # Get filter parameters from request
    selected_year = request.args.get('year')
    selected_event_id = request.args.get('event_id')
    
    # Get all available years
    years = get_event_years()
    
    # If event_id provided but no year, get the year for that event
    if selected_event_id and not selected_year:
        try:
            event_id = int(selected_event_id)
            selected_year = get_event_year_for_event(event_id)
        except (ValueError, TypeError):
            # Handle invalid event_id
            pass
    
    # Get events for the selected year
    events_list = []
    if selected_year:
        events_list = get_events_for_year(selected_year)
    
    # Get details for the selected event
    selected_event = None
    if selected_event_id:
        try:
            event_id = int(selected_event_id)
            selected_event = get_event_details(event_id)
        except (ValueError, TypeError):
            # Handle invalid event_id
            pass
    
    return render_template('events.html',
                         years=years,
                         selected_year=selected_year,
                         events_list=events_list,
                         selected_event=selected_event)

@bp.route('/<int:event_id>')
def event_detail(event_id):
    """Individual event detail page"""
    event = get_event_details(event_id)
    
    if not event:
        return render_template('events.html', events=[], error="Event not found")
    
    return render_template('event_detail.html', 
                         event=event, 
                         fights=event.get('fights', []))

@bp.route('/api/fight-stats/<fight_id>')
def api_fight_stats(fight_id):
    """API endpoint for fight statistics"""
    stats = get_fight_stats(fight_id)
    
    if 'error' in stats:
        return jsonify(stats), 404
        
    return jsonify(stats)