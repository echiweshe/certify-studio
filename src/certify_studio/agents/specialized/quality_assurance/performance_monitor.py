"""
Performance Monitor for Quality Assurance Agent.

This module monitors and optimizes performance metrics:
- Generation speed
- Resource usage (CPU, memory, GPU)
- API costs
- File sizes
- Rendering performance
"""

import asyncio
import time
import psutil
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict

from .models import (
    PerformanceMetrics,
    ValidationIssue,
    SeverityLevel,
    QualityDimension,
    ImprovementSuggestion,
    ImprovementType
)
from ....core.config import settings
from ....core.llm import MultimodalLLM
from ....core.llm.multimodal_llm import MultimodalMessage

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors and analyzes performance metrics for content generation."""
    
    def __init__(self, llm: Optional[MultimodalLLM] = None):
        """Initialize the performance monitor."""
        self.llm = llm or MultimodalLLM()
        self.performance_thresholds = self._load_performance_thresholds()
        self.metrics_history = defaultdict(list)
        self.cost_calculator = CostCalculator()
        self.resource_monitor = ResourceMonitor()
        
    def _load_performance_thresholds(self) -> Dict[str, Any]:
        """Load performance thresholds and targets."""
        return {
            "generation_time": {
                "excellent": 30,  # seconds
                "good": 60,
                "acceptable": 120,
                "poor": 300
            },
            "memory_usage": {
                "excellent": 500,  # MB
                "good": 1000,
                "acceptable": 2000,
                "poor": 4000
            },
            "cpu_usage": {
                "excellent": 50,  # percentage
                "good": 70,
                "acceptable": 85,
                "poor": 95
            },
            "file_sizes": {
                "video": {
                    "excellent": 50,  # MB per minute
                    "good": 100,
                    "acceptable": 200,
                    "poor": 500
                },
                "image": {
                    "excellent": 0.5,  # MB
                    "good": 1,
                    "acceptable": 2,
                    "poor": 5
                },
                "document": {
                    "excellent": 5,  # MB
                    "good": 10,
                    "acceptable": 20,
                    "poor": 50
                }
            },
            "api_costs": {
                "per_generation": {
                    "excellent": 0.50,  # USD
                    "good": 1.00,
                    "acceptable": 2.00,
                    "poor": 5.00
                }
            }
        }
        
    async def monitor_generation_performance(
        self,
        generation_id: str,
        generation_func: callable,
        *args,
        **kwargs
    ) -> Tuple[Any, PerformanceMetrics]:
        """Monitor performance during content generation."""
        logger.info(f"Starting performance monitoring for generation {generation_id}")
        
        metrics = PerformanceMetrics()
        
        # Start monitoring
        start_time = time.time()
        start_resources = await self.resource_monitor.get_current_resources()
        
        # Track API calls
        api_tracker = APICallTracker()
        
        try:
            # Execute generation with monitoring
            result = await self._execute_with_monitoring(
                generation_func,
                args,
                kwargs,
                metrics,
                api_tracker
            )
            
            # Calculate final metrics
            end_time = time.time()
            end_resources = await self.resource_monitor.get_current_resources()
            
            # Time metrics
            metrics.generation_time = end_time - start_time
            
            # Resource metrics
            metrics.memory_usage = end_resources["memory"] - start_resources["memory"]
            metrics.cpu_usage = end_resources["cpu_average"]
            metrics.gpu_usage = end_resources.get("gpu_usage", 0.0)
            
            # API metrics
            metrics.api_calls = api_tracker.total_calls
            metrics.api_costs = await self.cost_calculator.calculate_api_costs(
                api_tracker.get_calls_by_service()
            )
            
            # Analyze output if available
            if hasattr(result, "output_files") or isinstance(result, dict) and "output_files" in result:
                output_files = result.output_files if hasattr(result, "output_files") else result["output_files"]
                metrics.file_size = await self._analyze_file_sizes(output_files)
                
            # Identify optimization opportunities
            metrics.optimization_opportunities = await self._identify_optimizations(metrics)
            
            # Store in history
            self._record_metrics(generation_id, metrics)
            
            logger.info(f"Performance monitoring complete. Time: {metrics.generation_time:.2f}s, Cost: ${metrics.api_costs:.2f}")
            
            return result, metrics
            
        except Exception as e:
            logger.error(f"Error during performance monitoring: {e}")
            metrics.generation_time = time.time() - start_time
            return None, metrics
            
    async def _execute_with_monitoring(
        self,
        func: callable,
        args: tuple,
        kwargs: dict,
        metrics: PerformanceMetrics,
        api_tracker: 'APICallTracker'
    ) -> Any:
        """Execute function with detailed monitoring."""
        # Wrap function to track API calls
        original_funcs = {}
        
        # Monkey patch API call functions (simplified example)
        # In production, use proper instrumentation
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            # Restore original functions
            pass
            
    async def _analyze_file_sizes(self, output_files: Dict[str, Any]) -> Dict[str, int]:
        """Analyze sizes of output files."""
        file_sizes = {}
        
        for format_type, file_info in output_files.items():
            if isinstance(file_info, str):
                # It's a file path
                if os.path.exists(file_info):
                    file_sizes[format_type] = os.path.getsize(file_info)
            elif isinstance(file_info, dict) and "path" in file_info:
                if os.path.exists(file_info["path"]):
                    file_sizes[format_type] = os.path.getsize(file_info["path"])
            elif hasattr(file_info, "size"):
                file_sizes[format_type] = file_info.size
                
        return file_sizes
        
    async def _identify_optimizations(self, metrics: PerformanceMetrics) -> List[Dict[str, Any]]:
        """Identify potential performance optimizations."""
        optimizations = []
        
        # Check generation time
        time_rating = self._rate_metric(
            metrics.generation_time,
            self.performance_thresholds["generation_time"]
        )
        
        if time_rating in ["acceptable", "poor"]:
            optimizations.append({
                "area": "generation_time",
                "current": metrics.generation_time,
                "target": self.performance_thresholds["generation_time"]["good"],
                "suggestions": [
                    "Enable caching for repeated operations",
                    "Use parallel processing where possible",
                    "Optimize LLM prompts to reduce tokens",
                    "Consider using smaller models for simple tasks"
                ],
                "potential_improvement": f"{(1 - self.performance_thresholds['generation_time']['good'] / metrics.generation_time) * 100:.0f}%"
            })
            
        # Check memory usage
        if metrics.memory_usage > self.performance_thresholds["memory_usage"]["good"]:
            optimizations.append({
                "area": "memory_usage",
                "current": metrics.memory_usage,
                "target": self.performance_thresholds["memory_usage"]["good"],
                "suggestions": [
                    "Process content in smaller batches",
                    "Clear unnecessary objects from memory",
                    "Use streaming for large file operations",
                    "Optimize data structures"
                ],
                "potential_improvement": f"{(1 - self.performance_thresholds['memory_usage']['good'] / metrics.memory_usage) * 100:.0f}%"
            })
            
        # Check API costs
        if metrics.api_costs > self.performance_thresholds["api_costs"]["per_generation"]["good"]:
            optimizations.append({
                "area": "api_costs",
                "current": metrics.api_costs,
                "target": self.performance_thresholds["api_costs"]["per_generation"]["good"],
                "suggestions": [
                    "Use caching for repeated API calls",
                    "Batch API requests where possible",
                    "Use smaller/cheaper models for simple tasks",
                    "Implement prompt optimization"
                ],
                "potential_savings": f"${metrics.api_costs - self.performance_thresholds['api_costs']['per_generation']['good']:.2f}"
            })
            
        # Check file sizes
        for format_type, size in metrics.file_size.items():
            if format_type in self.performance_thresholds["file_sizes"]:
                threshold = self.performance_thresholds["file_sizes"][format_type]["good"]
                
                # Adjust threshold for video based on duration
                if format_type == "video" and "duration" in metrics.__dict__:
                    threshold *= (metrics.duration / 60)  # per minute
                    
                if size > threshold * 1024 * 1024:  # Convert MB to bytes
                    optimizations.append({
                        "area": f"{format_type}_size",
                        "current": size,
                        "target": threshold * 1024 * 1024,
                        "suggestions": [
                            f"Optimize {format_type} compression settings",
                            f"Reduce {format_type} resolution if appropriate",
                            f"Use more efficient {format_type} formats",
                            "Remove unnecessary assets"
                        ],
                        "potential_reduction": f"{(1 - threshold * 1024 * 1024 / size) * 100:.0f}%"
                    })
                    
        return optimizations
        
    def _rate_metric(self, value: float, thresholds: Dict[str, float]) -> str:
        """Rate a metric based on thresholds."""
        if value <= thresholds["excellent"]:
            return "excellent"
        elif value <= thresholds["good"]:
            return "good"
        elif value <= thresholds["acceptable"]:
            return "acceptable"
        else:
            return "poor"
            
    def _record_metrics(self, generation_id: str, metrics: PerformanceMetrics):
        """Record metrics in history for trend analysis."""
        self.metrics_history[generation_id].append({
            "timestamp": datetime.now(),
            "metrics": metrics
        })
        
        # Keep only last 100 entries per generation type
        if len(self.metrics_history[generation_id]) > 100:
            self.metrics_history[generation_id] = self.metrics_history[generation_id][-100:]
            
    async def analyze_performance_trends(self, generation_type: str) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if generation_type not in self.metrics_history:
            return {"error": "No historical data available"}
            
        history = self.metrics_history[generation_type]
        if len(history) < 2:
            return {"error": "Insufficient historical data"}
            
        trends = {
            "generation_time": self._calculate_trend([h["metrics"].generation_time for h in history]),
            "memory_usage": self._calculate_trend([h["metrics"].memory_usage for h in history]),
            "api_costs": self._calculate_trend([h["metrics"].api_costs for h in history]),
            "timeline": [h["timestamp"] for h in history]
        }
        
        # Identify concerning trends
        concerns = []
        if trends["generation_time"]["trend"] == "increasing" and trends["generation_time"]["change_rate"] > 0.1:
            concerns.append("Generation time is increasing significantly")
        if trends["api_costs"]["trend"] == "increasing" and trends["api_costs"]["change_rate"] > 0.2:
            concerns.append("API costs are rising rapidly")
            
        return {
            "trends": trends,
            "concerns": concerns,
            "recommendations": self._generate_trend_recommendations(trends)
        }
        
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend from a series of values."""
        if len(values) < 2:
            return {"trend": "insufficient_data"}
            
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return {"trend": "stable", "change_rate": 0}
            
        slope = numerator / denominator
        
        # Determine trend
        change_rate = abs(slope) / y_mean if y_mean != 0 else 0
        
        if change_rate < 0.05:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
            
        return {
            "trend": trend,
            "change_rate": change_rate,
            "average": y_mean,
            "latest": values[-1],
            "slope": slope
        }
        
    def _generate_trend_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []
        
        if trends["generation_time"]["trend"] == "increasing":
            recommendations.append("Investigate causes of increasing generation time")
            recommendations.append("Consider implementing performance optimizations")
            
        if trends["memory_usage"]["trend"] == "increasing":
            recommendations.append("Check for memory leaks")
            recommendations.append("Optimize memory-intensive operations")
            
        if trends["api_costs"]["trend"] == "increasing":
            recommendations.append("Review API usage patterns")
            recommendations.append("Implement more aggressive caching")
            
        return recommendations
        
    async def generate_performance_report(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Generate detailed performance report."""
        report = {
            "summary": {
                "generation_time": f"{metrics.generation_time:.2f}s",
                "memory_usage": f"{metrics.memory_usage:.0f}MB",
                "cpu_usage": f"{metrics.cpu_usage:.0f}%",
                "gpu_usage": f"{metrics.gpu_usage:.0f}%",
                "api_costs": f"${metrics.api_costs:.2f}",
                "total_api_calls": metrics.api_calls
            },
            "ratings": {},
            "optimizations": metrics.optimization_opportunities,
            "recommendations": []
        }
        
        # Rate each metric
        report["ratings"]["generation_time"] = self._rate_metric(
            metrics.generation_time,
            self.performance_thresholds["generation_time"]
        )
        report["ratings"]["memory_usage"] = self._rate_metric(
            metrics.memory_usage,
            self.performance_thresholds["memory_usage"]
        )
        report["ratings"]["cost_efficiency"] = self._rate_metric(
            metrics.api_costs,
            self.performance_thresholds["api_costs"]["per_generation"]
        )
        
        # Generate specific recommendations
        if report["ratings"]["generation_time"] in ["poor", "acceptable"]:
            report["recommendations"].append({
                "priority": "high",
                "area": "speed",
                "suggestion": "Implement parallel processing for independent operations"
            })
            
        if report["ratings"]["cost_efficiency"] == "poor":
            report["recommendations"].append({
                "priority": "high",
                "area": "cost",
                "suggestion": "Review and optimize LLM usage patterns"
            })
            
        return report


class APICallTracker:
    """Tracks API calls during execution."""
    
    def __init__(self):
        self.calls = []
        self.total_calls = 0
        
    def track_call(self, service: str, endpoint: str, tokens: int = 0, cost: float = 0.0):
        """Track an API call."""
        self.calls.append({
            "service": service,
            "endpoint": endpoint,
            "tokens": tokens,
            "cost": cost,
            "timestamp": datetime.now()
        })
        self.total_calls += 1
        
    def get_calls_by_service(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get calls grouped by service."""
        by_service = defaultdict(list)
        for call in self.calls:
            by_service[call["service"]].append(call)
        return dict(by_service)


class CostCalculator:
    """Calculates costs for various services."""
    
    def __init__(self):
        self.pricing = {
            "openai": {
                "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
                "embeddings": 0.0001  # per 1K tokens
            },
            "anthropic": {
                "claude-3-opus": {"input": 0.015, "output": 0.075},
                "claude-3-sonnet": {"input": 0.003, "output": 0.015}
            },
            "stability": {
                "image_generation": 0.002  # per image
            }
        }
        
    async def calculate_api_costs(self, calls_by_service: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate total API costs."""
        total_cost = 0.0
        
        for service, calls in calls_by_service.items():
            if service in self.pricing:
                for call in calls:
                    if "cost" in call and call["cost"] > 0:
                        total_cost += call["cost"]
                    else:
                        # Estimate based on tokens
                        total_cost += self._estimate_call_cost(service, call)
                        
        return total_cost
        
    def _estimate_call_cost(self, service: str, call: Dict[str, Any]) -> float:
        """Estimate cost for a single API call."""
        if service not in self.pricing:
            return 0.0
            
        endpoint = call.get("endpoint", "")
        tokens = call.get("tokens", 0)
        
        # Simplified estimation
        if "gpt" in endpoint:
            model_pricing = self.pricing[service].get("gpt-4", {"input": 0.03, "output": 0.06})
            # Assume 50/50 input/output split
            return (tokens / 1000) * (model_pricing["input"] + model_pricing["output"]) / 2
        elif "embed" in endpoint:
            return (tokens / 1000) * self.pricing[service].get("embeddings", 0.0001)
        elif "image" in endpoint:
            return self.pricing[service].get("image_generation", 0.002)
            
        return 0.0


class ResourceMonitor:
    """Monitors system resources."""
    
    async def get_current_resources(self) -> Dict[str, float]:
        """Get current resource usage."""
        resources = {
            "memory": psutil.Process().memory_info().rss / 1024 / 1024,  # MB
            "cpu_percent": psutil.Process().cpu_percent(interval=0.1),
            "cpu_average": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.Process().memory_percent()
        }
        
        # Try to get GPU usage if available
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                resources["gpu_usage"] = gpus[0].load * 100
                resources["gpu_memory"] = gpus[0].memoryUsed
        except:
            pass
            
        return resources
