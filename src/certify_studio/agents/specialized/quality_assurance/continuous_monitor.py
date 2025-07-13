"""
Continuous Monitor for Quality Assurance Agent.

This module provides continuous monitoring capabilities:
- Real-time quality tracking
- Trend analysis
- Anomaly detection
- Automated alerts
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
import statistics

from .models import (
    ContinuousMonitoring,
    QualityMetrics,
    QualityDimension,
    ValidationIssue,
    SeverityLevel,
    QualityScore
)
from ....core.config import Config

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """Provides continuous quality monitoring for content."""
    
    def __init__(self, config: Config):
        """Initialize the continuous monitor."""
        self.config = config
        self.active_monitors = {}
        self.monitoring_tasks = {}
        self.alert_handlers = []
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=100))
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        
    async def start_monitoring(
        self,
        content_id: str,
        monitoring_config: ContinuousMonitoring,
        quality_check_func: Callable
    ) -> bool:
        """Start continuous monitoring for content."""
        logger.info(f"Starting continuous monitoring for content {content_id}")
        
        # Store monitoring configuration
        self.active_monitors[content_id] = monitoring_config
        
        # Create monitoring task
        task = asyncio.create_task(
            self._monitoring_loop(content_id, monitoring_config, quality_check_func)
        )
        self.monitoring_tasks[content_id] = task
        
        return True
        
    async def stop_monitoring(self, content_id: str) -> bool:
        """Stop monitoring for content."""
        logger.info(f"Stopping monitoring for content {content_id}")
        
        if content_id in self.monitoring_tasks:
            # Cancel the monitoring task
            self.monitoring_tasks[content_id].cancel()
            
            # Clean up
            del self.monitoring_tasks[content_id]
            del self.active_monitors[content_id]
            
            return True
            
        return False
        
    async def _monitoring_loop(
        self,
        content_id: str,
        config: ContinuousMonitoring,
        quality_check_func: Callable
    ):
        """Main monitoring loop for a content item."""
        while True:
            try:
                # Wait for next check interval
                await asyncio.sleep(config.monitoring_interval)
                
                # Update next check time
                config.last_check = datetime.now()
                config.next_check = config.last_check + timedelta(seconds=config.monitoring_interval)
                
                # Perform quality check
                logger.debug(f"Performing quality check for {content_id}")
                quality_metrics = await quality_check_func(content_id)
                
                # Store metrics
                self._store_metrics(content_id, quality_metrics)
                config.historical_metrics.append(quality_metrics)
                
                # Keep only recent history
                if len(config.historical_metrics) > 100:
                    config.historical_metrics = config.historical_metrics[-100:]
                
                # Check against thresholds
                threshold_violations = self._check_thresholds(quality_metrics, config.quality_thresholds)
                
                # Detect anomalies
                anomalies = await self.anomaly_detector.detect_anomalies(
                    content_id,
                    quality_metrics,
                    config.historical_metrics
                )
                
                if anomalies:
                    config.anomalies_detected.extend(anomalies)
                    
                # Analyze trends
                trends = await self.trend_analyzer.analyze_trends(
                    config.historical_metrics
                )
                config.trend_analysis = trends
                
                # Check alert conditions
                alerts_triggered = await self._check_alert_conditions(
                    content_id,
                    quality_metrics,
                    threshold_violations,
                    anomalies,
                    config.alert_conditions
                )
                
                # Handle alerts
                if alerts_triggered:
                    await self._handle_alerts(content_id, alerts_triggered)
                    
            except asyncio.CancelledError:
                # Monitoring was stopped
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop for {content_id}: {e}")
                await asyncio.sleep(60)  # Wait before retrying
                
    def _store_metrics(self, content_id: str, metrics: QualityMetrics):
        """Store metrics in buffer for analysis."""
        timestamp = datetime.now()
        
        # Store overall score
        self.metrics_buffer[f"{content_id}:overall"].append((timestamp, metrics.overall_score))
        
        # Store dimension scores
        for dimension, score in metrics.dimension_scores.items():
            self.metrics_buffer[f"{content_id}:{dimension.value}"].append((timestamp, score.score))
            
        # Store specific metrics
        if metrics.performance_metrics:
            self.metrics_buffer[f"{content_id}:generation_time"].append(
                (timestamp, metrics.performance_metrics.generation_time)
            )
            self.metrics_buffer[f"{content_id}:api_costs"].append(
                (timestamp, metrics.performance_metrics.api_costs)
            )
            
    def _check_thresholds(
        self,
        metrics: QualityMetrics,
        thresholds: Dict[QualityDimension, float]
    ) -> List[Dict[str, Any]]:
        """Check if metrics violate thresholds."""
        violations = []
        
        for dimension, threshold in thresholds.items():
            if dimension in metrics.dimension_scores:
                actual_score = metrics.dimension_scores[dimension].score
                if actual_score < threshold:
                    violations.append({
                        "dimension": dimension,
                        "threshold": threshold,
                        "actual": actual_score,
                        "gap": threshold - actual_score,
                        "severity": self._calculate_violation_severity(threshold - actual_score)
                    })
                    
        return violations
        
    def _calculate_violation_severity(self, gap: float) -> SeverityLevel:
        """Calculate severity based on threshold gap."""
        if gap > 0.3:
            return SeverityLevel.CRITICAL
        elif gap > 0.2:
            return SeverityLevel.HIGH
        elif gap > 0.1:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
            
    async def _check_alert_conditions(
        self,
        content_id: str,
        metrics: QualityMetrics,
        threshold_violations: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        alert_conditions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met."""
        triggered_alerts = []
        
        for condition in alert_conditions:
            if await self._evaluate_alert_condition(
                condition,
                metrics,
                threshold_violations,
                anomalies
            ):
                triggered_alerts.append({
                    "condition": condition,
                    "content_id": content_id,
                    "timestamp": datetime.now(),
                    "metrics": metrics,
                    "violations": threshold_violations,
                    "anomalies": anomalies
                })
                
        return triggered_alerts
        
    async def _evaluate_alert_condition(
        self,
        condition: Dict[str, Any],
        metrics: QualityMetrics,
        violations: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]]
    ) -> bool:
        """Evaluate a single alert condition."""
        condition_type = condition.get("type", "threshold")
        
        if condition_type == "threshold":
            # Check if any violations match the condition
            dimension = condition.get("dimension")
            severity = condition.get("min_severity", SeverityLevel.MEDIUM)
            
            for violation in violations:
                if (not dimension or violation["dimension"] == dimension) and \
                   violation["severity"].value >= severity.value:
                    return True
                    
        elif condition_type == "anomaly":
            # Check if anomalies detected
            anomaly_type = condition.get("anomaly_type")
            confidence = condition.get("min_confidence", 0.7)
            
            for anomaly in anomalies:
                if (not anomaly_type or anomaly["type"] == anomaly_type) and \
                   anomaly.get("confidence", 0) >= confidence:
                    return True
                    
        elif condition_type == "trend":
            # Check trend conditions
            dimension = condition.get("dimension")
            trend_direction = condition.get("direction", "declining")
            min_duration = condition.get("min_duration", 3)  # checks
            
            # Get recent trends
            buffer_key = f"{dimension.value}" if dimension else "overall"
            recent_values = [v for _, v in self.metrics_buffer.get(buffer_key, [])[-min_duration:]]
            
            if len(recent_values) >= min_duration:
                trend = self._calculate_simple_trend(recent_values)
                if trend == trend_direction:
                    return True
                    
        elif condition_type == "composite":
            # Evaluate composite conditions
            sub_conditions = condition.get("conditions", [])
            operator = condition.get("operator", "AND")
            
            results = []
            for sub_condition in sub_conditions:
                result = await self._evaluate_alert_condition(
                    sub_condition,
                    metrics,
                    violations,
                    anomalies
                )
                results.append(result)
                
            if operator == "AND":
                return all(results)
            elif operator == "OR":
                return any(results)
                
        return False
        
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """Calculate simple trend from recent values."""
        if len(values) < 2:
            return "stable"
            
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
            
        slope = numerator / denominator
        
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"
            
    async def _handle_alerts(self, content_id: str, alerts: List[Dict[str, Any]]):
        """Handle triggered alerts."""
        for alert in alerts:
            logger.warning(f"Alert triggered for {content_id}: {alert['condition'].get('name', 'Unknown')}")
            
            # Call registered alert handlers
            for handler in self.alert_handlers:
                try:
                    await handler(content_id, alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
                    
    def register_alert_handler(self, handler: Callable):
        """Register an alert handler function."""
        self.alert_handlers.append(handler)
        
    async def get_monitoring_status(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Get current monitoring status for content."""
        if content_id not in self.active_monitors:
            return None
            
        config = self.active_monitors[content_id]
        
        # Get recent metrics
        recent_metrics = None
        if config.historical_metrics:
            recent_metrics = config.historical_metrics[-1]
            
        # Get current trends
        trends = config.trend_analysis
        
        # Count recent anomalies
        recent_anomalies = [
            a for a in config.anomalies_detected
            if datetime.now() - a.get("timestamp", datetime.min) < timedelta(hours=24)
        ]
        
        return {
            "content_id": content_id,
            "monitoring_active": True,
            "monitoring_interval": config.monitoring_interval,
            "last_check": config.last_check,
            "next_check": config.next_check,
            "current_quality": recent_metrics.overall_score if recent_metrics else None,
            "trends": trends,
            "recent_anomalies": len(recent_anomalies),
            "total_checks": len(config.historical_metrics)
        }
        
    async def get_monitoring_report(
        self,
        content_id: str,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """Generate monitoring report for content."""
        if content_id not in self.active_monitors:
            return {"error": "Content not being monitored"}
            
        config = self.active_monitors[content_id]
        cutoff_time = datetime.now() - time_window
        
        # Filter metrics by time window
        recent_metrics = [
            m for m in config.historical_metrics
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics in specified time window"}
            
        # Calculate statistics
        overall_scores = [m.overall_score for m in recent_metrics]
        
        report = {
            "content_id": content_id,
            "time_window": {
                "start": cutoff_time,
                "end": datetime.now(),
                "duration_hours": time_window.total_seconds() / 3600
            },
            "metrics_summary": {
                "check_count": len(recent_metrics),
                "average_quality": statistics.mean(overall_scores),
                "min_quality": min(overall_scores),
                "max_quality": max(overall_scores),
                "std_deviation": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0
            },
            "dimension_analysis": {},
            "anomalies": [],
            "alerts_triggered": 0,
            "recommendations": []
        }
        
        # Analyze each dimension
        for dimension in QualityDimension:
            dim_scores = []
            for metric in recent_metrics:
                if dimension in metric.dimension_scores:
                    dim_scores.append(metric.dimension_scores[dimension].score)
                    
            if dim_scores:
                report["dimension_analysis"][dimension.value] = {
                    "average": statistics.mean(dim_scores),
                    "min": min(dim_scores),
                    "max": max(dim_scores),
                    "trend": config.trend_analysis.get(dimension, "unknown")
                }
                
        # Add recent anomalies
        report["anomalies"] = [
            a for a in config.anomalies_detected
            if a.get("timestamp", datetime.min) > cutoff_time
        ]
        
        # Generate recommendations
        report["recommendations"] = await self._generate_monitoring_recommendations(
            report,
            config
        )
        
        return report
        
    async def _generate_monitoring_recommendations(
        self,
        report: Dict[str, Any],
        config: ContinuousMonitoring
    ) -> List[str]:
        """Generate recommendations based on monitoring data."""
        recommendations = []
        
        # Check for declining trends
        for dimension, analysis in report["dimension_analysis"].items():
            if analysis["trend"] == "declining":
                recommendations.append(
                    f"Address declining quality in {dimension} - average dropped to {analysis['average']:.1%}"
                )
                
        # Check for high variability
        if report["metrics_summary"]["std_deviation"] > 0.1:
            recommendations.append(
                "High quality variability detected - investigate causes of inconsistency"
            )
            
        # Check for anomalies
        if len(report["anomalies"]) > 5:
            recommendations.append(
                f"Multiple anomalies detected ({len(report['anomalies'])}) - review generation process"
            )
            
        # Check monitoring frequency
        checks_per_hour = report["metrics_summary"]["check_count"] / (report["time_window"]["duration_hours"])
        if checks_per_hour < 1:
            recommendations.append(
                "Consider increasing monitoring frequency for better quality tracking"
            )
            
        return recommendations


class AnomalyDetector:
    """Detects anomalies in quality metrics."""
    
    def __init__(self):
        self.history_window = 20  # Number of historical points to consider
        self.z_score_threshold = 2.5  # Standard deviations for anomaly
        
    async def detect_anomalies(
        self,
        content_id: str,
        current_metrics: QualityMetrics,
        historical_metrics: List[QualityMetrics]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in current metrics."""
        anomalies = []
        
        if len(historical_metrics) < self.history_window:
            return anomalies  # Not enough history
            
        # Get recent history
        recent_history = historical_metrics[-self.history_window:]
        
        # Check overall score
        overall_anomaly = self._check_metric_anomaly(
            current_metrics.overall_score,
            [m.overall_score for m in recent_history],
            "overall_quality"
        )
        if overall_anomaly:
            anomalies.append(overall_anomaly)
            
        # Check dimension scores
        for dimension, score in current_metrics.dimension_scores.items():
            historical_scores = [
                m.dimension_scores[dimension].score
                for m in recent_history
                if dimension in m.dimension_scores
            ]
            
            if historical_scores:
                dimension_anomaly = self._check_metric_anomaly(
                    score.score,
                    historical_scores,
                    f"{dimension.value}_score"
                )
                if dimension_anomaly:
                    anomalies.append(dimension_anomaly)
                    
        # Check performance metrics
        if current_metrics.performance_metrics:
            perf = current_metrics.performance_metrics
            
            # Check generation time
            historical_times = [
                m.performance_metrics.generation_time
                for m in recent_history
                if m.performance_metrics
            ]
            
            if historical_times:
                time_anomaly = self._check_metric_anomaly(
                    perf.generation_time,
                    historical_times,
                    "generation_time",
                    higher_is_anomaly=True
                )
                if time_anomaly:
                    anomalies.append(time_anomaly)
                    
        return anomalies
        
    def _check_metric_anomaly(
        self,
        current_value: float,
        historical_values: List[float],
        metric_name: str,
        higher_is_anomaly: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Check if current value is anomalous compared to history."""
        if not historical_values:
            return None
            
        # Calculate statistics
        mean = statistics.mean(historical_values)
        stdev = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
        
        if stdev == 0:
            return None  # No variation, can't detect anomaly
            
        # Calculate z-score
        z_score = (current_value - mean) / stdev
        
        # Check if anomalous
        is_anomaly = False
        if higher_is_anomaly and z_score > self.z_score_threshold:
            is_anomaly = True
        elif not higher_is_anomaly and z_score < -self.z_score_threshold:
            is_anomaly = True
            
        if is_anomaly:
            return {
                "type": "statistical_anomaly",
                "metric": metric_name,
                "current_value": current_value,
                "expected_range": {
                    "mean": mean,
                    "std_dev": stdev,
                    "lower_bound": mean - (self.z_score_threshold * stdev),
                    "upper_bound": mean + (self.z_score_threshold * stdev)
                },
                "z_score": z_score,
                "confidence": min(abs(z_score) / 5, 1.0),  # Higher z-score = higher confidence
                "timestamp": datetime.now(),
                "direction": "above" if z_score > 0 else "below"
            }
            
        return None


class TrendAnalyzer:
    """Analyzes trends in quality metrics."""
    
    def __init__(self):
        self.min_points = 5  # Minimum points for trend analysis
        self.smoothing_window = 3  # Moving average window
        
    async def analyze_trends(
        self,
        historical_metrics: List[QualityMetrics]
    ) -> Dict[QualityDimension, str]:
        """Analyze trends for each quality dimension."""
        trends = {}
        
        if len(historical_metrics) < self.min_points:
            return trends
            
        # Analyze overall trend
        overall_scores = [m.overall_score for m in historical_metrics]
        overall_trend = self._calculate_trend(overall_scores)
        
        # Analyze dimension trends
        for dimension in QualityDimension:
            dim_scores = []
            for metric in historical_metrics:
                if dimension in metric.dimension_scores:
                    dim_scores.append(metric.dimension_scores[dimension].score)
                    
            if len(dim_scores) >= self.min_points:
                trends[dimension] = self._calculate_trend(dim_scores)
            else:
                trends[dimension] = "insufficient_data"
                
        return trends
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values with smoothing."""
        if len(values) < self.min_points:
            return "insufficient_data"
            
        # Apply moving average smoothing
        smoothed = self._moving_average(values, self.smoothing_window)
        
        # Fit linear regression to smoothed data
        n = len(smoothed)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(smoothed) / n
        
        numerator = sum((x[i] - x_mean) * (smoothed[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
            
        slope = numerator / denominator
        
        # Calculate R-squared for confidence
        y_pred = [slope * (x[i] - x_mean) + y_mean for i in range(n)]
        ss_tot = sum((smoothed[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((smoothed[i] - y_pred[i]) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine trend based on slope and confidence
        if r_squared < 0.3:  # Low confidence in trend
            return "volatile"
        elif abs(slope) < 0.001:  # Very small slope
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"
            
    def _moving_average(self, values: List[float], window: int) -> List[float]:
        """Calculate moving average."""
        if window > len(values):
            window = len(values)
            
        smoothed = []
        for i in range(len(values)):
            start = max(0, i - window // 2)
            end = min(len(values), i + window // 2 + 1)
            smoothed.append(sum(values[start:end]) / (end - start))
            
        return smoothed
