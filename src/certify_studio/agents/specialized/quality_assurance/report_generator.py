"""
Report Generator for Quality Assurance Agent.

This module generates comprehensive quality reports:
- Validation reports
- Performance reports
- Benchmark comparisons
- Executive summaries
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import base64
import numpy as np

from .models import (
    ValidationReport,
    QualityMetrics,
    QualityDimension,
    QualityScore,
    ValidationIssue,
    SeverityLevel,
    ImprovementSuggestion,
    CertificationAlignment,
    PerformanceMetrics
)
from ....core.config import Settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates various quality assurance reports."""
    
    def __init__(self, config: Settings):
        """Initialize the report generator."""
        self.config = config
        self.report_templates = self._load_report_templates()
        self.visualization_engine = VisualizationEngine()
        
    def _load_report_templates(self) -> Dict[str, str]:
        """Load report templates."""
        return {
            "executive_summary": """
# Executive Summary - Quality Assurance Report

**Content ID**: {content_id}  
**Generated**: {timestamp}  
**Overall Status**: {status}

## Key Metrics
- **Overall Quality Score**: {overall_score:.1%}
- **Technical Accuracy**: {technical_accuracy:.1%}
- **Pedagogical Effectiveness**: {pedagogical_effectiveness:.1%}
- **Accessibility Compliance**: {accessibility_compliance:.1%}

## Summary
{summary_text}

## Recommendations
{recommendations}
""",
            "detailed_validation": """
# Detailed Validation Report

**Report ID**: {report_id}  
**Content ID**: {content_id}  
**Validation Date**: {timestamp}  
**Status**: {status}

## Quality Metrics

### Overall Score: {overall_score:.1%}

### Dimension Breakdown
{dimension_breakdown}

## Issues Found

### Critical Issues ({critical_count})
{critical_issues}

### High Priority Issues ({high_count})
{high_issues}

### Medium Priority Issues ({medium_count})
{medium_issues}

### Low Priority Issues ({low_count})
{low_issues}

## Passed Checks
{passed_checks}

## Improvement Suggestions
{improvement_suggestions}

## Technical Details
- **Validation Duration**: {validation_duration:.2f} seconds
- **Checks Performed**: {total_checks}
- **Auto-fixes Applied**: {auto_fixes_count}
""",
            "performance_report": """
# Performance Report

**Content ID**: {content_id}  
**Generated**: {timestamp}

## Performance Metrics

### Generation Performance
- **Total Time**: {generation_time:.2f} seconds
- **Memory Usage**: {memory_usage:.0f} MB
- **CPU Usage**: {cpu_usage:.0f}%
- **GPU Usage**: {gpu_usage:.0f}%

### Cost Analysis
- **Total API Calls**: {api_calls}
- **Total Cost**: ${api_costs:.2f}
- **Cost per Module**: ${cost_per_module:.2f}

### File Size Analysis
{file_size_analysis}

## Optimization Opportunities
{optimization_opportunities}

## Performance Trends
{performance_trends}
""",
            "certification_alignment": """
# Certification Alignment Report

**Certification**: {certification_id}  
**Content ID**: {content_id}  
**Alignment Score**: {alignment_score:.1%}  
**Exam Readiness**: {exam_readiness:.1%}

## Domain Coverage

{domain_coverage}

## Objective Analysis

### Covered Objectives ({covered_count})
{covered_objectives}

### Partially Covered ({partial_count})
{partial_objectives}

### Missing Objectives ({missing_count})
{missing_objectives}

## Weight Distribution
{weight_distribution}

## Recommendations
{recommendations}
"""
        }
        
    async def generate_validation_report(
        self,
        validation_report: ValidationReport,
        format: str = "markdown",
        include_visualizations: bool = True
    ) -> str:
        """Generate a comprehensive validation report."""
        logger.info(f"Generating validation report for {validation_report.content_id}")
        
        # Prepare data for report
        report_data = await self._prepare_validation_data(validation_report)
        
        # Generate visualizations if requested
        if include_visualizations:
            report_data["visualizations"] = await self.visualization_engine.create_validation_charts(
                validation_report
            )
            
        # Generate report based on format
        if format == "markdown":
            return self._generate_markdown_report(report_data, "detailed_validation")
        elif format == "html":
            return await self._generate_html_report(report_data, "detailed_validation")
        elif format == "json":
            return json.dumps(report_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    async def _prepare_validation_data(self, report: ValidationReport) -> Dict[str, Any]:
        """Prepare validation data for report generation."""
        # Count issues by severity
        issue_counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0,
            SeverityLevel.INFO: 0
        }
        
        for issue in report.issues:
            issue_counts[issue.severity] += 1
            
        # Group issues by severity
        grouped_issues = {
            SeverityLevel.CRITICAL: [],
            SeverityLevel.HIGH: [],
            SeverityLevel.MEDIUM: [],
            SeverityLevel.LOW: []
        }
        
        for issue in report.issues:
            if issue.severity in grouped_issues:
                grouped_issues[issue.severity].append(issue)
                
        # Prepare dimension breakdown
        dimension_scores = {}
        for dim, score in report.quality_metrics.dimension_scores.items():
            dimension_scores[dim.value] = {
                "score": score.score,
                "confidence": score.confidence,
                "status": self._get_score_status(score.score)
            }
            
        return {
            "report_id": str(report.id),
            "content_id": report.content_id,
            "timestamp": report.created_at.isoformat(),
            "status": report.status.value,
            "overall_score": report.quality_metrics.overall_score,
            "technical_accuracy": report.quality_metrics.technical_accuracy.accuracy_score,
            "pedagogical_effectiveness": report.quality_metrics.pedagogical_effectiveness.effectiveness_score,
            "accessibility_compliance": report.quality_metrics.accessibility_report.compliance_score,
            "dimension_scores": dimension_scores,
            "issue_counts": issue_counts,
            "grouped_issues": grouped_issues,
            "passed_checks": report.passed_checks,
            "failed_checks": report.failed_checks,
            "improvement_suggestions": report.improvement_suggestions,
            "validation_duration": report.validation_duration,
            "total_checks": len(report.passed_checks) + len(report.failed_checks),
            "auto_fixes_count": len(report.auto_fixes_applied)
        }
        
    def _get_score_status(self, score: float) -> str:
        """Get status label for a score."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Good"
        elif score >= 0.7:
            return "Acceptable"
        elif score >= 0.6:
            return "Needs Improvement"
        else:
            return "Poor"
            
    def _generate_markdown_report(self, data: Dict[str, Any], template_name: str) -> str:
        """Generate markdown report from data."""
        template = self.report_templates.get(template_name, "")
        
        # Format dimension breakdown
        dimension_lines = []
        for dim, info in data.get("dimension_scores", {}).items():
            dimension_lines.append(
                f"- **{dim.replace('_', ' ').title()}**: {info['score']:.1%} ({info['status']})"
            )
        data["dimension_breakdown"] = "\n".join(dimension_lines)
        
        # Format issues
        for severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]:
            issues = data["grouped_issues"].get(severity, [])
            if issues:
                issue_lines = []
                for issue in issues[:10]:  # Limit to 10 per category
                    issue_lines.append(f"- **{issue.title}**: {issue.description}")
                    if issue.suggested_fix:
                        issue_lines.append(f"  - *Fix*: {issue.suggested_fix}")
                data[f"{severity.value}_issues"] = "\n".join(issue_lines)
            else:
                data[f"{severity.value}_issues"] = "*No issues found*"
                
            data[f"{severity.value}_count"] = data["issue_counts"][severity]
            
        # Format passed checks
        if data["passed_checks"]:
            data["passed_checks"] = "\n".join([f"✓ {check}" for check in data["passed_checks"][:20]])
        else:
            data["passed_checks"] = "*No checks passed*"
            
        # Format improvement suggestions
        if data["improvement_suggestions"]:
            suggestion_lines = []
            for i, suggestion in enumerate(data["improvement_suggestions"][:10], 1):
                suggestion_lines.append(f"{i}. **{suggestion.title}** ({suggestion.priority.value} priority)")
                suggestion_lines.append(f"   - {suggestion.description}")
                if suggestion.implementation_steps:
                    suggestion_lines.append("   - Steps:")
                    for step in suggestion.implementation_steps[:3]:
                        suggestion_lines.append(f"     - {step}")
            data["improvement_suggestions"] = "\n".join(suggestion_lines)
        else:
            data["improvement_suggestions"] = "*No improvement suggestions*"
            
        # Fill template
        return template.format(**data)
        
    async def _generate_html_report(self, data: Dict[str, Any], template_name: str) -> str:
        """Generate HTML report from data."""
        # First generate markdown
        markdown_content = self._generate_markdown_report(data, template_name)
        
        # Convert to HTML (simplified - in production use a proper markdown parser)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Quality Assurance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f0f0f0; }}
        .excellent {{ color: green; }}
        .good {{ color: darkgreen; }}
        .acceptable {{ color: orange; }}
        .needs-improvement {{ color: darkorange; }}
        .poor {{ color: red; }}
        .visualization {{ margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    {self._markdown_to_html(markdown_content)}
    {self._add_visualizations(data.get("visualizations", {}))}
</body>
</html>
"""
        return html
        
    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML converter."""
        html = markdown
        
        # Headers
        html = html.replace("# ", "<h1>").replace("\n\n", "</h1>\n\n", 1)
        html = html.replace("## ", "<h2>").replace("\n\n", "</h2>\n\n")
        html = html.replace("### ", "<h3>").replace("\n\n", "</h3>\n\n")
        
        # Bold
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Italic
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        
        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>\n)+', r'<ul>\g<0></ul>\n', html)
        
        # Paragraphs
        html = re.sub(r'\n\n', '</p>\n\n<p>', html)
        html = f"<p>{html}</p>"
        
        return html
        
    def _add_visualizations(self, visualizations: Dict[str, str]) -> str:
        """Add visualizations to HTML report."""
        if not visualizations:
            return ""
            
        html_parts = ["<div class='visualizations'><h2>Visualizations</h2>"]
        
        for name, data_url in visualizations.items():
            html_parts.append(f"""
            <div class='visualization'>
                <h3>{name.replace('_', ' ').title()}</h3>
                <img src='{data_url}' alt='{name}' style='max-width: 100%; height: auto;'>
            </div>
            """)
            
        html_parts.append("</div>")
        return "\n".join(html_parts)
        
    async def generate_executive_summary(
        self,
        validation_report: ValidationReport,
        performance_metrics: Optional[PerformanceMetrics] = None,
        certification_alignment: Optional[CertificationAlignment] = None
    ) -> str:
        """Generate executive summary report."""
        data = {
            "content_id": validation_report.content_id,
            "timestamp": datetime.now().isoformat(),
            "status": validation_report.status.value,
            "overall_score": validation_report.quality_metrics.overall_score,
            "technical_accuracy": validation_report.quality_metrics.technical_accuracy.accuracy_score,
            "pedagogical_effectiveness": validation_report.quality_metrics.pedagogical_effectiveness.effectiveness_score,
            "accessibility_compliance": validation_report.quality_metrics.accessibility_report.compliance_score
        }
        
        # Generate summary text
        summary_parts = []
        
        if data["overall_score"] >= 0.9:
            summary_parts.append("The content meets or exceeds all quality standards.")
        elif data["overall_score"] >= 0.8:
            summary_parts.append("The content is of good quality with minor areas for improvement.")
        else:
            summary_parts.append("The content requires significant improvements to meet quality standards.")
            
        # Add specific insights
        if validation_report.issues:
            critical_count = sum(1 for i in validation_report.issues if i.severity == SeverityLevel.CRITICAL)
            if critical_count > 0:
                summary_parts.append(f"{critical_count} critical issues require immediate attention.")
                
        if performance_metrics:
            if performance_metrics.generation_time > 300:  # 5 minutes
                summary_parts.append("Generation time exceeds optimal targets.")
            if performance_metrics.api_costs > 5.0:
                summary_parts.append("API costs are higher than expected.")
                
        if certification_alignment:
            if certification_alignment.alignment_score < 0.8:
                summary_parts.append("Content alignment with certification objectives needs improvement.")
                
        data["summary_text"] = " ".join(summary_parts)
        
        # Generate recommendations
        recommendations = []
        
        # Priority 1: Critical issues
        critical_issues = [i for i in validation_report.issues if i.severity == SeverityLevel.CRITICAL]
        if critical_issues:
            recommendations.append(f"1. **Address {len(critical_issues)} critical issues immediately**")
            
        # Priority 2: Low scores
        low_score_dims = []
        for dim, score in validation_report.quality_metrics.dimension_scores.items():
            if score.score < 0.7:
                low_score_dims.append(dim.value)
                
        if low_score_dims:
            recommendations.append(f"2. **Improve {', '.join(low_score_dims)}**")
            
        # Priority 3: Performance
        if performance_metrics and performance_metrics.optimization_opportunities:
            recommendations.append("3. **Implement performance optimizations**")
            
        # Priority 4: Certification alignment
        if certification_alignment and certification_alignment.missing_objectives:
            recommendations.append(f"4. **Cover {len(certification_alignment.missing_objectives)} missing certification objectives**")
            
        if not recommendations:
            recommendations.append("• Maintain current quality standards")
            recommendations.append("• Consider minor optimizations for excellence")
            
        data["recommendations"] = "\n".join(recommendations)
        
        return self._generate_markdown_report(data, "executive_summary")
        
    async def generate_performance_report(
        self,
        performance_metrics: PerformanceMetrics,
        content_id: str,
        historical_data: Optional[List[PerformanceMetrics]] = None
    ) -> str:
        """Generate performance analysis report."""
        data = {
            "content_id": content_id,
            "timestamp": datetime.now().isoformat(),
            "generation_time": performance_metrics.generation_time,
            "memory_usage": performance_metrics.memory_usage,
            "cpu_usage": performance_metrics.cpu_usage,
            "gpu_usage": performance_metrics.gpu_usage,
            "api_calls": performance_metrics.api_calls,
            "api_costs": performance_metrics.api_costs,
            "cost_per_module": performance_metrics.api_costs / max(performance_metrics.api_calls, 1)
        }
        
        # File size analysis
        if performance_metrics.file_size:
            size_lines = []
            for format_type, size in performance_metrics.file_size.items():
                size_mb = size / (1024 * 1024)
                size_lines.append(f"- **{format_type}**: {size_mb:.2f} MB")
            data["file_size_analysis"] = "\n".join(size_lines)
        else:
            data["file_size_analysis"] = "*No file size data available*"
            
        # Optimization opportunities
        if performance_metrics.optimization_opportunities:
            opt_lines = []
            for i, opt in enumerate(performance_metrics.optimization_opportunities, 1):
                opt_lines.append(f"{i}. **{opt['area'].replace('_', ' ').title()}**")
                opt_lines.append(f"   - Current: {opt['current']}")
                opt_lines.append(f"   - Target: {opt['target']}")
                if "suggestions" in opt:
                    opt_lines.append("   - Suggestions:")
                    for suggestion in opt["suggestions"][:3]:
                        opt_lines.append(f"     - {suggestion}")
            data["optimization_opportunities"] = "\n".join(opt_lines)
        else:
            data["optimization_opportunities"] = "*No optimization opportunities identified*"
            
        # Performance trends
        if historical_data and len(historical_data) > 1:
            trend_lines = []
            
            # Calculate trends
            gen_times = [m.generation_time for m in historical_data]
            avg_time = sum(gen_times) / len(gen_times)
            trend = "improving" if gen_times[-1] < avg_time else "declining"
            
            trend_lines.append(f"- **Generation Time Trend**: {trend}")
            trend_lines.append(f"  - Average: {avg_time:.2f}s")
            trend_lines.append(f"  - Latest: {gen_times[-1]:.2f}s")
            
            data["performance_trends"] = "\n".join(trend_lines)
        else:
            data["performance_trends"] = "*Insufficient historical data for trend analysis*"
            
        return self._generate_markdown_report(data, "performance_report")
        
    async def generate_certification_report(
        self,
        certification_alignment: CertificationAlignment,
        content_id: str
    ) -> str:
        """Generate certification alignment report."""
        data = {
            "certification_id": certification_alignment.certification_id,
            "content_id": content_id,
            "alignment_score": certification_alignment.alignment_score,
            "exam_readiness": certification_alignment.exam_readiness_score,
            "covered_count": len(certification_alignment.covered_objectives),
            "partial_count": len(certification_alignment.partial_objectives),
            "missing_count": len(certification_alignment.missing_objectives)
        }
        
        # Domain coverage
        domain_lines = []
        for domain, weight in certification_alignment.weight_distribution.items():
            depth = certification_alignment.depth_analysis.get(domain, 0)
            status = "✓" if depth >= 0.8 else "⚠" if depth >= 0.5 else "✗"
            domain_lines.append(f"{status} **{domain}**")
            domain_lines.append(f"  - Weight: {weight:.1%}")
            domain_lines.append(f"  - Depth: {depth:.1%}")
        data["domain_coverage"] = "\n".join(domain_lines)
        
        # Covered objectives
        if certification_alignment.covered_objectives:
            data["covered_objectives"] = "\n".join([
                f"✓ {obj}" for obj in certification_alignment.covered_objectives[:10]
            ])
            if len(certification_alignment.covered_objectives) > 10:
                data["covered_objectives"] += f"\n... and {len(certification_alignment.covered_objectives) - 10} more"
        else:
            data["covered_objectives"] = "*No objectives fully covered*"
            
        # Partial objectives
        if certification_alignment.partial_objectives:
            partial_lines = []
            for obj_info in certification_alignment.partial_objectives[:10]:
                partial_lines.append(f"⚠ {obj_info['objective']} ({obj_info['coverage']:.1%} coverage)")
            data["partial_objectives"] = "\n".join(partial_lines)
        else:
            data["partial_objectives"] = "*No partially covered objectives*"
            
        # Missing objectives
        if certification_alignment.missing_objectives:
            data["missing_objectives"] = "\n".join([
                f"✗ {obj}" for obj in certification_alignment.missing_objectives[:10]
            ])
            if len(certification_alignment.missing_objectives) > 10:
                data["missing_objectives"] += f"\n... and {len(certification_alignment.missing_objectives) - 10} more"
        else:
            data["missing_objectives"] = "*All objectives covered*"
            
        # Weight distribution analysis
        weight_lines = []
        for domain, actual_weight in certification_alignment.weight_distribution.items():
            # Assuming we have expected weights somewhere
            weight_lines.append(f"- **{domain}**: {actual_weight:.1%}")
        data["weight_distribution"] = "\n".join(weight_lines)
        
        # Recommendations
        recommendations = []
        
        if certification_alignment.missing_objectives:
            recommendations.append(f"1. Add content for {len(certification_alignment.missing_objectives)} missing objectives")
            
        low_depth_domains = [
            domain for domain, depth in certification_alignment.depth_analysis.items()
            if depth < 0.6
        ]
        if low_depth_domains:
            recommendations.append(f"2. Increase depth of coverage for: {', '.join(low_depth_domains)}")
            
        if certification_alignment.exam_readiness_score < 0.8:
            recommendations.append("3. Add more practice questions and hands-on exercises")
            
        if not recommendations:
            recommendations.append("• Content is well-aligned with certification objectives")
            recommendations.append("• Consider adding supplementary materials for excellence")
            
        data["recommendations"] = "\n".join(recommendations)
        
        return self._generate_markdown_report(data, "certification_alignment")
        
    async def export_report(
        self,
        report_content: str,
        output_path: Path,
        format: str = "markdown"
    ) -> Path:
        """Export report to file."""
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            output_file = output_path.with_suffix(".md")
            output_file.write_text(report_content)
        elif format == "html":
            output_file = output_path.with_suffix(".html")
            html_content = await self._generate_html_report(
                {"content": report_content},
                "custom"
            )
            output_file.write_text(html_content)
        elif format == "pdf":
            # Would need a PDF generation library like reportlab
            raise NotImplementedError("PDF export not yet implemented")
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
        logger.info(f"Report exported to {output_file}")
        return output_file


class VisualizationEngine:
    """Creates visualizations for quality reports."""
    
    def __init__(self):
        self.style_config = {
            "figure.figsize": (10, 6),
            "axes.labelsize": 12,
            "axes.titlesize": 14,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10
        }
        
    async def create_validation_charts(
        self,
        validation_report: ValidationReport
    ) -> Dict[str, str]:
        """Create various charts for validation report."""
        charts = {}
        
        # Quality scores radar chart
        charts["quality_radar"] = await self._create_quality_radar_chart(
            validation_report.quality_metrics
        )
        
        # Issues by severity pie chart
        charts["issues_severity"] = await self._create_issues_severity_chart(
            validation_report.issues
        )
        
        # Dimension scores bar chart
        charts["dimension_scores"] = await self._create_dimension_scores_chart(
            validation_report.quality_metrics.dimension_scores
        )
        
        return charts
        
    async def _create_quality_radar_chart(self, metrics: QualityMetrics) -> str:
        """Create radar chart of quality dimensions."""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        
        # Prepare data
        dimensions = []
        scores = []
        
        for dim, score in metrics.dimension_scores.items():
            dimensions.append(dim.value.replace('_', '\n'))
            scores.append(score.score)
            
        # Add first point at end to close the radar
        dimensions.append(dimensions[0])
        scores.append(scores[0])
        
        # Calculate angles
        angles = [n / float(len(dimensions) - 1) * 2 * 3.14159 for n in range(len(dimensions))]
        
        # Plot
        ax.plot(angles, scores, 'o-', linewidth=2, color='#1f77b4')
        ax.fill(angles, scores, alpha=0.25, color='#1f77b4')
        
        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dimensions[:-1])
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'])
        
        # Add title
        plt.title('Quality Dimension Scores', size=16, y=1.08)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{image_base64}"
        
    async def _create_issues_severity_chart(self, issues: List[ValidationIssue]) -> str:
        """Create pie chart of issues by severity."""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Count issues by severity
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
            
        if not severity_counts:
            # No issues - create a simple text plot
            ax.text(0.5, 0.5, 'No Issues Found', 
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   fontsize=20,
                   color='green')
            ax.axis('off')
        else:
            # Create pie chart
            labels = list(severity_counts.keys())
            sizes = list(severity_counts.values())
            colors = {
                'critical': '#d62728',
                'high': '#ff7f0e',
                'medium': '#ffbb78',
                'low': '#2ca02c',
                'info': '#1f77b4'
            }
            
            pie_colors = [colors.get(label, '#gray') for label in labels]
            
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=pie_colors,
                autopct='%1.0f%%',
                startangle=90
            )
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_weight('bold')
                autotext.set_color('white')
                
            ax.set_title('Issues by Severity', fontsize=16)
            
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{image_base64}"
        
    async def _create_dimension_scores_chart(
        self,
        dimension_scores: Dict[QualityDimension, 'QualityScore']
    ) -> str:
        """Create bar chart of dimension scores."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Prepare data
        dimensions = []
        scores = []
        colors = []
        
        for dim, score in dimension_scores.items():
            dimensions.append(dim.value.replace('_', ' ').title())
            scores.append(score.score)
            
            # Color based on score
            if score.score >= 0.9:
                colors.append('#2ca02c')  # Green
            elif score.score >= 0.8:
                colors.append('#1f77b4')  # Blue
            elif score.score >= 0.7:
                colors.append('#ffbb78')  # Light orange
            else:
                colors.append('#d62728')  # Red
                
        # Create bars
        bars = ax.bar(range(len(dimensions)), scores, color=colors)
        
        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{score:.1%}',
                   ha='center', va='bottom', fontweight='bold')
                   
        # Customize chart
        ax.set_xlabel('Quality Dimension', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Quality Scores by Dimension', fontsize=16)
        ax.set_ylim(0, 1.1)
        ax.set_xticks(range(len(dimensions)))
        ax.set_xticklabels(dimensions, rotation=45, ha='right')
        
        # Add target line
        ax.axhline(y=0.85, color='gray', linestyle='--', alpha=0.7, label='Target (85%)')
        ax.legend()
        
        # Add grid
        ax.grid(True, axis='y', alpha=0.3)
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        plt.close()
        
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{image_base64}"
