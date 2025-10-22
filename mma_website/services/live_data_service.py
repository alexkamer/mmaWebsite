"""
Live Data Service for MMA Intelligence
Integrates real-time UFC data from ESPN API and other sources
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class LiveDataService:
    """Service for fetching real-time MMA data from external APIs"""
    
    def __init__(self):
        self.espn_base_url = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache for live data
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time = self.cache[cache_key].get('cached_at', 0)
        return (time.time() - cached_time) < self.cache_ttl
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'cached_at': time.time()
        }
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get cached data if valid"""
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        return None
    
    def get_upcoming_events(self) -> Dict[str, Any]:
        """Get upcoming UFC events"""
        cache_key = "upcoming_events"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(f"{self.espn_base_url}/scoreboard", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = []
            if 'events' in data:
                for event in data['events'][:5]:  # Get next 5 events
                    event_info = {
                        'id': event.get('id'),
                        'name': event.get('name', ''),
                        'short_name': event.get('shortName', ''),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'venue': event.get('competitions', [{}])[0].get('venue', {}).get('fullName', ''),
                        'location': event.get('competitions', [{}])[0].get('venue', {}).get('address', {}).get('city', ''),
                        'fights': []
                    }
                    
                    # Get fights for this event
                    if 'competitions' in event:
                        for competition in event['competitions']:
                            if 'competitors' in competition and len(competition['competitors']) == 2:
                                fighter1 = competition['competitors'][0]
                                fighter2 = competition['competitors'][1]
                                
                                fight_info = {
                                    'fighter1': {
                                        'name': fighter1.get('athlete', {}).get('displayName', ''),
                                        'record': fighter1.get('record', {}).get('summary', ''),
                                        'photo': fighter1.get('athlete', {}).get('headshot', {}).get('href', '')
                                    },
                                    'fighter2': {
                                        'name': fighter2.get('athlete', {}).get('displayName', ''),
                                        'record': fighter2.get('record', {}).get('summary', ''),
                                        'photo': fighter2.get('athlete', {}).get('headshot', {}).get('href', '')
                                    },
                                    'weight_class': competition.get('weightClass', ''),
                                    'title_fight': competition.get('notes', [{}])[0].get('headline', '').lower().find('title') != -1
                                }
                                event_info['fights'].append(fight_info)
                    
                    events.append(event_info)
            
            result = {
                'success': True,
                'events': events,
                'last_updated': datetime.now().isoformat()
            }
            
            self._cache_data(cache_key, result)
            logger.info(f"Fetched {len(events)} upcoming UFC events")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {e}")
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
    
    def get_current_rankings(self) -> Dict[str, Any]:
        """Get current UFC rankings"""
        cache_key = "current_rankings"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Try to get rankings from ESPN
            response = requests.get(f"{self.espn_base_url}/athletes", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            divisions = {}
            if 'athletes' in data:
                for athlete in data['athletes'][:50]:  # Get top athletes
                    if 'position' in athlete and athlete['position']:
                        weight_class = athlete.get('weightClass', 'Unknown')
                        rank = athlete['position'].get('rank', 0)
                        
                        if weight_class not in divisions:
                            divisions[weight_class] = []
                        
                        fighter_info = {
                            'rank': rank,
                            'name': athlete.get('displayName', ''),
                            'record': athlete.get('record', {}).get('summary', ''),
                            'photo': athlete.get('headshot', {}).get('href', ''),
                            'nationality': athlete.get('citizenship', ''),
                            'is_champion': rank == 1
                        }
                        divisions[weight_class].append(fighter_info)
            
            # Sort each division by rank
            for division in divisions.values():
                division.sort(key=lambda x: x['rank'])
            
            result = {
                'success': True,
                'divisions': divisions,
                'last_updated': datetime.now().isoformat()
            }
            
            self._cache_data(cache_key, result)
            logger.info(f"Fetched rankings for {len(divisions)} divisions")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching rankings: {e}")
            return {
                'success': False,
                'error': str(e),
                'divisions': {}
            }
    
    def get_recent_results(self) -> Dict[str, Any]:
        """Get recent UFC fight results"""
        cache_key = "recent_results"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get events from the past 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            date_filter = f"?dates={start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
            response = requests.get(f"{self.espn_base_url}/scoreboard{date_filter}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            recent_fights = []
            if 'events' in data:
                for event in data['events']:
                    if event.get('status', {}).get('type', {}).get('name') == 'STATUS_FINAL':
                        event_info = {
                            'event_name': event.get('name', ''),
                            'date': event.get('date'),
                            'location': event.get('competitions', [{}])[0].get('venue', {}).get('fullName', ''),
                            'fights': []
                        }
                        
                        if 'competitions' in event:
                            for competition in event['competitions']:
                                if 'competitors' in competition and len(competition['competitors']) == 2:
                                    fighter1 = competition['competitors'][0]
                                    fighter2 = competition['competitors'][1]
                                    
                                    # Determine winner
                                    winner = None
                                    if fighter1.get('winner'):
                                        winner = fighter1.get('athlete', {}).get('displayName', '')
                                    elif fighter2.get('winner'):
                                        winner = fighter2.get('athlete', {}).get('displayName', '')
                                    
                                    fight_result = {
                                        'fighter1': fighter1.get('athlete', {}).get('displayName', ''),
                                        'fighter2': fighter2.get('athlete', {}).get('displayName', ''),
                                        'winner': winner,
                                        'method': competition.get('result', {}).get('description', ''),
                                        'weight_class': competition.get('weightClass', '')
                                    }
                                    event_info['fights'].append(fight_result)
                        
                        if event_info['fights']:  # Only add events with fights
                            recent_fights.append(event_info)
            
            result = {
                'success': True,
                'recent_fights': recent_fights[:10],  # Last 10 events
                'last_updated': datetime.now().isoformat()
            }
            
            self._cache_data(cache_key, result)
            logger.info(f"Fetched {len(recent_fights)} recent events")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching recent results: {e}")
            return {
                'success': False,
                'error': str(e),
                'recent_fights': []
            }
    
    def get_fighter_news(self, fighter_name: str) -> Dict[str, Any]:
        """Get recent news about a specific fighter"""
        cache_key = f"fighter_news_{fighter_name.lower()}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # This would integrate with news APIs
            # For now, return a placeholder structure
            result = {
                'success': True,
                'fighter': fighter_name,
                'news': [],
                'last_updated': datetime.now().isoformat(),
                'message': 'News integration coming soon'
            }
            
            self._cache_data(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching fighter news: {e}")
            return {
                'success': False,
                'error': str(e),
                'news': []
            }
    
    def get_betting_trends(self) -> Dict[str, Any]:
        """Get current betting trends and odds"""
        cache_key = "betting_trends"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # This would integrate with odds APIs
            # For now, return a placeholder
            result = {
                'success': True,
                'trends': [],
                'last_updated': datetime.now().isoformat(),
                'message': 'Betting integration coming soon'
            }
            
            self._cache_data(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching betting trends: {e}")
            return {
                'success': False,
                'error': str(e),
                'trends': []
            }
    
    def clear_cache(self):
        """Clear all cached live data"""
        self.cache.clear()
        logger.info("Live data cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        active_entries = sum(1 for key in self.cache.keys() if self._is_cache_valid(key))
        
        return {
            'total_cached_entries': len(self.cache),
            'active_entries': active_entries,
            'cache_ttl_seconds': self.cache_ttl,
            'cache_keys': list(self.cache.keys())
        }

# Global service instance
live_data_service = LiveDataService()