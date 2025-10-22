"""
Conversation Memory Service for MMA Intelligence
Tracks conversation context and provides better continuity
"""

import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Manages conversation context and history for better chatbot responses"""
    
    def __init__(self, max_conversations: int = 20, session_timeout: int = 1800):
        """
        Initialize conversation memory
        
        Args:
            max_conversations: Maximum number of conversations to keep in memory
            session_timeout: Session timeout in seconds (30 minutes default)
        """
        self.conversations = {}  # session_id -> conversation_data
        self.max_conversations = max_conversations
        self.session_timeout = session_timeout
    
    def _cleanup_expired_sessions(self):
        """Remove expired conversation sessions"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, conversation in self.conversations.items():
            last_activity = conversation.get('last_activity', current_time)
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            
            if (current_time - last_activity).seconds > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.conversations.pop(session_id, None)
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def _extract_context_entities(self, question: str, classification: Dict, data: list[dict]) -> Dict:
        """Extract key entities from the query for context tracking"""
        entities = {
            'fighters': [],
            'events': [],
            'weight_classes': [],
            'question_type': classification.get('question_type'),
            'keywords': []
        }
        
        # Extract fighter names from question
        question_lower = question.lower()
        common_names = ['jon jones', 'conor mcgregor', 'tom aspinall', 'daniel cormier', 
                       'amanda nunes', 'israel adesanya', 'khabib', 'anderson silva']
        
        for name in common_names:
            if name in question_lower:
                entities['fighters'].append(name.title())
        
        # Extract from data if available
        if data and len(data) > 0:
            first_row = data[0]
            
            # Look for fighter names in various fields
            name_fields = ['full_name', 'fighter_name', 'opponent', 'fighter_1', 'fighter_2']
            for field in name_fields:
                if field in first_row and first_row[field]:
                    entities['fighters'].append(str(first_row[field]))
            
            # Look for events
            if 'event_name' in first_row and first_row['event_name']:
                entities['events'].append(str(first_row['event_name']))
            
            # Look for weight classes
            if 'weight_class' in first_row and first_row['weight_class']:
                entities['weight_classes'].append(str(first_row['weight_class']))
        
        # Remove duplicates and empty values
        entities['fighters'] = list(set(filter(None, entities['fighters'])))
        entities['events'] = list(set(filter(None, entities['events'])))
        entities['weight_classes'] = list(set(filter(None, entities['weight_classes'])))
        
        return entities
    
    def add_interaction(self, session_id: str, question: str, response: Dict[str, Any]):
        """Add a new interaction to the conversation history"""
        self._cleanup_expired_sessions()
        
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'session_id': session_id,
                'created_at': datetime.now(),
                'interactions': [],
                'context': {
                    'current_fighters': [],
                    'current_events': [],
                    'current_weight_classes': [],
                    'recent_question_types': [],
                    'topics_discussed': set()
                }
            }
        
        conversation = self.conversations[session_id]
        
        # Extract entities from this interaction
        classification = response.get('classification', {})
        data = response.get('data', [])
        entities = self._extract_context_entities(question, classification, data)
        
        # Create interaction record
        interaction = {
            'timestamp': datetime.now(),
            'question': question,
            'question_type': classification.get('question_type'),
            'entities': entities,
            'success': response.get('success', False),
            'row_count': response.get('row_count', 0),
            'cached': response.get('cached', False)
        }
        
        # Add to interactions list (keep last 10)
        conversation['interactions'].append(interaction)
        if len(conversation['interactions']) > 10:
            conversation['interactions'].pop(0)
        
        # Update context
        context = conversation['context']
        
        # Update current entities (keep last 3 for each type)
        context['current_fighters'].extend(entities['fighters'])
        context['current_fighters'] = list(set(context['current_fighters']))[-3:]
        
        context['current_events'].extend(entities['events'])
        context['current_events'] = list(set(context['current_events']))[-3:]
        
        context['current_weight_classes'].extend(entities['weight_classes'])
        context['current_weight_classes'] = list(set(context['current_weight_classes']))[-3:]
        
        # Track question types (keep last 5)
        if classification.get('question_type'):
            context['recent_question_types'].append(classification['question_type'])
            if len(context['recent_question_types']) > 5:
                context['recent_question_types'].pop(0)
        
        # Track topics (handle both set and list cases)
        topics = context['topics_discussed']
        if isinstance(topics, list):
            # Convert back to set for adding new items
            topics = set(topics)
        
        if entities['fighters']:
            topics.add(f"fighter:{entities['fighters'][0]}")
        if entities['events']:
            topics.add(f"event:{entities['events'][0]}")
        
        # Convert set to list for JSON serialization
        context['topics_discussed'] = list(topics)[-10:]
        
        conversation['last_activity'] = datetime.now()
        
        logger.info(f"Added interaction for session {session_id}: {question[:50]}...")
    
    def get_context(self, session_id: str) -> Optional[Dict]:
        """Get conversation context for a session"""
        self._cleanup_expired_sessions()
        
        if session_id not in self.conversations:
            return None
        
        return self.conversations[session_id]['context']
    
    def get_recent_interactions(self, session_id: str, count: int = 3) -> list[dict]:
        """Get recent interactions for context"""
        if session_id not in self.conversations:
            return []
        
        interactions = self.conversations[session_id]['interactions']
        return interactions[-count:] if len(interactions) > count else interactions
    
    def generate_context_prompt(self, session_id: str, current_question: str) -> str:
        """Generate a context prompt for better AI responses"""
        context = self.get_context(session_id)
        recent_interactions = self.get_recent_interactions(session_id, 2)
        
        if not context and not recent_interactions:
            return ""
        
        context_prompt = "CONVERSATION CONTEXT:\n"
        
        if context:
            if context['current_fighters']:
                context_prompt += f"- Recent fighters discussed: {', '.join(context['current_fighters'])}\n"
            
            if context['current_events']:
                context_prompt += f"- Recent events discussed: {', '.join(context['current_events'])}\n"
            
            if context['current_weight_classes']:
                context_prompt += f"- Recent weight classes: {', '.join(context['current_weight_classes'])}\n"
            
            if context['recent_question_types']:
                context_prompt += f"- Recent question types: {', '.join(context['recent_question_types'][-3:])}\n"
        
        if recent_interactions:
            context_prompt += "- Recent questions:\n"
            for interaction in recent_interactions[-2:]:
                context_prompt += f"  • {interaction['question'][:100]}\n"
        
        context_prompt += f"\nCURRENT QUESTION: {current_question}\n"
        context_prompt += "\nUse this context to provide more relevant and connected responses. Reference previous discussions when appropriate.\n\n"
        
        return context_prompt
    
    def suggest_follow_ups(self, session_id: str, current_classification: Dict) -> list[str]:
        """Generate contextual follow-up suggestions based on conversation history"""
        context = self.get_context(session_id)
        
        if not context:
            return []
        
        suggestions = []
        current_type = current_classification.get('question_type')
        
        # Context-aware suggestions based on current entities
        if context['current_fighters']:
            fighter = context['current_fighters'][-1]
            if current_type == 'record_lookup':
                suggestions.extend([
                    f"{fighter} recent fights",
                    f"Who should {fighter} fight next?"
                ])
            elif current_type == 'fight_history':
                suggestions.extend([
                    f"{fighter} knockout wins", 
                    f"Compare {fighter} vs top contenders"
                ])
        
        if context['current_weight_classes'] and len(context['current_weight_classes']) > 0:
            weight_class = context['current_weight_classes'][-1]
            suggestions.extend([
                f"Best finishers in {weight_class}",
                f"{weight_class} title history"
            ])
        
        # Remove duplicates and limit to 2
        unique_suggestions = list(set(suggestions))
        return unique_suggestions[:2]
    
    def get_stats(self) -> Dict:
        """Get conversation memory statistics"""
        active_sessions = len(self.conversations)
        total_interactions = sum(len(conv['interactions']) for conv in self.conversations.values())
        
        return {
            'active_sessions': active_sessions,
            'total_interactions': total_interactions,
            'max_conversations': self.max_conversations,
            'session_timeout_minutes': self.session_timeout // 60
        }

# Global memory instance
conversation_memory = ConversationMemory(max_conversations=50, session_timeout=1800)  # 30 minutes