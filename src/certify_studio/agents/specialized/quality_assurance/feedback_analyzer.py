"""
Feedback Analyzer for Quality Assurance Agent.

This module analyzes feedback from multiple sources:
- User feedback and ratings
- Automated quality checks
- Expert reviews
- Learning effectiveness metrics
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import statistics

from .models import (
    QAFeedback,
    ValidationIssue,
    SeverityLevel,
    QualityDimension,
    ImprovementSuggestion,
    ImprovementType,
    LearningRecord
)
from ....core.llm import LLMClient
from ....core.config import Config

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Analyzes feedback to improve content quality."""
    
    def __init__(self, config: Config):
        """Initialize the feedback analyzer."""
        self.config = config
        self.llm_client = LLMClient(config)
        self.feedback_history = defaultdict(list)
        self.pattern_detector = PatternDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.learning_records = []
        
    async def analyze_feedback(
        self,
        content_id: str,
        feedback_data: List[Dict[str, Any]],
        validation_report: Optional[Dict[str, Any]] = None
    ) -> QAFeedback:
        """Analyze feedback from various sources."""
        logger.info(f"Analyzing feedback for content {content_id}")
        
        qa_feedback = QAFeedback(content_id=content_id)
        
        # Categorize feedback by type
        user_feedback = [f for f in feedback_data if f.get("type") == "user"]
        automated_feedback = [f for f in feedback_data if f.get("type") == "automated"]
        expert_feedback = [f for f in feedback_data if f.get("type") == "expert"]
        
        # Analyze user feedback
        if user_feedback:
            user_analysis = await self._analyze_user_feedback(user_feedback)
            qa_feedback.user_satisfaction_score = user_analysis["satisfaction_score"]
            qa_feedback.quality_impact.update(user_analysis["quality_impact"])
            
        # Analyze automated feedback
        if automated_feedback:
            auto_analysis = await self._analyze_automated_feedback(automated_feedback)
            qa_feedback.issues_found_post_release.extend(auto_analysis["issues"])
            qa_feedback.quality_impact.update(auto_analysis["quality_impact"])
            
        # Analyze expert feedback
        if expert_feedback:
            expert_analysis = await self._analyze_expert_feedback(expert_feedback)
            qa_feedback.learning_effectiveness_score = expert_analysis["effectiveness_score"]
            qa_feedback.suggestions_implemented.extend(expert_analysis["implemented"])
            qa_feedback.suggestions_rejected.extend(expert_analysis["rejected"])
            
        # Combine with validation report if available
        if validation_report:
            qa_feedback.quality_impact.update(
                self._extract_quality_impact_from_validation(validation_report)
            )
            
        # Detect patterns across feedback
        patterns = await self.pattern_detector.detect_patterns(feedback_data)
        qa_feedback.lessons_learned = self._extract_lessons_from_patterns(patterns)
        
        # Update learning records
        await self._update_learning_records(qa_feedback, patterns)
        
        # Store feedback for historical analysis
        self._store_feedback(content_id, qa_feedback)
        
        logger.info(f"Feedback analysis complete. Satisfaction: {qa_feedback.user_satisfaction_score}")
        return qa_feedback
        
    async def _analyze_user_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user feedback for insights."""
        analysis = {
            "satisfaction_score": 0.0,
            "quality_impact": {},
            "common_complaints": [],
            "common_praises": []
        }
        
        # Extract ratings
        ratings = [f.get("rating", 0) for f in feedback if "rating" in f]
        if ratings:
            analysis["satisfaction_score"] = statistics.mean(ratings) / 5.0  # Normalize to 0-1
            
        # Analyze comments
        comments = [f.get("comment", "") for f in feedback if "comment" in f]
        if comments:
            # Sentiment analysis
            sentiments = await self.sentiment_analyzer.analyze_batch(comments)
            
            # Categorize feedback
            positive_comments = []
            negative_comments = []
            
            for comment, sentiment in zip(comments, sentiments):
                if sentiment["score"] > 0.6:
                    positive_comments.append(comment)
                elif sentiment["score"] < 0.4:
                    negative_comments.append(comment)
                    
            # Extract themes
            if negative_comments:
                analysis["common_complaints"] = await self._extract_themes(negative_comments)
            if positive_comments:
                analysis["common_praises"] = await self._extract_themes(positive_comments)
                
        # Map to quality dimensions
        analysis["quality_impact"] = await self._map_feedback_to_quality_dimensions(
            analysis["common_complaints"],
            analysis["common_praises"]
        )
        
        return analysis
        
    async def _analyze_automated_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze automated feedback from monitoring systems."""
        analysis = {
            "issues": [],
            "quality_impact": {},
            "performance_degradation": False
        }
        
        # Convert to ValidationIssue objects
        for item in feedback:
            if item.get("issue_type"):
                issue = ValidationIssue(
                    dimension=QualityDimension(item.get("dimension", "technical_accuracy")),
                    severity=SeverityLevel(item.get("severity", "medium")),
                    title=item.get("title", "Automated Issue"),
                    description=item.get("description", ""),
                    location=item.get("location", {}),
                    confidence=item.get("confidence", 0.8)
                )
                analysis["issues"].append(issue)
                
        # Analyze performance metrics
        performance_metrics = [f for f in feedback if f.get("type") == "performance"]
        if performance_metrics:
            # Check for degradation
            degradation = any(
                m.get("value", 0) > m.get("threshold", float('inf'))
                for m in performance_metrics
            )
            analysis["performance_degradation"] = degradation
            
        # Calculate quality impact
        for issue in analysis["issues"]:
            dimension = issue.dimension
            severity_weight = {
                SeverityLevel.CRITICAL: -0.3,
                SeverityLevel.HIGH: -0.2,
                SeverityLevel.MEDIUM: -0.1,
                SeverityLevel.LOW: -0.05
            }
            
            current_impact = analysis["quality_impact"].get(dimension, 0.0)
            analysis["quality_impact"][dimension] = current_impact + severity_weight.get(issue.severity, 0)
            
        return analysis
        
    async def _analyze_expert_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze feedback from subject matter experts."""
        analysis = {
            "effectiveness_score": 0.0,
            "implemented": [],
            "rejected": [],
            "key_insights": []
        }
        
        # Extract effectiveness ratings
        effectiveness_ratings = [
            f.get("effectiveness_rating", 0)
            for f in feedback
            if "effectiveness_rating" in f
        ]
        if effectiveness_ratings:
            analysis["effectiveness_score"] = statistics.mean(effectiveness_ratings) / 10.0
            
        # Process suggestions
        for item in feedback:
            if item.get("suggestion"):
                suggestion = item["suggestion"]
                if item.get("implemented", False):
                    analysis["implemented"].append(suggestion)
                elif item.get("rejected", False):
                    analysis["rejected"].append(suggestion)
                    
            if item.get("insight"):
                analysis["key_insights"].append(item["insight"])
                
        return analysis
        
    async def _extract_themes(self, texts: List[str]) -> List[str]:
        """Extract common themes from text feedback."""
        try:
            prompt = f"""
            Extract the main themes from these feedback comments.
            Return the top 5 themes as a JSON array of strings.
            
            Comments:
            {chr(10).join(texts[:20])}  # Limit to prevent token overflow
            
            Focus on specific, actionable themes.
            """
            
            response = await self.llm_client.generate(prompt)
            themes = json.loads(response)
            return themes[:5]  # Top 5 themes
            
        except Exception as e:
            logger.error(f"Failed to extract themes: {e}")
            return []
            
    async def _map_feedback_to_quality_dimensions(
        self,
        complaints: List[str],
        praises: List[str]
    ) -> Dict[QualityDimension, float]:
        """Map feedback themes to quality dimensions."""
        impact = {}
        
        # Keywords for each dimension
        dimension_keywords = {
            QualityDimension.TECHNICAL_ACCURACY: ["incorrect", "wrong", "error", "bug", "mistake"],
            QualityDimension.PEDAGOGICAL_EFFECTIVENESS: ["confusing", "unclear", "hard to understand", "too fast", "too slow"],
            QualityDimension.ACCESSIBILITY_COMPLIANCE: ["can't see", "can't hear", "no captions", "contrast", "font size"],
            QualityDimension.USER_EXPERIENCE: ["difficult", "frustrating", "annoying", "clunky", "smooth", "easy"],
            QualityDimension.VISUAL_QUALITY: ["ugly", "beautiful", "blurry", "clear", "professional"],
            QualityDimension.INTERACTIVE_ENGAGEMENT: ["boring", "engaging", "interactive", "passive", "fun"]
        }
        
        # Analyze complaints (negative impact)
        for complaint in complaints:
            complaint_lower = complaint.lower()
            for dimension, keywords in dimension_keywords.items():
                if any(keyword in complaint_lower for keyword in keywords):
                    impact[dimension] = impact.get(dimension, 0) - 0.1
                    
        # Analyze praises (positive impact)
        for praise in praises:
            praise_lower = praise.lower()
            for dimension, keywords in dimension_keywords.items():
                # Look for positive versions
                if any(keyword in praise_lower for keyword in ["clear", "accurate", "easy", "beautiful", "engaging"]):
                    impact[dimension] = impact.get(dimension, 0) + 0.1
                    
        return impact
        
    def _extract_quality_impact_from_validation(
        self,
        validation_report: Dict[str, Any]
    ) -> Dict[QualityDimension, float]:
        """Extract quality impact from validation report."""
        impact = {}
        
        if "quality_metrics" in validation_report:
            metrics = validation_report["quality_metrics"]
            
            # Map scores to impact (1.0 = no impact, < 1.0 = negative impact)
            if "technical_accuracy" in metrics:
                impact[QualityDimension.TECHNICAL_ACCURACY] = metrics["technical_accuracy"]["accuracy_score"] - 1.0
                
            if "accessibility_report" in metrics:
                impact[QualityDimension.ACCESSIBILITY_COMPLIANCE] = metrics["accessibility_report"]["compliance_score"] - 1.0
                
        return impact
        
    def _extract_lessons_from_patterns(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Extract actionable lessons from detected patterns."""
        lessons = []
        
        for pattern in patterns:
            if pattern["confidence"] > 0.7:  # High confidence patterns
                lesson = f"{pattern['description']} (seen {pattern['occurrences']} times)"
                
                if pattern.get("recommendation"):
                    lesson += f" - Recommendation: {pattern['recommendation']}"
                    
                lessons.append(lesson)
                
        return lessons[:10]  # Top 10 lessons
        
    async def _update_learning_records(
        self,
        feedback: QAFeedback,
        patterns: List[Dict[str, Any]]
    ):
        """Update learning records based on feedback analysis."""
        for pattern in patterns:
            # Check if pattern already exists
            existing_record = next(
                (r for r in self.learning_records if r.pattern_description == pattern["description"]),
                None
            )
            
            if existing_record:
                # Update existing record
                existing_record.occurrences += pattern["occurrences"]
                existing_record.last_seen = datetime.now()
                existing_record.confidence = (existing_record.confidence + pattern["confidence"]) / 2
            else:
                # Create new record
                record = LearningRecord(
                    pattern_type=pattern["type"],
                    pattern_description=pattern["description"],
                    occurrences=pattern["occurrences"],
                    impact_on_quality=pattern.get("quality_impact", {}),
                    suggested_prevention=pattern.get("recommendation", ""),
                    confidence=pattern["confidence"],
                    applicable_contexts=pattern.get("contexts", [])
                )
                self.learning_records.append(record)
                
    def _store_feedback(self, content_id: str, feedback: QAFeedback):
        """Store feedback for historical analysis."""
        self.feedback_history[content_id].append({
            "timestamp": datetime.now(),
            "feedback": feedback
        })
        
        # Keep only last 50 entries per content
        if len(self.feedback_history[content_id]) > 50:
            self.feedback_history[content_id] = self.feedback_history[content_id][-50:]
            
    async def generate_improvement_suggestions(
        self,
        feedback: QAFeedback,
        validation_report: Optional[Dict[str, Any]] = None
    ) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions based on feedback."""
        suggestions = []
        
        # Based on quality impact
        for dimension, impact in feedback.quality_impact.items():
            if impact < -0.1:  # Significant negative impact
                suggestion = await self._generate_dimension_improvement(dimension, abs(impact))
                if suggestion:
                    suggestions.append(suggestion)
                    
        # Based on specific issues
        for issue in feedback.issues_found_post_release:
            if issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                suggestion = await self._generate_issue_improvement(issue)
                if suggestion:
                    suggestions.append(suggestion)
                    
        # Based on patterns
        for lesson in feedback.lessons_learned:
            suggestion = await self._generate_pattern_improvement(lesson)
            if suggestion:
                suggestions.append(suggestion)
                    
        # Sort by priority
        suggestions.sort(key=lambda s: {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 4
        }.get(s.priority, 5))
        
        return suggestions[:10]  # Top 10 suggestions
        
    async def _generate_dimension_improvement(
        self,
        dimension: QualityDimension,
        impact_magnitude: float
    ) -> Optional[ImprovementSuggestion]:
        """Generate improvement suggestion for a quality dimension."""
        dimension_improvements = {
            QualityDimension.TECHNICAL_ACCURACY: {
                "type": ImprovementType.CONTENT_CORRECTION,
                "title": "Improve Technical Accuracy",
                "steps": [
                    "Review all technical content for accuracy",
                    "Validate code examples and commands",
                    "Update outdated information",
                    "Add verification references"
                ]
            },
            QualityDimension.PEDAGOGICAL_EFFECTIVENESS: {
                "type": ImprovementType.PEDAGOGICAL_ENHANCEMENT,
                "title": "Enhance Learning Effectiveness",
                "steps": [
                    "Simplify complex explanations",
                    "Add more examples and practice exercises",
                    "Improve content flow and progression",
                    "Add visual aids for difficult concepts"
                ]
            },
            QualityDimension.ACCESSIBILITY_COMPLIANCE: {
                "type": ImprovementType.ACCESSIBILITY_FIX,
                "title": "Fix Accessibility Issues",
                "steps": [
                    "Add missing alt text for images",
                    "Improve color contrast ratios",
                    "Ensure keyboard navigation works",
                    "Add captions to all videos"
                ]
            },
            QualityDimension.VISUAL_QUALITY: {
                "type": ImprovementType.VISUAL_IMPROVEMENT,
                "title": "Enhance Visual Quality",
                "steps": [
                    "Improve image and video resolution",
                    "Ensure consistent visual style",
                    "Optimize animations for smoothness",
                    "Fix any visual glitches"
                ]
            }
        }
        
        if dimension not in dimension_improvements:
            return None
            
        improvement = dimension_improvements[dimension]
        
        return ImprovementSuggestion(
            type=improvement["type"],
            priority=SeverityLevel.HIGH if impact_magnitude > 0.2 else SeverityLevel.MEDIUM,
            title=improvement["title"],
            description=f"Quality impact detected: {impact_magnitude:.1%} degradation in {dimension.value}",
            rationale=f"User feedback indicates issues with {dimension.value.replace('_', ' ')}",
            expected_impact={dimension: impact_magnitude},
            implementation_steps=improvement["steps"],
            estimated_effort=2.0 * impact_magnitude * 10,  # hours
            auto_implementable=dimension == QualityDimension.ACCESSIBILITY_COMPLIANCE
        )
        
    async def _generate_issue_improvement(
        self,
        issue: ValidationIssue
    ) -> Optional[ImprovementSuggestion]:
        """Generate improvement suggestion for a specific issue."""
        return ImprovementSuggestion(
            type=ImprovementType.CONTENT_CORRECTION,
            priority=issue.severity,
            title=f"Fix: {issue.title}",
            description=issue.description,
            rationale="Issue detected in post-release validation",
            expected_impact={issue.dimension: 0.1},
            implementation_steps=[
                f"Locate issue: {issue.location}",
                f"Apply fix: {issue.suggested_fix}" if issue.suggested_fix else "Implement appropriate fix",
                "Test the fix",
                "Verify no regressions"
            ],
            estimated_effort=1.0 if issue.auto_fixable else 3.0,
            auto_implementable=issue.auto_fixable,
            implementation_code=issue.suggested_fix if issue.auto_fixable else None
        )
        
    async def _generate_pattern_improvement(
        self,
        lesson: str
    ) -> Optional[ImprovementSuggestion]:
        """Generate improvement based on learned patterns."""
        try:
            # Use LLM to generate specific improvement
            prompt = f"""
            Based on this lesson learned from content feedback:
            "{lesson}"
            
            Generate a specific improvement suggestion with:
            1. Type of improvement needed
            2. Clear implementation steps
            3. Expected impact
            
            Format as JSON with fields: type, title, description, steps, impact
            """
            
            response = await self.llm_client.generate(prompt)
            suggestion_data = json.loads(response)
            
            return ImprovementSuggestion(
                type=ImprovementType(suggestion_data.get("type", "content_correction")),
                priority=SeverityLevel.MEDIUM,
                title=suggestion_data.get("title", "Pattern-based Improvement"),
                description=suggestion_data.get("description", lesson),
                rationale=f"Pattern detected: {lesson}",
                implementation_steps=suggestion_data.get("steps", []),
                estimated_effort=3.0,
                auto_implementable=False
            )
            
        except Exception as e:
            logger.error(f"Failed to generate pattern improvement: {e}")
            return None
            
    async def analyze_historical_feedback(
        self,
        content_id: str,
        time_window: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """Analyze historical feedback trends."""
        if content_id not in self.feedback_history:
            return {"error": "No historical feedback available"}
            
        history = self.feedback_history[content_id]
        cutoff_time = datetime.now() - time_window
        
        # Filter by time window
        recent_feedback = [
            entry for entry in history
            if entry["timestamp"] > cutoff_time
        ]
        
        if not recent_feedback:
            return {"error": "No feedback in specified time window"}
            
        # Analyze trends
        satisfaction_scores = [
            entry["feedback"].user_satisfaction_score
            for entry in recent_feedback
            if entry["feedback"].user_satisfaction_score is not None
        ]
        
        effectiveness_scores = [
            entry["feedback"].learning_effectiveness_score
            for entry in recent_feedback
            if entry["feedback"].learning_effectiveness_score is not None
        ]
        
        # Calculate statistics
        analysis = {
            "period": {
                "start": recent_feedback[0]["timestamp"],
                "end": recent_feedback[-1]["timestamp"],
                "feedback_count": len(recent_feedback)
            },
            "satisfaction": {
                "average": statistics.mean(satisfaction_scores) if satisfaction_scores else None,
                "trend": self._calculate_trend(satisfaction_scores),
                "latest": satisfaction_scores[-1] if satisfaction_scores else None
            },
            "effectiveness": {
                "average": statistics.mean(effectiveness_scores) if effectiveness_scores else None,
                "trend": self._calculate_trend(effectiveness_scores),
                "latest": effectiveness_scores[-1] if effectiveness_scores else None
            },
            "common_issues": self._extract_common_issues(recent_feedback),
            "improvement_velocity": self._calculate_improvement_velocity(recent_feedback)
        }
        
        return analysis
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a series of values."""
        if len(values) < 2:
            return "insufficient_data"
            
        # Simple linear regression
        n = len(values)
        if n == 0:
            return "no_data"
            
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
            
    def _extract_common_issues(self, feedback_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract most common issues from feedback."""
        issue_counts = defaultdict(int)
        issue_examples = defaultdict(list)
        
        for entry in feedback_entries:
            feedback = entry["feedback"]
            for issue in feedback.issues_found_post_release:
                issue_key = f"{issue.dimension.value}:{issue.title}"
                issue_counts[issue_key] += 1
                issue_examples[issue_key].append(issue)
                
        # Sort by frequency
        common_issues = []
        for issue_key, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            dimension, title = issue_key.split(":", 1)
            common_issues.append({
                "dimension": dimension,
                "title": title,
                "frequency": count,
                "percentage": count / len(feedback_entries) * 100,
                "example": issue_examples[issue_key][0].description
            })
            
        return common_issues
        
    def _calculate_improvement_velocity(self, feedback_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate how quickly improvements are being made."""
        if len(feedback_entries) < 2:
            return {"status": "insufficient_data"}
            
        # Track suggestions over time
        implemented_over_time = []
        rejected_over_time = []
        
        for entry in feedback_entries:
            feedback = entry["feedback"]
            implemented_over_time.append(len(feedback.suggestions_implemented))
            rejected_over_time.append(len(feedback.suggestions_rejected))
            
        # Calculate rates
        total_implemented = sum(implemented_over_time)
        total_rejected = sum(rejected_over_time)
        total_suggestions = total_implemented + total_rejected
        
        if total_suggestions == 0:
            implementation_rate = 0
        else:
            implementation_rate = total_implemented / total_suggestions
            
        return {
            "status": "active",
            "total_implemented": total_implemented,
            "total_rejected": total_rejected,
            "implementation_rate": implementation_rate,
            "trend": self._calculate_trend(implemented_over_time),
            "average_per_period": total_implemented / len(feedback_entries)
        }


class PatternDetector:
    """Detects patterns in feedback data."""
    
    def __init__(self):
        self.pattern_cache = {}
        
    async def detect_patterns(self, feedback_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in feedback."""
        patterns = []
        
        # Group feedback by type
        by_type = defaultdict(list)
        for item in feedback_data:
            by_type[item.get("type", "unknown")].append(item)
            
        # Detect patterns in each type
        for feedback_type, items in by_type.items():
            if len(items) >= 3:  # Need at least 3 items for a pattern
                type_patterns = await self._detect_type_patterns(feedback_type, items)
                patterns.extend(type_patterns)
                
        # Detect cross-type patterns
        if len(feedback_data) >= 5:
            cross_patterns = await self._detect_cross_patterns(feedback_data)
            patterns.extend(cross_patterns)
            
        # Sort by confidence and occurrences
        patterns.sort(key=lambda p: (p["confidence"], p["occurrences"]), reverse=True)
        
        return patterns
        
    async def _detect_type_patterns(self, feedback_type: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns within a feedback type."""
        patterns = []
        
        if feedback_type == "user":
            # Look for recurring complaints
            complaints = [item.get("comment", "") for item in items if item.get("rating", 5) < 3]
            if complaints:
                common_words = self._extract_common_words(complaints)
                for word, count in common_words:
                    if count >= 3:
                        patterns.append({
                            "type": "common_complaint",
                            "description": f"Users frequently mention '{word}' in negative feedback",
                            "occurrences": count,
                            "confidence": min(count / len(complaints), 1.0),
                            "recommendation": f"Address issues related to '{word}'",
                            "contexts": [feedback_type]
                        })
                        
        elif feedback_type == "automated":
            # Look for recurring technical issues
            issue_types = defaultdict(int)
            for item in items:
                if item.get("issue_type"):
                    issue_types[item["issue_type"]] += 1
                    
            for issue_type, count in issue_types.items():
                if count >= 2:
                    patterns.append({
                        "type": "recurring_issue",
                        "description": f"Technical issue '{issue_type}' occurs frequently",
                        "occurrences": count,
                        "confidence": 0.8,
                        "recommendation": f"Implement automated prevention for '{issue_type}'",
                        "contexts": [feedback_type]
                    })
                    
        return patterns
        
    async def _detect_cross_patterns(self, feedback_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns across different feedback types."""
        patterns = []
        
        # Look for correlation between user complaints and technical issues
        user_complaints = [f for f in feedback_data if f.get("type") == "user" and f.get("rating", 5) < 3]
        technical_issues = [f for f in feedback_data if f.get("type") == "automated" and f.get("issue_type")]
        
        if user_complaints and technical_issues:
            # Simple correlation check
            complaint_topics = set()
            for complaint in user_complaints:
                if complaint.get("comment"):
                    words = complaint["comment"].lower().split()
                    complaint_topics.update(words)
                    
            issue_topics = set()
            for issue in technical_issues:
                if issue.get("description"):
                    words = issue["description"].lower().split()
                    issue_topics.update(words)
                    
            common_topics = complaint_topics.intersection(issue_topics)
            if common_topics:
                patterns.append({
                    "type": "correlated_issues",
                    "description": f"User complaints correlate with technical issues: {', '.join(list(common_topics)[:3])}",
                    "occurrences": len(common_topics),
                    "confidence": 0.7,
                    "recommendation": "Prioritize fixing technical issues that directly impact user experience",
                    "contexts": ["user", "automated"]
                })
                
        return patterns
        
    def _extract_common_words(self, texts: List[str], min_length: int = 4) -> List[Tuple[str, int]]:
        """Extract common meaningful words from texts."""
        word_counts = defaultdict(int)
        stop_words = {"the", "and", "but", "for", "with", "this", "that", "have", "from", "what", "when", "where", "which", "while"}
        
        for text in texts:
            words = text.lower().split()
            for word in words:
                # Clean word
                word = ''.join(c for c in word if c.isalnum())
                if len(word) >= min_length and word not in stop_words:
                    word_counts[word] += 1
                    
        # Sort by frequency
        return sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]


class SentimentAnalyzer:
    """Analyzes sentiment of text feedback."""
    
    def __init__(self):
        self.positive_words = {
            "excellent", "great", "good", "amazing", "helpful", "clear",
            "easy", "useful", "effective", "comprehensive", "well-explained"
        }
        self.negative_words = {
            "confusing", "difficult", "hard", "unclear", "bad", "poor",
            "complicated", "frustrating", "boring", "incomplete", "wrong"
        }
        
    async def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """Analyze sentiment for multiple texts."""
        results = []
        for text in texts:
            sentiment = await self.analyze(text)
            results.append(sentiment)
        return results
        
    async def analyze(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single text."""
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Calculate simple sentiment score
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            score = 0.5  # Neutral
        else:
            score = positive_count / total_sentiment_words
            
        return {
            "score": score,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "confidence": min(total_sentiment_words / 10, 1.0)  # Higher confidence with more sentiment words
        }
