"""
ConceptResolver - Memory-based concept resolution using mem0

Resolves natural language concepts to system concepts using memory.
Learns from successful patterns over time with persistent storage.
"""

from typing import Dict, Any, List, Optional
import logging
import os
from mem0 import Memory

logger = logging.getLogger(__name__)


class ConceptResolver:
    """Memory-based concept resolution with mem0 integration"""
    
    def __init__(self):
        # Initialize mem0 with PostgreSQL/pgvector backend 
        try:
            from mem0 import Memory
            
            config = {
                "vector_store": {
                    "provider": "pgvector",
                    "config": {
                        "host": "postgres",  # Docker service name
                        "port": 5432,       # Internal container port
                        "user": "encore", 
                        "password": "secure_password",
                        "dbname": "encoreproai"
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                        "embedding_dims": 1536
                    }
                }
            }
            
            self.memory = Memory.from_config(config)
            logger.info("Initialized mem0 with PostgreSQL/pgvector backend")
        except Exception as e:
            logger.warning(f"Failed to initialize mem0: {e}. Falling back to basic mappings.")
            self.memory = None
        
        # Fallback mappings for when mem0 is not available
        self.basic_mappings = {
            # Financial concepts
            "revenue": "financial_performance",
            "sales": "financial_performance", 
            "income": "financial_performance",
            "money": "financial_performance",
            "earnings": "financial_performance",
            "gross": "financial_performance",
            
            # Audience concepts
            "attendance": "audience_metrics",
            "tickets": "audience_metrics",
            "people": "audience_metrics",
            "customers": "audience_metrics",
            "patrons": "audience_metrics",
            "attendees": "audience_metrics",
            "audience": "audience_metrics",
            
            # Performance concepts
            "performance": "general_analysis",
            "performing": "general_analysis",
            "how did": "general_analysis",
            "doing": "general_analysis",
            
            # Analysis concepts
            "trends": "trend_analysis",
            "trending": "trend_analysis",
            "comparison": "comparative_analysis",
            "compare": "comparative_analysis",
            "vs": "comparative_analysis",
            "versus": "comparative_analysis",
            
            # Emotional concepts
            "overwhelmed": "emotional_support",
            "stressed": "emotional_support",
            "confused": "emotional_support",
            "worried": "emotional_support",
            "help": "emotional_support",
            "frustrated": "emotional_support"
        }
        
        # Seed memory with initial mappings if available
        if self.memory:
            self._seed_initial_mappings()
    
    def resolve(self, concept_text: str, user_id: str = "system") -> Dict[str, Any]:
        """
        Resolve a concept to memory context using mem0 or fallback mappings
        
        1. Query mem0 for related memories
        2. If no memory found, use basic mappings
        3. Return enriched memory context
        """
        
        concept_lower = concept_text.lower().strip()
        
        # Try mem0 first if available
        if self.memory:
            try:
                # Search for related memories - try multiple search strategies
                search_queries = [
                    f"concept {concept_text}",
                    f"{concept_text} maps to",
                    f"{concept_text} mapping",
                    concept_text
                ]
                
                related_memories = []
                for search_query in search_queries:
                    memories = self.memory.search(
                        query=search_query,
                        user_id=user_id,
                        limit=3
                    )
                    if memories:
                        related_memories.extend(memories)
                        break
                
                if related_memories:
                    # Debug: log what we got back
                    logger.info(f"Found {len(related_memories)} memories for '{concept_text}'")
                    logger.info(f"First memory type: {type(related_memories[0])}")
                    logger.info(f"First memory content: {related_memories[0]}")
                    
                    # Extract the best matching concept
                    best_memory = related_memories[0]
                    mapped_concept = self._extract_concept_from_memory(best_memory)
                    
                    # Get related queries from memory
                    related_queries = self._get_related_queries(concept_text, user_id)
                    
                    logger.info(f"Found memory for concept '{concept_text}' -> '{mapped_concept}'")
                    
                    return {
                        "concept": mapped_concept,
                        "original_text": concept_text,
                        "related_queries": related_queries,
                        "usage_count": len(related_memories),
                        "relevance_score": best_memory.get('score', 0.8),
                        "confidence": 0.9,
                        "source": "memory"
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to query mem0 for concept '{concept_text}': {e}")
                logger.debug(f"Exception type: {type(e)}, Details: {str(e)}")
        
        # Fallback to basic mappings
        mapped_concept = self.basic_mappings.get(concept_lower, "general")
        
        logger.debug(f"Using fallback mapping: '{concept_text}' -> '{mapped_concept}'")
        
        return {
            "concept": mapped_concept,
            "original_text": concept_text,
            "related_queries": [],
            "usage_count": 1,
            "relevance_score": 0.8 if mapped_concept != "general" else 0.5,
            "confidence": 0.7 if mapped_concept != "general" else 0.3,
            "source": "fallback"
        }
    
    def learn_from_success(self, concept_text: str, successful_mapping: str, user_id: str = "system"):
        """
        Learn from successful concept mappings by storing in mem0
        """
        if not self.memory:
            logger.info(f"LEARNING (fallback): '{concept_text}' successfully mapped to '{successful_mapping}'")
            return
            
        try:
            # Store successful mapping in memory
            memory_text = f"The concept '{concept_text}' successfully maps to '{successful_mapping}' for analysis purposes."
            
            self.memory.add(
                messages=[{"role": "user", "content": memory_text}],
                user_id=user_id,
                metadata={
                    "type": "concept_mapping",
                    "concept": concept_text,
                    "mapping": successful_mapping,
                    "success": True
                }
            )
            
            logger.info(f"STORED: '{concept_text}' -> '{successful_mapping}' in memory")
            
        except Exception as e:
            logger.error(f"Failed to store successful mapping in memory: {e}")
    
    def learn_from_correction(self, concept_text: str, corrected_mapping: str, user_id: str):
        """
        Learn from user corrections by storing in mem0
        """
        if not self.memory:
            logger.info(f"USER CORRECTION (fallback): '{concept_text}' should be '{corrected_mapping}'")
            return
            
        try:
            # Store user correction in memory
            memory_text = f"User corrected: the concept '{concept_text}' should map to '{corrected_mapping}', not the previous mapping."
            
            self.memory.add(
                messages=[{"role": "user", "content": memory_text}],
                user_id=user_id,
                metadata={
                    "type": "user_correction",
                    "concept": concept_text,
                    "corrected_mapping": corrected_mapping,
                    "correction": True
                }
            )
            
            logger.info(f"USER CORRECTION STORED: '{concept_text}' -> '{corrected_mapping}' for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store user correction in memory: {e}")
    
    def _seed_initial_mappings(self):
        """
        Seed mem0 with initial concept mappings if memory is empty
        """
        try:
            # Check if we already have memories
            existing_memories = self.memory.search(
                query="concept mapping",
                user_id="system",
                limit=1
            )
            
            if existing_memories:
                logger.info("Memory already seeded with concept mappings")
                return
                
            # Seed with core mappings
            core_mappings = [
                ("revenue", "financial_performance"),
                ("sales", "financial_performance"),
                ("attendance", "audience_metrics"),
                ("tickets", "audience_metrics"),
                ("overwhelmed", "emotional_support"),
                ("worried", "emotional_support")
            ]
            
            for concept, mapping in core_mappings:
                memory_text = f"The concept '{concept}' maps to '{mapping}' for analysis purposes."
                
                self.memory.add(
                    messages=[{"role": "system", "content": memory_text}],
                    user_id="system",
                    metadata={
                        "type": "initial_mapping",
                        "concept": concept,
                        "mapping": mapping
                    }
                )
                
            logger.info(f"Seeded memory with {len(core_mappings)} initial concept mappings")
            
        except Exception as e:
            logger.warning(f"Failed to seed initial mappings: {e}")
    
    def _extract_concept_from_memory(self, memory: Dict[str, Any]) -> str:
        """
        Extract the concept mapping from a memory result
        """
        # mem0 stores data in memory['payload'] or memory['metadata']
        payload = memory.get('payload', {})
        
        # Try to get mapping from different possible fields
        if 'mapping' in payload:
            return payload['mapping']
        elif 'corrected_mapping' in payload:
            return payload['corrected_mapping']
        elif 'metadata' in memory and 'mapping' in memory['metadata']:
            return memory['metadata']['mapping']
            
        # Fall back to parsing the memory text
        memory_text = memory.get('memory', '') or memory.get('data', '') or payload.get('data', '')
        
        # Simple parsing - look for "maps to 'concept'"
        import re
        match = re.search(r"maps to ['\"]([^'\"]+)['\"]?", memory_text)
        if match:
            return match.group(1)
            
        # If all else fails, return general
        return "general_analysis"
    
    def _get_related_queries(self, concept_text: str, user_id: str) -> List[str]:
        """
        Get related queries that used this concept
        """
        try:
            related_memories = self.memory.search(
                query=f"queries using {concept_text}",
                user_id=user_id,
                limit=3
            )
            
            related_queries = []
            for memory in related_memories:
                if 'metadata' in memory and 'query' in memory['metadata']:
                    related_queries.append(memory['metadata']['query'])
                    
            return related_queries
            
        except Exception as e:
            logger.warning(f"Failed to get related queries for '{concept_text}': {e}")
            return []