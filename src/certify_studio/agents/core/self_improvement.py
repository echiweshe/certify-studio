"""
Self-Improvement System for Autonomous Agents

This module implements mechanisms for agents to learn from experience,
improve their strategies, and adapt their behavior over time.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import asyncio
import json
from loguru import logger
from collections import defaultdict, deque

from certify_studio.core.llm import MultimodalLLM


class PerformanceMetric(Enum):
    """Types of performance metrics to track."""
    SUCCESS_RATE = "success_rate"
    COMPLETION_TIME = "completion_time"
    QUALITY_SCORE = "quality_score"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    LEARNING_RATE = "learning_rate"


@dataclass
class PerformanceRecord:
    """Record of agent performance on a task."""
    task_id: str
    task_type: str
    timestamp: datetime
    metrics: Dict[PerformanceMetric, float]
    context: Dict[str, Any]
    strategy_used: str
    outcome: str
    feedback: Optional[Dict[str, Any]] = None


@dataclass
class ImprovementStrategy:
    """Represents a strategy for improving agent performance."""
    id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    applicable_to: List[str]  # Task types this strategy applies to
    expected_improvement: float
    risk_level: float
    tested: bool = False
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of this strategy."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5


@dataclass
class ExperimentResult:
    """Result of an improvement experiment."""
    experiment_id: str
    strategy_id: str
    baseline_performance: Dict[PerformanceMetric, float]
    experimental_performance: Dict[PerformanceMetric, float]
    sample_size: int
    confidence_interval: Tuple[float, float]
    p_value: float
    significant: bool
    recommendation: str


class SelfImprovementSystem:
    """System for continuous self-improvement of agents."""
    
    def __init__(self, llm: Optional[MultimodalLLM] = None):
        self.performance_history: List[PerformanceRecord] = []
        self.strategies: Dict[str, ImprovementStrategy] = {}
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.models: Dict[str, Any] = {}
        self.learning_curves: Dict[str, List[float]] = defaultdict(list)
        self.llm = llm
        
        # Performance tracking
        self.recent_performance = deque(maxlen=100)  # Keep last 100 records
        self.performance_baselines: Dict[str, Dict[PerformanceMetric, float]] = {}
        
        # Initialize basic improvement strategies
        self._initialize_strategies()
        
        logger.info("Initialized SelfImprovementSystem")
    
    def _initialize_strategies(self):
        """Initialize basic improvement strategies."""
        # Parameter tuning strategy
        self.add_strategy(ImprovementStrategy(
            id="param_tuning",
            name="Parameter Tuning",
            description="Adjust algorithm parameters based on performance",
            parameters={"learning_rate": 0.1, "exploration_rate": 0.2},
            applicable_to=["all"],
            expected_improvement=0.1,
            risk_level=0.2
        ))
        
        # Feature engineering strategy
        self.add_strategy(ImprovementStrategy(
            id="feature_engineering",
            name="Feature Engineering",
            description="Create new features from existing data",
            parameters={"method": "polynomial", "degree": 2},
            applicable_to=["prediction", "classification"],
            expected_improvement=0.15,
            risk_level=0.3
        ))
        
        # Ensemble strategy
        self.add_strategy(ImprovementStrategy(
            id="ensemble",
            name="Ensemble Methods",
            description="Combine multiple models for better performance",
            parameters={"n_models": 3, "voting": "soft"},
            applicable_to=["prediction", "decision_making"],
            expected_improvement=0.2,
            risk_level=0.4
        ))
    
    async def analyze_performance(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task performance and identify improvement areas."""
        logger.debug(f"Analyzing performance for task: {task_result.get('task_id')}")
        
        # Create performance record
        record = self._create_performance_record(task_result)
        self.performance_history.append(record)
        self.recent_performance.append(record)
        
        # Extract metrics
        metrics = record.metrics
        
        # Analyze performance trends
        trend_analysis = await self._analyze_trends(record.task_type)
        
        # Identify bottlenecks
        bottlenecks = await self._identify_bottlenecks(record)
        
        # Generate improvement hypotheses
        hypotheses = await self._generate_improvement_hypotheses(
            bottlenecks, trend_analysis, record
        )
        
        # Update learning curves
        self._update_learning_curves(record)
        
        return {
            "metrics": metrics,
            "trend_analysis": trend_analysis,
            "bottlenecks": bottlenecks,
            "improvement_hypotheses": hypotheses,
            "current_performance_level": self._calculate_performance_level(record.task_type)
        }
    
    async def experiment_with_strategies(
        self,
        hypotheses: List[Dict[str, Any]],
        task_type: str
    ) -> Dict[str, Any]:
        """Run controlled experiments to test improvement hypotheses."""
        logger.info(f"Starting experiments for {len(hypotheses)} hypotheses")
        
        experiments = []
        
        for hypothesis in hypotheses[:3]:  # Limit concurrent experiments
            # Select appropriate strategy
            strategy = self._select_strategy_for_hypothesis(hypothesis, task_type)
            
            if not strategy:
                continue
            
            # Design experiment
            experiment = await self._design_experiment(hypothesis, strategy)
            
            # Run A/B test
            result = await self._run_ab_test(experiment, task_type)
            
            # Analyze results
            analysis = await self._analyze_experiment_results(result)
            
            experiments.append({
                "hypothesis": hypothesis,
                "strategy": strategy,
                "experiment": experiment,
                "result": result,
                "analysis": analysis
            })
            
            # Update strategy statistics
            if analysis["significant"] and analysis.get("overall_improvement", 0) > 0:
                strategy.success_count += 1
            else:
                strategy.failure_count += 1
        
        # Select best strategies
        best_strategies = await self._select_best_strategies(experiments)
        
        # Clean up completed experiments
        self._cleanup_experiments()
        
        return {
            "experiments_run": len(experiments),
            "experiments": experiments,
            "best_strategies": best_strategies,
            "recommendations": self._generate_recommendations(best_strategies)
        }
    
    async def adapt_behavior(
        self,
        best_strategies: List[Dict[str, Any]],
        agent_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt agent behavior based on successful strategies."""
        logger.info(f"Adapting behavior with {len(best_strategies)} strategies")
        
        adaptations = {}
        
        for strategy_info in best_strategies:
            strategy = strategy_info["strategy"]
            improvement = strategy_info["improvement"]
            
            # Update parameters
            param_updates = await self._calculate_parameter_updates(
                strategy, improvement, agent_config
            )
            adaptations["parameters"] = param_updates
            
            # Update decision logic
            logic_updates = await self._update_decision_logic(
                strategy, agent_config
            )
            adaptations["decision_logic"] = logic_updates
            
            # Update knowledge base
            knowledge_updates = await self._update_knowledge_base(
                strategy, strategy_info["experiment_results"]
            )
            adaptations["knowledge"] = knowledge_updates
        
        # Retrain predictive models
        model_updates = await self._retrain_models()
        adaptations["models"] = model_updates
        
        # Validate adaptations
        validation_result = await self._validate_adaptations(adaptations)
        
        return {
            "adaptations": adaptations,
            "validation": validation_result,
            "expected_improvement": self._estimate_overall_improvement(best_strategies)
        }
    
    def add_strategy(self, strategy: ImprovementStrategy) -> None:
        """Add a new improvement strategy."""
        self.strategies[strategy.id] = strategy
    
    def get_performance_summary(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        if task_type:
            records = [r for r in self.performance_history if r.task_type == task_type]
        else:
            records = self.performance_history
        
        if not records:
            return {"error": "No performance records found"}
        
        # Calculate summary statistics
        summary = {}
        
        for metric in PerformanceMetric:
            values = [r.metrics.get(metric, 0) for r in records]
            if values:
                summary[metric.value] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "trend": self._calculate_trend(values)
                }
        
        return {
            "task_type": task_type,
            "num_records": len(records),
            "metrics_summary": summary,
            "performance_level": self._calculate_performance_level(task_type)
        }
    
    # Helper methods
    
    def _create_performance_record(self, task_result: Dict[str, Any]) -> PerformanceRecord:
        """Create a performance record from task result."""
        # Extract metrics
        metrics = {}
        
        # Success rate
        if "success" in task_result:
            metrics[PerformanceMetric.SUCCESS_RATE] = 1.0 if task_result["success"] else 0.0
        
        # Completion time
        if "duration" in task_result:
            metrics[PerformanceMetric.COMPLETION_TIME] = task_result["duration"]
        
        # Quality score
        if "quality_score" in task_result:
            metrics[PerformanceMetric.QUALITY_SCORE] = task_result["quality_score"]
        
        # Resource efficiency
        if "resources_used" in task_result:
            metrics[PerformanceMetric.RESOURCE_EFFICIENCY] = 1.0 / (1 + task_result["resources_used"])
        
        # Error rate
        if "errors" in task_result:
            metrics[PerformanceMetric.ERROR_RATE] = len(task_result["errors"]) / max(task_result.get("total_operations", 1), 1)
        
        return PerformanceRecord(
            task_id=task_result.get("task_id", "unknown"),
            task_type=task_result.get("task_type", "general"),
            timestamp=datetime.now(),
            metrics=metrics,
            context=task_result.get("context", {}),
            strategy_used=task_result.get("strategy", "default"),
            outcome=task_result.get("outcome", "completed"),
            feedback=task_result.get("feedback")
        )
    
    async def _analyze_trends(self, task_type: str) -> Dict[str, Any]:
        """Analyze performance trends for a task type."""
        # Get recent records for this task type
        recent_records = [r for r in self.recent_performance if r.task_type == task_type]
        
        if len(recent_records) < 3:
            return {"status": "insufficient_data", "records": len(recent_records)}
        
        trends = {}
        
        for metric in PerformanceMetric:
            values = [r.metrics.get(metric, 0) for r in recent_records]
            if values:
                trend = self._calculate_trend(values)
                trends[metric.value] = {
                    "direction": trend,
                    "magnitude": abs(self._calculate_trend_magnitude(values)),
                    "stable": self._is_stable(values)
                }
        
        # Identify concerning trends
        concerns = []
        if trends.get(PerformanceMetric.SUCCESS_RATE.value, {}).get("direction") == "declining":
            concerns.append("Success rate is declining")
        if trends.get(PerformanceMetric.ERROR_RATE.value, {}).get("direction") == "increasing":
            concerns.append("Error rate is increasing")
        
        return {
            "trends": trends,
            "concerns": concerns,
            "overall_trend": self._calculate_overall_trend(trends)
        }
    
    async def _identify_bottlenecks(self, record: PerformanceRecord) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Check each metric against baseline
        baseline = self._get_baseline(record.task_type)
        
        for metric, value in record.metrics.items():
            baseline_value = baseline.get(metric, 0.5)
            
            # Identify underperforming metrics
            if metric in [PerformanceMetric.SUCCESS_RATE, PerformanceMetric.QUALITY_SCORE]:
                if value < baseline_value * 0.9:  # 10% below baseline
                    bottlenecks.append({
                        "metric": metric.value,
                        "current": value,
                        "baseline": baseline_value,
                        "severity": "high" if value < baseline_value * 0.7 else "medium"
                    })
            elif metric == PerformanceMetric.ERROR_RATE:
                if value > baseline_value * 1.1:  # 10% above baseline
                    bottlenecks.append({
                        "metric": metric.value,
                        "current": value,
                        "baseline": baseline_value,
                        "severity": "high" if value > baseline_value * 1.5 else "medium"
                    })
        
        return bottlenecks
    
    async def _generate_improvement_hypotheses(
        self,
        bottlenecks: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any],
        record: PerformanceRecord
    ) -> List[Dict[str, Any]]:
        """Generate hypotheses for performance improvement."""
        hypotheses = []
        
        # Hypothesis based on bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["metric"] == PerformanceMetric.SUCCESS_RATE.value:
                hypotheses.append({
                    "id": f"improve_success_{record.task_type}",
                    "description": "Improve success rate through better error handling",
                    "target_metric": PerformanceMetric.SUCCESS_RATE,
                    "expected_improvement": 0.15,
                    "confidence": 0.7
                })
            elif bottleneck["metric"] == PerformanceMetric.COMPLETION_TIME.value:
                hypotheses.append({
                    "id": f"optimize_time_{record.task_type}",
                    "description": "Optimize algorithms for faster completion",
                    "target_metric": PerformanceMetric.COMPLETION_TIME,
                    "expected_improvement": 0.2,
                    "confidence": 0.6
                })
        
        # Hypothesis based on trends
        if trend_analysis.get("concerns"):
            for concern in trend_analysis["concerns"]:
                if "error rate" in concern.lower():
                    hypotheses.append({
                        "id": f"reduce_errors_{record.task_type}",
                        "description": "Implement better validation to reduce errors",
                        "target_metric": PerformanceMetric.ERROR_RATE,
                        "expected_improvement": 0.3,
                        "confidence": 0.8
                    })
        
        # Rank hypotheses by expected impact
        hypotheses.sort(key=lambda h: h["expected_improvement"] * h["confidence"], reverse=True)
        
        return hypotheses[:5]  # Return top 5 hypotheses
    
    def _update_learning_curves(self, record: PerformanceRecord) -> None:
        """Update learning curves for the task type."""
        # Calculate composite performance score
        performance_score = self._calculate_composite_score(record.metrics)
        
        # Add to learning curve
        self.learning_curves[record.task_type].append(performance_score)
        
        # Keep only recent history
        if len(self.learning_curves[record.task_type]) > 1000:
            self.learning_curves[record.task_type] = self.learning_curves[record.task_type][-1000:]
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear regression
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "improving"
        else:
            return "declining"
    
    def _calculate_trend_magnitude(self, values: List[float]) -> float:
        """Calculate magnitude of trend."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
    
    def _is_stable(self, values: List[float]) -> bool:
        """Check if values are stable (low variance)."""
        if len(values) < 2:
            return True
        
        cv = np.std(values) / (np.mean(values) + 1e-7)  # Coefficient of variation
        return cv < 0.1  # Less than 10% variation
    
    def _calculate_overall_trend(self, trends: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall trend from individual metric trends."""
        if not trends:
            return "unknown"
        
        # Count trend directions
        directions = [t.get("direction", "stable") for t in trends.values()]
        improving = directions.count("improving")
        declining = directions.count("declining")
        
        if improving > declining:
            return "improving"
        elif declining > improving:
            return "declining"
        else:
            return "stable"
    
    def _get_baseline(self, task_type: str) -> Dict[PerformanceMetric, float]:
        """Get performance baseline for task type."""
        if task_type not in self.performance_baselines:
            # Calculate baseline from historical data
            records = [r for r in self.performance_history if r.task_type == task_type]
            
            if records:
                baseline = {}
                for metric in PerformanceMetric:
                    values = [r.metrics.get(metric, 0.5) for r in records]
                    baseline[metric] = np.median(values) if values else 0.5
                self.performance_baselines[task_type] = baseline
            else:
                # Default baseline
                self.performance_baselines[task_type] = {
                    PerformanceMetric.SUCCESS_RATE: 0.7,
                    PerformanceMetric.COMPLETION_TIME: 60.0,
                    PerformanceMetric.QUALITY_SCORE: 0.7,
                    PerformanceMetric.RESOURCE_EFFICIENCY: 0.5,
                    PerformanceMetric.ERROR_RATE: 0.1
                }
        
        return self.performance_baselines[task_type]
    
    def _calculate_composite_score(self, metrics: Dict[PerformanceMetric, float]) -> float:
        """Calculate composite performance score from metrics."""
        weights = {
            PerformanceMetric.SUCCESS_RATE: 0.3,
            PerformanceMetric.QUALITY_SCORE: 0.3,
            PerformanceMetric.RESOURCE_EFFICIENCY: 0.2,
            PerformanceMetric.ERROR_RATE: -0.2  # Negative weight
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in metrics:
                value = metrics[metric]
                # Normalize error rate
                if metric == PerformanceMetric.ERROR_RATE:
                    value = 1 - value
                score += value * abs(weight)
                total_weight += abs(weight)
        
        return score / total_weight if total_weight > 0 else 0.5
    
    def _calculate_performance_level(self, task_type: str) -> str:
        """Calculate current performance level for a task type."""
        recent_records = [r for r in self.recent_performance if r.task_type == task_type]
        
        if not recent_records:
            return "unknown"
        
        # Calculate average composite score
        scores = [self._calculate_composite_score(r.metrics) for r in recent_records[-10:]]
        avg_score = np.mean(scores)
        
        # Map to performance levels
        if avg_score >= 0.9:
            return "expert"
        elif avg_score >= 0.7:
            return "proficient"
        elif avg_score >= 0.5:
            return "competent"
        elif avg_score >= 0.3:
            return "developing"
        else:
            return "novice"
    
    def _select_strategy_for_hypothesis(
        self,
        hypothesis: Dict[str, Any],
        task_type: str
    ) -> Optional[ImprovementStrategy]:
        """Select appropriate strategy for testing a hypothesis."""
        # Find applicable strategies
        applicable_strategies = [
            s for s in self.strategies.values()
            if task_type in s.applicable_to or "all" in s.applicable_to
        ]
        
        if not applicable_strategies:
            return None
        
        # Select based on expected improvement and risk
        best_strategy = None
        best_score = 0
        
        for strategy in applicable_strategies:
            # Calculate selection score
            score = (strategy.expected_improvement * (1 - strategy.risk_level) * 
                    (0.5 if strategy.tested else 1.0))  # Prefer untested strategies
            
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy
    
    async def _design_experiment(
        self,
        hypothesis: Dict[str, Any],
        strategy: ImprovementStrategy
    ) -> Dict[str, Any]:
        """Design an A/B test experiment."""
        experiment_id = f"exp_{hypothesis['id']}_{datetime.now().timestamp()}"
        
        experiment = {
            "id": experiment_id,
            "hypothesis": hypothesis,
            "strategy": strategy.id,
            "control_group": {
                "size": 50,
                "parameters": "current"
            },
            "treatment_group": {
                "size": 50,
                "parameters": strategy.parameters
            },
            "duration": timedelta(hours=24),
            "metrics_to_track": [hypothesis["target_metric"]],
            "success_criteria": {
                "improvement": hypothesis["expected_improvement"] * 0.5,  # Conservative
                "confidence": 0.95
            }
        }
        
        # Store active experiment
        self.active_experiments[experiment_id] = {
            "experiment": experiment,
            "start_time": datetime.now(),
            "results": {"control": [], "treatment": []}
        }
        
        return experiment
    
    async def _run_ab_test(
        self,
        experiment: Dict[str, Any],
        task_type: str
    ) -> ExperimentResult:
        """Run A/B test (simulated for now)."""
        # In a real system, this would coordinate actual task execution
        # Here we'll simulate based on historical data and expected improvements
        
        experiment_data = self.active_experiments.get(experiment["id"])
        if not experiment_data:
            raise ValueError(f"Experiment {experiment['id']} not found")
        
        # Simulate results based on historical performance
        baseline = self._get_baseline(task_type)
        
        # Control group (baseline performance)
        control_results = self._simulate_task_results(
            baseline, experiment["control_group"]["size"], variation=0.1
        )
        
        # Treatment group (with expected improvement)
        strategy = self.strategies[experiment["strategy"]]
        treatment_baseline = {}
        for metric, value in baseline.items():
            if metric == PerformanceMetric.ERROR_RATE:
                # For error rate, improvement means reduction
                treatment_baseline[metric] = value * (1 - strategy.expected_improvement)
            elif metric == PerformanceMetric.COMPLETION_TIME:
                # For completion time, improvement means reduction
                treatment_baseline[metric] = value * (1 - strategy.expected_improvement * 0.5)
            else:
                # For other metrics, improvement means increase
                treatment_baseline[metric] = value * (1 + strategy.expected_improvement)
        
        treatment_results = self._simulate_task_results(
            treatment_baseline, experiment["treatment_group"]["size"], variation=0.15
        )
        
        # Calculate statistics
        control_metrics = self._aggregate_metrics(control_results)
        treatment_metrics = self._aggregate_metrics(treatment_results)
        
        # Perform statistical test
        p_value = self._calculate_p_value(control_results, treatment_results)
        
        # Calculate confidence interval
        target_metric = experiment["metrics_to_track"][0]
        improvement = (
            treatment_metrics.get(target_metric, 0) - 
            control_metrics.get(target_metric, 0)
        )
        ci = self._calculate_confidence_interval(improvement, len(control_results))
        
        return ExperimentResult(
            experiment_id=experiment["id"],
            strategy_id=experiment["strategy"],
            baseline_performance=control_metrics,
            experimental_performance=treatment_metrics,
            sample_size=experiment["control_group"]["size"] + experiment["treatment_group"]["size"],
            confidence_interval=ci,
            p_value=p_value,
            significant=p_value < 0.05,
            recommendation="adopt" if p_value < 0.05 and improvement > 0 else "reject"
        )
    
    async def _analyze_experiment_results(self, result: ExperimentResult) -> Dict[str, Any]:
        """Analyze experiment results in detail."""
        analysis = {
            "significant": result.significant,
            "recommendation": result.recommendation,
            "improvement": {},
            "insights": []
        }
        
        # Calculate improvement for each metric
        for metric in PerformanceMetric:
            if metric in result.baseline_performance and metric in result.experimental_performance:
                baseline = result.baseline_performance[metric]
                experimental = result.experimental_performance[metric]
                
                if baseline > 0:
                    improvement_pct = ((experimental - baseline) / baseline) * 100
                    analysis["improvement"][metric.value] = improvement_pct
                    
                    if abs(improvement_pct) > 10:
                        analysis["insights"].append(
                            f"{metric.value} changed by {improvement_pct:.1f}%"
                        )
        
        # Overall assessment
        avg_improvement = np.mean(list(analysis["improvement"].values())) if analysis["improvement"] else 0
        analysis["overall_improvement"] = avg_improvement
        
        if result.significant and avg_improvement > 5:
            analysis["insights"].append(
                "Strategy shows statistically significant improvement"
            )
        elif not result.significant:
            analysis["insights"].append(
                "Results are not statistically significant"
            )
        
        return analysis
    
    async def _select_best_strategies(
        self,
        experiments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Select the best performing strategies from experiments."""
        best_strategies = []
        
        for exp in experiments:
            analysis = exp["analysis"]
            
            if analysis["significant"] and analysis["overall_improvement"] > 0:
                best_strategies.append({
                    "strategy": exp["strategy"],
                    "improvement": analysis["overall_improvement"],
                    "confidence": 1 - exp["result"].p_value,
                    "experiment_results": exp["result"]
                })
        
        # Sort by improvement
        best_strategies.sort(key=lambda x: x["improvement"], reverse=True)
        
        return best_strategies[:3]  # Return top 3
    
    def _cleanup_experiments(self) -> None:
        """Clean up completed experiments."""
        current_time = datetime.now()
        
        completed = []
        for exp_id, exp_data in self.active_experiments.items():
            duration = exp_data["experiment"]["duration"]
            if current_time - exp_data["start_time"] > duration:
                completed.append(exp_id)
        
        for exp_id in completed:
            del self.active_experiments[exp_id]
    
    def _generate_recommendations(self, best_strategies: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        for strategy_info in best_strategies:
            strategy = strategy_info["strategy"]
            improvement = strategy_info["improvement"]
            
            recommendations.append(
                f"Implement {strategy.name} for {improvement:.1f}% improvement"
            )
            
            # Add specific parameter recommendations
            if strategy.parameters:
                param_str = ", ".join(f"{k}={v}" for k, v in strategy.parameters.items())
                recommendations.append(f"  Parameters: {param_str}")
        
        if not recommendations:
            recommendations.append("No significant improvements found. Consider exploring new strategies.")
        
        return recommendations
    
    async def _calculate_parameter_updates(
        self,
        strategy: ImprovementStrategy,
        improvement: float,
        current_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate parameter updates based on strategy."""
        updates = {}
        
        # Scale parameters based on improvement
        scale_factor = min(improvement / 10, 0.5)  # Max 50% change
        
        for param, value in strategy.parameters.items():
            if param in current_config:
                current_value = current_config[param]
                
                if isinstance(current_value, (int, float)):
                    # Numerical parameters
                    if "rate" in param:
                        # Learning rates, exploration rates, etc.
                        updates[param] = current_value * (1 + scale_factor)
                    elif "threshold" in param:
                        # Thresholds
                        updates[param] = current_value * (1 - scale_factor * 0.5)
                    else:
                        # General numerical parameters
                        updates[param] = current_value + (value - current_value) * scale_factor
                else:
                    # Non-numerical parameters
                    updates[param] = value
        
        return updates
    
    async def _update_decision_logic(
        self,
        strategy: ImprovementStrategy,
        current_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update decision-making logic based on strategy."""
        logic_updates = {}
        
        if strategy.id == "ensemble":
            logic_updates["use_ensemble"] = True
            logic_updates["ensemble_size"] = strategy.parameters.get("n_models", 3)
            logic_updates["voting_method"] = strategy.parameters.get("voting", "soft")
        
        elif strategy.id == "feature_engineering":
            logic_updates["feature_engineering"] = True
            logic_updates["feature_method"] = strategy.parameters.get("method", "polynomial")
        
        return logic_updates
    
    async def _update_knowledge_base(
        self,
        strategy: ImprovementStrategy,
        experiment_results: Any
    ) -> Dict[str, Any]:
        """Update knowledge base with learnings from strategy."""
        knowledge_updates = {
            "successful_strategies": {
                strategy.id: {
                    "success_rate": strategy.success_rate,
                    "avg_improvement": experiment_results.experimental_performance.get(
                        PerformanceMetric.SUCCESS_RATE, 0
                    ) - experiment_results.baseline_performance.get(
                        PerformanceMetric.SUCCESS_RATE, 0
                    ),
                    "best_contexts": []  # TODO: Analyze contexts where strategy works best
                }
            }
        }
        
        return knowledge_updates
    
    async def _retrain_models(self) -> Dict[str, Any]:
        """Retrain predictive models with recent data."""
        retrained = {}
        
        # Group performance records by task type
        task_records = defaultdict(list)
        for record in self.performance_history[-1000:]:  # Use last 1000 records
            task_records[record.task_type].append(record)
        
        # Retrain model for each task type
        for task_type, records in task_records.items():
            if len(records) >= 50:  # Minimum records for training
                model_key = f"{task_type}_performance"
                
                try:
                    # Prepare training data
                    X, y = self._prepare_training_data(records)
                    
                    if len(X) > 0:
                        # Train model
                        model = RandomForestRegressor(
                            n_estimators=100,
                            max_depth=10,
                            random_state=42
                        )
                        
                        # Split data
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=0.2, random_state=42
                        )
                        
                        # Train
                        model.fit(X_train, y_train)
                        
                        # Evaluate
                        train_score = model.score(X_train, y_train)
                        test_score = model.score(X_test, y_test)
                        
                        # Store model
                        self.models[model_key] = model
                        
                        retrained[task_type] = {
                            "train_score": train_score,
                            "test_score": test_score,
                            "num_samples": len(X)
                        }
                
                except Exception as e:
                    logger.error(f"Failed to retrain model for {task_type}: {e}")
                    retrained[task_type] = {"error": str(e)}
        
        return retrained
    
    async def _validate_adaptations(self, adaptations: Dict[str, Any]) -> Dict[str, Any]:
        """Validate proposed adaptations before applying."""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check parameter ranges
        if "parameters" in adaptations:
            for param, value in adaptations["parameters"].items():
                if "rate" in param and not 0 <= value <= 1:
                    validation["errors"].append(
                        f"Invalid {param}: {value} (must be between 0 and 1)"
                    )
                    validation["valid"] = False
        
        # Check for conflicting updates
        if "decision_logic" in adaptations:
            logic = adaptations["decision_logic"]
            if logic.get("use_ensemble") and logic.get("ensemble_size", 0) < 2:
                validation["warnings"].append(
                    "Ensemble size should be at least 2"
                )
        
        return validation
    
    def _estimate_overall_improvement(self, strategies: List[Dict[str, Any]]) -> float:
        """Estimate overall improvement from applying strategies."""
        if not strategies:
            return 0.0
        
        # Combine improvements (with diminishing returns)
        combined_improvement = 0.0
        remaining_potential = 1.0
        
        for strategy in strategies:
            improvement = strategy["improvement"] / 100  # Convert to fraction
            combined_improvement += improvement * remaining_potential
            remaining_potential *= (1 - improvement * 0.5)  # Diminishing returns
        
        return combined_improvement * 100  # Convert back to percentage
    
    def _simulate_task_results(
        self,
        baseline: Dict[PerformanceMetric, float],
        num_samples: int,
        variation: float = 0.1
    ) -> List[Dict[PerformanceMetric, float]]:
        """Simulate task results for testing."""
        results = []
        
        for _ in range(num_samples):
            result = {}
            for metric, base_value in baseline.items():
                # Add random variation
                noise = np.random.normal(0, base_value * variation)
                value = base_value + noise
                
                # Clamp to valid ranges
                if metric in [PerformanceMetric.SUCCESS_RATE, PerformanceMetric.QUALITY_SCORE,
                             PerformanceMetric.RESOURCE_EFFICIENCY, PerformanceMetric.ERROR_RATE]:
                    value = np.clip(value, 0, 1)
                elif metric == PerformanceMetric.COMPLETION_TIME:
                    value = max(0, value)
                
                result[metric] = value
            
            results.append(result)
        
        return results
    
    def _aggregate_metrics(
        self,
        results: List[Dict[PerformanceMetric, float]]
    ) -> Dict[PerformanceMetric, float]:
        """Aggregate metrics from multiple results."""
        aggregated = {}
        
        for metric in PerformanceMetric:
            values = [r.get(metric, 0) for r in results if metric in r]
            if values:
                aggregated[metric] = np.mean(values)
        
        return aggregated
    
    def _calculate_p_value(
        self,
        control: List[Dict[PerformanceMetric, float]],
        treatment: List[Dict[PerformanceMetric, float]]
    ) -> float:
        """Calculate p-value for difference between groups."""
        # Use composite scores for simplicity
        control_scores = [self._calculate_composite_score(r) for r in control]
        treatment_scores = [self._calculate_composite_score(r) for r in treatment]
        
        # Perform t-test
        try:
            from scipy import stats
            _, p_value = stats.ttest_ind(control_scores, treatment_scores)
            return p_value
        except:
            # Fallback to simple estimation
            return 0.05  # Assume borderline significance
    
    def _calculate_confidence_interval(
        self,
        mean_diff: float,
        sample_size: int
    ) -> Tuple[float, float]:
        """Calculate 95% confidence interval."""
        # Simplified calculation
        std_error = 0.1 / np.sqrt(sample_size)  # Assumed standard deviation
        margin = 1.96 * std_error  # 95% confidence
        
        return (mean_diff - margin, mean_diff + margin)
    
    def _prepare_training_data(
        self,
        records: List[PerformanceRecord]
    ) -> Tuple[List[List[float]], List[List[float]]]:
        """Prepare training data from performance records."""
        X = []
        y = []
        
        for record in records:
            # Features
            features = []
            
            # Task type encoding (simple hash)
            features.append(hash(record.task_type) % 100)
            
            # Strategy encoding
            if record.strategy_used in self.strategies:
                strat = self.strategies[record.strategy_used]
                features.extend([
                    strat.expected_improvement,
                    strat.risk_level,
                    strat.success_rate
                ])
            else:
                features.extend([0.0, 0.0, 0.5])
            
            # Context features (simplified)
            features.append(record.context.get("complexity", 0.5))
            features.append(record.context.get("data_size", 100) / 1000)
            features.append(record.context.get("time_constraint", 60) / 3600)
            
            # Targets (all metrics)
            targets = []
            for metric in PerformanceMetric:
                targets.append(record.metrics.get(metric, 0.5))
            
            X.append(features)
            y.append(targets)
        
        return X, y
