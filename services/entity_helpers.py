"""
Entity helper methods for working with resolved entities while preserving ambiguity

This service provides convenient access to entity information without losing
the ambiguity context that the orchestrator needs for decision making.
"""

from typing import List, Optional, Dict, Any
from models.frame import ResolvedEntity, EntityCandidate


class EntityHelpers:
    """Helper methods for working with resolved entities"""
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.8
    MEDIUM_CONFIDENCE = 0.5
    AMBIGUITY_THRESHOLD = 0.7
    
    @staticmethod
    def get_best_candidate(resolved: ResolvedEntity) -> Optional[EntityCandidate]:
        """Get highest scoring candidate"""
        return resolved.candidates[0] if resolved.candidates else None
    
    @staticmethod
    def get_candidates_above_threshold(
        resolved: ResolvedEntity, 
        threshold: float = MEDIUM_CONFIDENCE
    ) -> List[EntityCandidate]:
        """Get all candidates above score threshold"""
        return [c for c in resolved.candidates if c.score >= threshold]
    
    @staticmethod
    def is_ambiguous(
        resolved: ResolvedEntity, 
        threshold: float = AMBIGUITY_THRESHOLD
    ) -> bool:
        """Check if entity has multiple good candidates"""
        good_candidates = [c for c in resolved.candidates if c.score >= threshold]
        return len(good_candidates) > 1
    
    @staticmethod
    def is_high_confidence(resolved: ResolvedEntity) -> bool:
        """Check if the best candidate has high confidence"""
        best = resolved.candidates[0] if resolved.candidates else None
        return best is not None and best.score >= EntityHelpers.HIGH_CONFIDENCE
    
    @staticmethod
    def get_entity_ids(
        resolved: ResolvedEntity, 
        threshold: float = MEDIUM_CONFIDENCE
    ) -> List[str]:
        """Get IDs of all reasonable candidates for filtering"""
        return [c.id for c in resolved.candidates if c.score >= threshold]
    
    @staticmethod
    def get_best_by_type(
        resolved_entities: List[ResolvedEntity],
        entity_type: str
    ) -> Optional[ResolvedEntity]:
        """Get the best resolved entity of a specific type"""
        for resolved in resolved_entities:
            best = EntityHelpers.get_best_candidate(resolved)
            if best and best.entity_type == entity_type:
                return resolved
        return None
    
    @staticmethod
    def format_ambiguity_context(
        resolved: ResolvedEntity, 
        max_candidates: int = 3
    ) -> str:
        """Format ambiguous entity for orchestrator context"""
        if not EntityHelpers.is_ambiguous(resolved):
            best = EntityHelpers.get_best_candidate(resolved)
            if best:
                return f"{resolved.text} → {best.name} (ID: {best.id}, score: {best.score:.2f})"
            return f"{resolved.text} (unresolved)"
        
        # Format multiple candidates
        lines = [f"{resolved.text} could be:"]
        for candidate in resolved.candidates[:max_candidates]:
            lines.append(f"  - {candidate.name} ({candidate.entity_type}): {candidate.disambiguation}")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_display_name(
        resolved: ResolvedEntity,
        use_original: bool = True
    ) -> str:
        """Get display name, preferring original text unless low confidence"""
        if use_original and EntityHelpers.is_high_confidence(resolved):
            return resolved.text
        
        best = EntityHelpers.get_best_candidate(resolved)
        if best:
            return best.name
        
        return resolved.text
    
    @staticmethod
    def to_filter_values(
        resolved: ResolvedEntity,
        strategy: str = "best"  # "best", "all_good", "all"
    ) -> List[str]:
        """Convert resolved entity to filter values based on strategy"""
        if strategy == "best":
            best = EntityHelpers.get_best_candidate(resolved)
            return [best.id] if best else []
        elif strategy == "all_good":
            return EntityHelpers.get_entity_ids(resolved, EntityHelpers.MEDIUM_CONFIDENCE)
        else:  # "all"
            return [c.id for c in resolved.candidates]