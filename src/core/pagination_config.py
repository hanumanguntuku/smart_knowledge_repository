"""
Pagination Configuration and Safety Mechanisms
Handles page size limits with performance monitoring and safety checks
"""
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PaginationLimits:
    """Configuration for pagination limits with safety thresholds"""
    # Standard limits
    search_results_max: int = 200
    browse_documents_max: int = 500
    api_default_limit: int = 100
    
    # Safety thresholds
    performance_warning_threshold: int = 100  # Warn if processing takes >100ms per item
    memory_warning_threshold_mb: int = 50    # Warn if response >50MB
    
    # Timeout settings
    query_timeout_seconds: int = 30
    large_query_timeout_seconds: int = 60
    
    # Progressive loading thresholds
    progressive_loading_threshold: int = 100  # Use progressive loading for >100 items
    batch_size: int = 50                      # Load in batches of 50

class PaginationManager:
    """Manages pagination with performance monitoring and safety checks"""
    
    def __init__(self, limits: PaginationLimits = None):
        self.limits = limits or PaginationLimits()
        self.performance_metrics: Dict[str, List[float]] = {}
    
    def validate_page_size(self, requested_size: int, operation_type: str = "general") -> Tuple[int, List[str]]:
        """
        Validate and adjust page size with warnings
        
        Args:
            requested_size: Requested page size
            operation_type: Type of operation (search, browse, api)
            
        Returns:
            Tuple of (adjusted_size, warnings)
        """
        warnings = []
        
        # Determine max limit based on operation type
        if operation_type == "search":
            max_limit = self.limits.search_results_max
        elif operation_type == "browse":
            max_limit = self.limits.browse_documents_max
        elif operation_type == "api":
            max_limit = self.limits.api_default_limit * 5  # Allow 5x API default
        else:
            max_limit = 100
        
        # Validate against limits
        if requested_size > max_limit:
            warnings.append(f"Requested size {requested_size} exceeds maximum {max_limit}. Using {max_limit}.")
            return max_limit, warnings
        
        # Performance warnings
        if requested_size > self.limits.performance_warning_threshold:
            warnings.append(f"Large page size ({requested_size}) may impact performance. Consider using pagination.")
        
        if requested_size > self.limits.progressive_loading_threshold:
            warnings.append(f"Progressive loading recommended for {requested_size} items.")
        
        return requested_size, warnings
    
    def should_use_progressive_loading(self, size: int) -> bool:
        """Determine if progressive loading should be used"""
        return size > self.limits.progressive_loading_threshold
    
    def get_batch_size(self, total_size: int) -> int:
        """Get optimal batch size for progressive loading"""
        if total_size <= self.limits.batch_size:
            return total_size
        return min(self.limits.batch_size, total_size // 4)  # At most 4 batches
    
    def monitor_performance(self, operation: str, start_time: float, item_count: int, response_size_mb: float = 0):
        """Monitor and log performance metrics"""
        duration = time.time() - start_time
        
        # Track performance metrics
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        
        self.performance_metrics[operation].append(duration)
        
        # Performance warnings
        time_per_item = duration / max(item_count, 1) * 1000  # ms per item
        
        if time_per_item > self.limits.performance_warning_threshold:
            logger.warning(f"Performance warning: {operation} took {time_per_item:.1f}ms per item (threshold: {self.limits.performance_warning_threshold}ms)")
        
        if response_size_mb > self.limits.memory_warning_threshold_mb:
            logger.warning(f"Memory warning: {operation} response size {response_size_mb:.1f}MB (threshold: {self.limits.memory_warning_threshold_mb}MB)")
        
        logger.info(f"Performance: {operation} - {item_count} items in {duration:.2f}s ({time_per_item:.1f}ms/item)")
    
    def get_timeout_for_size(self, size: int) -> int:
        """Get appropriate timeout based on request size"""
        if size > self.limits.progressive_loading_threshold:
            return self.limits.large_query_timeout_seconds
        return self.limits.query_timeout_seconds
    
    def get_performance_summary(self) -> Dict[str, Dict[str, float]]:
        """Get performance summary for all operations"""
        summary = {}
        
        for operation, times in self.performance_metrics.items():
            if times:
                summary[operation] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "total_requests": len(times)
                }
        
        return summary

# Global pagination manager instance
pagination_manager = PaginationManager()
