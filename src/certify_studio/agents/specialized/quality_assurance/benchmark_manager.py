"""
Benchmark Manager for Quality Assurance Agent.

This module manages quality benchmarks and comparisons:
- Industry standards
- Best practices
- Competitive analysis
- Performance targets
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import logging
from collections import defaultdict

from .models import (
    QualityBenchmark,
    BenchmarkType,
    QualityDimension,
    QualityScore,
    ValidationIssue,
    SeverityLevel
)
from ....core.llm import LLMClient
from ....core.config import Config

logger = logging.getLogger(__name__)


class BenchmarkManager:
    """Manages quality benchmarks and comparisons."""
    
    def __init__(self, config: Config):
        """Initialize the benchmark manager."""
        self.config = config
        self.llm_client = LLMClient(config)
        self.benchmarks = self._load_default_benchmarks()
        self.custom_benchmarks = {}
        self.benchmark_results_cache = {}
        
    def _load_default_benchmarks(self) -> Dict[str, QualityBenchmark]:
        """Load default industry benchmarks."""
        benchmarks = {}
        
        # Technical accuracy benchmarks
        benchmarks["tech_accuracy_standard"] = QualityBenchmark(
            name="Technical Accuracy Standard",
            type=BenchmarkType.INDUSTRY_STANDARD,
            dimension=QualityDimension.TECHNICAL_ACCURACY,
            target_score=0.95,
            description="Industry standard for technical accuracy in educational content",
            source="IEEE Learning Technology Standards Committee",
            criteria={
                "code_correctness": 0.98,
                "command_accuracy": 0.95,
                "fact_verification": 0.95,
                "up_to_date_info": 0.90
            },
            examples=[
                "All code examples must compile/run without errors",
                "Commands must work in specified environments",
                "Technical facts must be verifiable from authoritative sources"
            ]
        )
        
        # Pedagogical effectiveness benchmarks
        benchmarks["pedagogy_standard"] = QualityBenchmark(
            name="Pedagogical Effectiveness Standard",
            type=BenchmarkType.BEST_PRACTICE,
            dimension=QualityDimension.PEDAGOGICAL_EFFECTIVENESS,
            target_score=0.85,
            description="Best practices for effective learning design",
            source="Association for Educational Communications and Technology",
            criteria={
                "clear_objectives": 0.90,
                "appropriate_difficulty": 0.85,
                "engagement_level": 0.80,
                "retention_design": 0.85
            },
            examples=[
                "Learning objectives clearly stated at beginning",
                "Content difficulty matches target audience",
                "Interactive elements every 5-10 minutes",
                "Spaced repetition for key concepts"
            ]
        )
        
        # Accessibility benchmarks
        benchmarks["wcag_aa"] = QualityBenchmark(
            name="WCAG 2.1 Level AA",
            type=BenchmarkType.ACCESSIBILITY_STANDARD,
            dimension=QualityDimension.ACCESSIBILITY_COMPLIANCE,
            target_score=1.0,  # 100% compliance required
            description="Web Content Accessibility Guidelines 2.1 Level AA compliance",
            source="W3C Web Accessibility Initiative",
            criteria={
                "perceivable": 1.0,
                "operable": 1.0,
                "understandable": 1.0,
                "robust": 1.0
            },
            examples=[
                "All images have descriptive alt text",
                "Color contrast ratio of at least 4.5:1",
                "All content keyboard navigable",
                "Clear and consistent navigation"
            ]
        )
        
        # Performance benchmarks
        benchmarks["performance_target"] = QualityBenchmark(
            name="Content Generation Performance",
            type=BenchmarkType.PERFORMANCE_TARGET,
            dimension=QualityDimension.PERFORMANCE_EFFICIENCY,
            target_score=0.90,
            description="Performance targets for content generation",
            source="Internal performance standards",
            criteria={
                "generation_speed": 0.85,  # Within time targets
                "resource_efficiency": 0.90,  # CPU/Memory usage
                "cost_efficiency": 0.85,  # API costs
                "output_optimization": 0.95  # File sizes
            },
            examples=[
                "Generate standard lesson in under 2 minutes",
                "Memory usage under 2GB",
                "API costs under $1 per lesson",
                "Video files optimized for web delivery"
            ]
        )
        
        # User satisfaction benchmarks
        benchmarks["user_satisfaction"] = QualityBenchmark(
            name="User Satisfaction Target",
            type=BenchmarkType.USER_SATISFACTION,
            dimension=QualityDimension.USER_EXPERIENCE,
            target_score=0.85,
            description="Target user satisfaction ratings",
            source="Industry user research standards",
            criteria={
                "overall_satisfaction": 0.85,
                "ease_of_use": 0.90,
                "learning_effectiveness": 0.85,
                "recommendation_likelihood": 0.80
            },
            examples=[
                "85% user satisfaction rating",
                "90% find content easy to follow",
                "85% report effective learning",
                "Net Promoter Score > 40"
            ]
        )
        
        # Visual quality benchmarks
        benchmarks["visual_quality"] = QualityBenchmark(
            name="Visual Design Standards",
            type=BenchmarkType.BEST_PRACTICE,
            dimension=QualityDimension.VISUAL_QUALITY,
            target_score=0.90,
            description="Standards for visual quality and design",
            source="Design industry best practices",
            criteria={
                "clarity": 0.95,
                "consistency": 0.90,
                "aesthetics": 0.85,
                "brand_alignment": 0.95
            },
            examples=[
                "HD quality for all videos (1080p minimum)",
                "Consistent color scheme throughout",
                "Professional typography and spacing",
                "Smooth animations at 60fps"
            ]
        )
        
        return benchmarks
        
    async def compare_against_benchmarks(
        self,
        quality_scores: Dict[QualityDimension, QualityScore],
        selected_benchmarks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare quality scores against benchmarks."""
        logger.info("Comparing content against quality benchmarks")
        
        # Select benchmarks to use
        if selected_benchmarks:
            benchmarks_to_use = {
                k: v for k, v in self.benchmarks.items()
                if k in selected_benchmarks
            }
        else:
            # Use all relevant benchmarks
            benchmarks_to_use = self.benchmarks
            
        comparison_results = {}
        
        for benchmark_id, benchmark in benchmarks_to_use.items():
            # Find matching quality score
            if benchmark.dimension in quality_scores:
                score = quality_scores[benchmark.dimension]
                
                # Compare against benchmark
                comparison = await self._compare_single_benchmark(
                    score,
                    benchmark
                )
                
                comparison_results[benchmark_id] = comparison
            else:
                comparison_results[benchmark_id] = {
                    "status": "not_evaluated",
                    "reason": f"No score available for {benchmark.dimension.value}"
                }
                
        # Calculate overall benchmark performance
        overall_performance = self._calculate_overall_performance(comparison_results)
        
        return {
            "comparisons": comparison_results,
            "overall": overall_performance,
            "recommendations": await self._generate_benchmark_recommendations(comparison_results)
        }
        
    async def _compare_single_benchmark(
        self,
        score: QualityScore,
        benchmark: QualityBenchmark
    ) -> Dict[str, Any]:
        """Compare a quality score against a single benchmark."""
        comparison = {
            "benchmark_name": benchmark.name,
            "dimension": benchmark.dimension.value,
            "actual_score": score.score,
            "target_score": benchmark.target_score,
            "gap": score.score - benchmark.target_score,
            "status": "pass" if score.score >= benchmark.target_score else "fail",
            "criteria_comparison": {}
        }
        
        # Compare individual criteria if available
        if benchmark.criteria and score.sub_scores:
            for criterion, target in benchmark.criteria.items():
                actual = score.sub_scores.get(criterion, 0.0)
                comparison["criteria_comparison"][criterion] = {
                    "actual": actual,
                    "target": target,
                    "gap": actual - target,
                    "status": "pass" if actual >= target else "fail"
                }
                
        # Add specific feedback
        if comparison["status"] == "fail":
            comparison["improvement_areas"] = self._identify_improvement_areas(
                score,
                benchmark
            )
            
        return comparison
        
    def _identify_improvement_areas(
        self,
        score: QualityScore,
        benchmark: QualityBenchmark
    ) -> List[str]:
        """Identify specific areas needing improvement."""
        areas = []
        
        # Check overall gap
        gap = benchmark.target_score - score.score
        if gap > 0.2:
            areas.append(f"Significant gap ({gap:.1%}) from {benchmark.name}")
            
        # Check criteria gaps
        if benchmark.criteria and score.sub_scores:
            for criterion, target in benchmark.criteria.items():
                actual = score.sub_scores.get(criterion, 0.0)
                if actual < target:
                    areas.append(f"{criterion.replace('_', ' ').title()}: {actual:.1%} (target: {target:.1%})")
                    
        # Add examples as guidance
        if areas and benchmark.examples:
            areas.append(f"Consider: {benchmark.examples[0]}")
            
        return areas
        
    def _calculate_overall_performance(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall benchmark performance."""
        total_benchmarks = len(comparison_results)
        passed_benchmarks = sum(1 for r in comparison_results.values() if r.get("status") == "pass")
        
        # Calculate weighted score based on dimension importance
        dimension_weights = {
            QualityDimension.TECHNICAL_ACCURACY: 0.25,
            QualityDimension.PEDAGOGICAL_EFFECTIVENESS: 0.20,
            QualityDimension.ACCESSIBILITY_COMPLIANCE: 0.15,
            QualityDimension.USER_EXPERIENCE: 0.15,
            QualityDimension.PERFORMANCE_EFFICIENCY: 0.10,
            QualityDimension.VISUAL_QUALITY: 0.10,
            QualityDimension.CERTIFICATION_ALIGNMENT: 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for result in comparison_results.values():
            if "actual_score" in result and "dimension" in result:
                dimension = QualityDimension(result["dimension"])
                weight = dimension_weights.get(dimension, 0.1)
                weighted_score += result["actual_score"] * weight
                total_weight += weight
                
        if total_weight > 0:
            normalized_score = weighted_score / total_weight
        else:
            normalized_score = 0.0
            
        return {
            "passed": passed_benchmarks,
            "total": total_benchmarks,
            "pass_rate": passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0,
            "weighted_score": normalized_score,
            "status": self._get_overall_status(normalized_score, passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0)
        }
        
    def _get_overall_status(self, weighted_score: float, pass_rate: float) -> str:
        """Determine overall benchmark status."""
        if pass_rate >= 0.9 and weighted_score >= 0.85:
            return "excellent"
        elif pass_rate >= 0.7 and weighted_score >= 0.75:
            return "good"
        elif pass_rate >= 0.5 and weighted_score >= 0.65:
            return "acceptable"
        else:
            return "needs_improvement"
            
    async def _generate_benchmark_recommendations(
        self,
        comparison_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on benchmark comparisons."""
        recommendations = []
        
        # Prioritize failed benchmarks
        failed_benchmarks = [
            (bid, result) for bid, result in comparison_results.items()
            if result.get("status") == "fail"
        ]
        
        # Sort by gap size
        failed_benchmarks.sort(key=lambda x: x[1].get("gap", 0))
        
        for benchmark_id, result in failed_benchmarks:
            benchmark = self.benchmarks.get(benchmark_id)
            if not benchmark:
                continue
                
            recommendation = {
                "priority": "high" if result["gap"] < -0.2 else "medium",
                "benchmark": benchmark.name,
                "dimension": benchmark.dimension.value,
                "current_score": result["actual_score"],
                "target_score": result["target_score"],
                "gap": abs(result["gap"]),
                "actions": []
            }
            
            # Add specific actions based on dimension
            if benchmark.dimension == QualityDimension.TECHNICAL_ACCURACY:
                recommendation["actions"] = [
                    "Implement automated code validation",
                    "Add technical review by subject matter expert",
                    "Cross-reference all facts with official documentation"
                ]
            elif benchmark.dimension == QualityDimension.ACCESSIBILITY_COMPLIANCE:
                recommendation["actions"] = [
                    "Run automated accessibility checker",
                    "Fix all WCAG violations",
                    "Test with screen readers"
                ]
            elif benchmark.dimension == QualityDimension.PEDAGOGICAL_EFFECTIVENESS:
                recommendation["actions"] = [
                    "Review content flow and progression",
                    "Add more interactive elements",
                    "Include practice exercises"
                ]
                
            # Add improvement areas
            if "improvement_areas" in result:
                recommendation["specific_improvements"] = result["improvement_areas"]
                
            recommendations.append(recommendation)
            
        return recommendations[:5]  # Top 5 recommendations
        
    async def add_custom_benchmark(
        self,
        benchmark_id: str,
        benchmark: QualityBenchmark
    ) -> bool:
        """Add a custom benchmark."""
        try:
            self.custom_benchmarks[benchmark_id] = benchmark
            logger.info(f"Added custom benchmark: {benchmark.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom benchmark: {e}")
            return False
            
    async def update_benchmark_from_best_content(
        self,
        dimension: QualityDimension,
        top_content_scores: List[QualityScore]
    ) -> QualityBenchmark:
        """Update benchmark based on best performing content."""
        if not top_content_scores:
            raise ValueError("No content scores provided")
            
        # Calculate statistics from top content
        scores = [s.score for s in top_content_scores]
        avg_score = sum(scores) / len(scores)
        
        # Aggregate sub-scores
        aggregated_criteria = defaultdict(list)
        for score in top_content_scores:
            for criterion, value in score.sub_scores.items():
                aggregated_criteria[criterion].append(value)
                
        # Calculate average for each criterion
        criteria_benchmarks = {}
        for criterion, values in aggregated_criteria.items():
            criteria_benchmarks[criterion] = sum(values) / len(values)
            
        # Create new benchmark
        new_benchmark = QualityBenchmark(
            name=f"Best Practice - {dimension.value}",
            type=BenchmarkType.BEST_PRACTICE,
            dimension=dimension,
            target_score=avg_score * 0.95,  # Set target slightly below best average
            description=f"Benchmark derived from top performing content in {dimension.value}",
            source="Internal content analysis",
            criteria=criteria_benchmarks,
            examples=self._extract_best_practices(top_content_scores)
        )
        
        # Store as custom benchmark
        benchmark_id = f"best_practice_{dimension.value}"
        await self.add_custom_benchmark(benchmark_id, new_benchmark)
        
        return new_benchmark
        
    def _extract_best_practices(self, top_scores: List[QualityScore]) -> List[str]:
        """Extract best practices from top performing content."""
        practices = []
        
        # Look for common evidence in high-scoring content
        all_evidence = []
        for score in top_scores:
            all_evidence.extend(score.evidence)
            
        # Find most common practices (simplified)
        if all_evidence:
            # Take first few unique practices
            seen = set()
            for evidence in all_evidence:
                if evidence not in seen and len(practices) < 5:
                    practices.append(evidence)
                    seen.add(evidence)
                    
        return practices
        
    async def generate_competitive_analysis(
        self,
        our_scores: Dict[QualityDimension, QualityScore],
        competitor_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate competitive analysis against other platforms."""
        analysis = {
            "our_position": {},
            "competitors": {},
            "strengths": [],
            "weaknesses": [],
            "opportunities": []
        }
        
        # Calculate our average score
        our_avg = sum(s.score for s in our_scores.values()) / len(our_scores) if our_scores else 0
        
        # Analyze each competitor
        for competitor in competitor_data:
            comp_name = competitor["name"]
            comp_scores = competitor["scores"]
            
            comp_avg = sum(comp_scores.values()) / len(comp_scores) if comp_scores else 0
            
            analysis["competitors"][comp_name] = {
                "average_score": comp_avg,
                "comparison": "ahead" if our_avg > comp_avg else "behind",
                "gap": our_avg - comp_avg
            }
            
            # Dimension-by-dimension comparison
            for dimension in QualityDimension:
                our_score = our_scores.get(dimension, QualityScore(dimension=dimension, score=0)).score
                their_score = comp_scores.get(dimension.value, 0)
                
                if our_score > their_score + 0.1:
                    if dimension.value not in [s["dimension"] for s in analysis["strengths"]]:
                        analysis["strengths"].append({
                            "dimension": dimension.value,
                            "advantage": our_score - their_score,
                            "competitor": comp_name
                        })
                elif their_score > our_score + 0.1:
                    if dimension.value not in [w["dimension"] for w in analysis["weaknesses"]]:
                        analysis["weaknesses"].append({
                            "dimension": dimension.value,
                            "gap": their_score - our_score,
                            "competitor": comp_name
                        })
                        
        # Identify opportunities
        analysis["opportunities"] = await self._identify_competitive_opportunities(
            analysis["weaknesses"],
            analysis["strengths"]
        )
        
        # Overall position
        ahead_count = sum(1 for c in analysis["competitors"].values() if c["comparison"] == "ahead")
        total_competitors = len(analysis["competitors"])
        
        analysis["our_position"] = {
            "rank": total_competitors - ahead_count + 1,
            "total": total_competitors + 1,
            "average_score": our_avg,
            "market_position": self._determine_market_position(ahead_count, total_competitors)
        }
        
        return analysis
        
    async def _identify_competitive_opportunities(
        self,
        weaknesses: List[Dict[str, Any]],
        strengths: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify opportunities based on competitive analysis."""
        opportunities = []
        
        # Quick wins - small gaps that can be closed easily
        for weakness in weaknesses:
            if weakness["gap"] < 0.15:  # Small gap
                opportunities.append({
                    "type": "quick_win",
                    "dimension": weakness["dimension"],
                    "action": f"Close {weakness['gap']:.1%} gap in {weakness['dimension']}",
                    "impact": "high",
                    "effort": "low"
                })
                
        # Differentiation opportunities - build on strengths
        for strength in strengths[:3]:  # Top 3 strengths
            opportunities.append({
                "type": "differentiation",
                "dimension": strength["dimension"],
                "action": f"Further enhance {strength['dimension']} to increase competitive advantage",
                "impact": "high",
                "effort": "medium"
            })
            
        return opportunities
        
    def _determine_market_position(self, ahead_count: int, total: int) -> str:
        """Determine market position based on competitive standing."""
        if total == 0:
            return "unknown"
            
        position_ratio = ahead_count / total
        
        if position_ratio >= 0.8:
            return "market_leader"
        elif position_ratio >= 0.6:
            return "strong_competitor"
        elif position_ratio >= 0.4:
            return "average_performer"
        elif position_ratio >= 0.2:
            return "catching_up"
        else:
            return "needs_improvement"
            
    async def export_benchmark_report(
        self,
        comparison_results: Dict[str, Any],
        format: str = "json"
    ) -> str:
        """Export benchmark comparison report."""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "comparisons": comparison_results["comparisons"],
            "overall_performance": comparison_results["overall"],
            "recommendations": comparison_results.get("recommendations", []),
            "benchmarks_used": {}
        }
        
        # Add benchmark details
        for benchmark_id in comparison_results["comparisons"]:
            if benchmark_id in self.benchmarks:
                benchmark = self.benchmarks[benchmark_id]
                report_data["benchmarks_used"][benchmark_id] = {
                    "name": benchmark.name,
                    "type": benchmark.type.value,
                    "source": benchmark.source,
                    "target_score": benchmark.target_score
                }
                
        if format == "json":
            return json.dumps(report_data, indent=2)
        elif format == "markdown":
            return self._format_benchmark_report_markdown(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _format_benchmark_report_markdown(self, report_data: Dict[str, Any]) -> str:
        """Format benchmark report as markdown."""
        md = ["# Quality Benchmark Report\n"]
        md.append(f"Generated: {report_data['generated_at']}\n")
        
        # Overall performance
        overall = report_data["overall_performance"]
        md.append("## Overall Performance\n")
        md.append(f"- **Status**: {overall['status']}")
        md.append(f"- **Benchmarks Passed**: {overall['passed']}/{overall['total']}")
        md.append(f"- **Pass Rate**: {overall['pass_rate']:.1%}")
        md.append(f"- **Weighted Score**: {overall['weighted_score']:.1%}\n")
        
        # Individual benchmarks
        md.append("## Benchmark Comparisons\n")
        for benchmark_id, result in report_data["comparisons"].items():
            if result.get("status") != "not_evaluated":
                md.append(f"### {result['benchmark_name']}")
                md.append(f"- **Status**: {result['status']}")
                md.append(f"- **Score**: {result['actual_score']:.1%} (Target: {result['target_score']:.1%})")
                if result['gap'] < 0:
                    md.append(f"- **Gap**: {abs(result['gap']):.1%} below target")
                else:
                    md.append(f"- **Gap**: {result['gap']:.1%} above target")
                md.append("")
                
        # Recommendations
        if report_data["recommendations"]:
            md.append("## Recommendations\n")
            for i, rec in enumerate(report_data["recommendations"], 1):
                md.append(f"### {i}. {rec['benchmark']} ({rec['priority']} priority)")
                md.append(f"- **Gap to close**: {rec['gap']:.1%}")
                md.append("- **Actions**:")
                for action in rec["actions"]:
                    md.append(f"  - {action}")
                md.append("")
                
        return "\n".join(md)
