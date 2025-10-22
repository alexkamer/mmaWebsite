"""
Query Caching Service for MMA Intelligence
Provides intelligent caching for frequently asked questions
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QueryCache:
    """In-memory cache for MMA query results with intelligent invalidation"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        """
        Initialize the query cache
        
        Args:
            max_size: Maximum number of cached queries
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_cache_key(self, question: str) -> str:
        """Generate a consistent cache key from the question"""
        # Normalize the question for better cache hits
        normalized = question.lower().strip()
        # Remove common variations that should match
        normalized = normalized.replace("'s", "").replace("?", "").replace(".", "")
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_expired(self, cache_entry: Dict) -> bool:
        """Check if a cache entry has expired"""
        if 'expires_at' not in cache_entry:
            return True
        return datetime.now() > cache_entry['expires_at']
    
    def _should_cache_question(self, question: str, classification: Dict) -> bool:
        """Determine if a question should be cached based on type"""
        if not classification:
            return False
            
        question_type = classification.get('question_type', '')
        
        # Cache record lookups and fight history (relatively static data)
        cacheable_types = ['record_lookup', 'fight_history', 'factual', 'events']
        
        # Don't cache predictions or real-time data
        non_cacheable_types = ['predictions', 'betting']
        
        if question_type in non_cacheable_types:
            return False
            
        if question_type in cacheable_types:
            return True
            
        # Cache high-confidence results
        confidence = classification.get('confidence', 0)
        return confidence >= 0.8
    
    def _evict_if_needed(self):
        """Remove oldest entries if cache is full"""
        if len(self.cache) >= self.max_size:
            # Remove the least recently accessed entry
            if self.access_times:
                oldest_key = min(self.access_times.keys(), 
                               key=lambda k: self.access_times[k])
                self.cache.pop(oldest_key, None)
                self.access_times.pop(oldest_key, None)
    
    def get(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result for a question
        
        Args:
            question: The user's question
            
        Returns:
            Cached result if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(question)
        
        if cache_key not in self.cache:
            self.miss_count += 1
            return None
        
        cache_entry = self.cache[cache_key]
        
        # Check if expired
        if self._is_expired(cache_entry):
            self.cache.pop(cache_key, None)
            self.access_times.pop(cache_key, None)
            self.miss_count += 1
            return None
        
        # Update access time
        self.access_times[cache_key] = time.time()
        self.hit_count += 1
        
        logger.info(f"Cache hit for question: {question[:50]}...")
        return cache_entry['result']
    
    def put(self, question: str, result: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache a query result
        
        Args:
            question: The user's question
            result: The query result to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        # Only cache successful results
        if not result.get('success'):
            return
        
        classification = result.get('classification', {})
        
        # Check if this type of question should be cached
        if not self._should_cache_question(question, classification):
            logger.debug(f"Not caching question type: {classification.get('question_type')}")
            return
        
        cache_key = self._generate_cache_key(question)
        
        # Evict old entries if needed
        self._evict_if_needed()
        
        # Calculate expiration time
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Store the result
        cache_entry = {
            'result': result,
            'cached_at': datetime.now(),
            'expires_at': expires_at,
            'question': question,
            'question_type': classification.get('question_type')
        }
        
        self.cache[cache_key] = cache_entry
        self.access_times[cache_key] = time.time()
        
        logger.info(f"Cached result for question: {question[:50]}... (expires in {ttl}s)")
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("Query cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }
    
    def get_cached_questions(self) -> list[dict]:
        """Get list of currently cached questions (for debugging)"""
        cached_questions = []
        for cache_entry in self.cache.values():
            cached_questions.append({
                'question': cache_entry['question'][:100] + '...' if len(cache_entry['question']) > 100 else cache_entry['question'],
                'question_type': cache_entry.get('question_type'),
                'cached_at': cache_entry['cached_at'].isoformat(),
                'expires_at': cache_entry['expires_at'].isoformat()
            })
        return cached_questions

# Global cache instance
query_cache = QueryCache(max_size=50, default_ttl=1800)  # 30 minutes default