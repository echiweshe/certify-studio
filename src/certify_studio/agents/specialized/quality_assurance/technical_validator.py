"""
Technical Validator for Quality Assurance Agent.

This module validates technical accuracy of content including:
- Code correctness
- Technical facts verification
- API/command validation
- Version compatibility
- Best practices compliance
"""

import asyncio
import ast
import json
import re
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
import logging

from .models import (
    TechnicalAccuracy,
    ValidationIssue,
    SeverityLevel,
    QualityDimension
)
from ....core.llm import MultimodalLLM
from ....core.llm.multimodal_llm import MultimodalMessage
from ....config import settings

logger = logging.getLogger(__name__)


class TechnicalValidator:
    """Validates technical accuracy of educational content."""
    
    def __init__(self, llm: Optional[MultimodalLLM] = None):
        """Initialize the technical validator."""
        self.llm = llm or MultimodalLLM()
        self.validation_cache = {}
        self.known_technologies = self._load_technology_database()
        self.best_practices = self._load_best_practices()
        
    def _load_technology_database(self) -> Dict[str, Any]:
        """Load database of known technologies and their versions."""
        return {
            "aws": {
                "services": ["EC2", "S3", "Lambda", "RDS", "DynamoDB", "VPC", "IAM", "CloudFormation"],
                "current_versions": {"CLI": "2.x", "SDK": "3.x"},
                "deprecated": ["EC2-Classic"],
                "best_practices": ["least-privilege", "encryption-at-rest", "multi-az"]
            },
            "python": {
                "current_version": "3.12",
                "deprecated_features": ["print statement", "xrange", "raw_input"],
                "best_practices": ["type hints", "async/await", "context managers"]
            },
            "kubernetes": {
                "current_version": "1.28",
                "api_versions": {"apps/v1": "current", "extensions/v1beta1": "deprecated"},
                "best_practices": ["resource-limits", "health-checks", "namespaces"]
            },
            # Add more technologies as needed
        }
        
    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load best practices for various technologies."""
        return {
            "security": [
                "never hardcode credentials",
                "use environment variables for secrets",
                "implement least privilege",
                "encrypt data in transit and at rest",
                "validate all inputs"
            ],
            "performance": [
                "use caching appropriately",
                "implement pagination for large datasets",
                "optimize database queries",
                "use async operations for I/O",
                "monitor resource usage"
            ],
            "code_quality": [
                "follow naming conventions",
                "write meaningful comments",
                "handle errors gracefully",
                "write testable code",
                "avoid code duplication"
            ]
        }
        
    async def validate_technical_content(
        self,
        content: Dict[str, Any],
        certification_context: Optional[str] = None
    ) -> TechnicalAccuracy:
        """Validate technical accuracy of content."""
        logger.info("Starting technical validation")
        
        accuracy = TechnicalAccuracy()
        issues = []
        
        # Extract technical elements from content
        technical_elements = await self._extract_technical_elements(content)
        
        # Validate each type of technical content
        if technical_elements.get("code_blocks"):
            code_issues = await self._validate_code_blocks(
                technical_elements["code_blocks"],
                certification_context
            )
            issues.extend(code_issues)
            
        if technical_elements.get("commands"):
            command_issues = await self._validate_commands(
                technical_elements["commands"]
            )
            issues.extend(command_issues)
            
        if technical_elements.get("technical_facts"):
            fact_issues = await self._validate_technical_facts(
                technical_elements["technical_facts"],
                certification_context
            )
            issues.extend(fact_issues)
            
        if technical_elements.get("configurations"):
            config_issues = await self._validate_configurations(
                technical_elements["configurations"]
            )
            issues.extend(config_issues)
            
        # Check for deprecated features
        deprecation_issues = await self._check_deprecations(technical_elements)
        issues.extend(deprecation_issues)
        
        # Verify best practices
        practice_issues = await self._check_best_practices(technical_elements)
        issues.extend(practice_issues)
        
        # Calculate accuracy score
        accuracy.incorrect_statements = [i for i in issues if i.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        accuracy.outdated_information = deprecation_issues
        accuracy.missing_context = [i for i in issues if "context" in i.description.lower()]
        
        total_elements = sum(len(v) if isinstance(v, list) else 1 for v in technical_elements.values())
        accuracy.accuracy_score = max(0, 1 - (len(issues) / max(total_elements, 1)))
        accuracy.is_accurate = accuracy.accuracy_score >= 0.9 and not accuracy.incorrect_statements
        
        # Add reference sources
        accuracy.reference_sources = await self._gather_reference_sources(
            technical_elements,
            certification_context
        )
        
        logger.info(f"Technical validation complete. Score: {accuracy.accuracy_score}")
        return accuracy
        
    async def _extract_technical_elements(self, content: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Extract technical elements from content for validation."""
        elements = {
            "code_blocks": [],
            "commands": [],
            "technical_facts": [],
            "configurations": [],
            "api_calls": [],
            "file_paths": []
        }
        
        # Extract from different content types
        if "text" in content:
            text_elements = await self._extract_from_text(content["text"])
            for key in elements:
                elements[key].extend(text_elements.get(key, []))
                
        if "code" in content:
            elements["code_blocks"].append({
                "code": content["code"],
                "language": content.get("language", "unknown"),
                "context": content.get("context", "")
            })
            
        if "diagrams" in content:
            for diagram in content.get("diagrams", []):
                if diagram.get("code"):
                    elements["code_blocks"].append({
                        "code": diagram["code"],
                        "language": "diagram",
                        "context": diagram.get("description", "")
                    })
                    
        return elements
        
    async def _extract_from_text(self, text: str) -> Dict[str, List[Any]]:
        """Extract technical elements from text content."""
        elements = {
            "code_blocks": [],
            "commands": [],
            "technical_facts": [],
            "configurations": []
        }
        
        # Extract code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        code_matches = re.findall(code_pattern, text, re.DOTALL)
        for lang, code in code_matches:
            elements["code_blocks"].append({
                "code": code,
                "language": lang or "unknown",
                "context": text[:50]  # Surrounding context
            })
            
        # Extract inline code/commands
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.findall(inline_pattern, text)
        for match in inline_matches:
            if any(cmd in match for cmd in ["$", "sudo", "npm", "pip", "docker", "kubectl"]):
                elements["commands"].append(match)
                
        # Extract technical statements (simplified - could use NLP)
        sentences = text.split(".")
        for sentence in sentences:
            if any(tech in sentence.lower() for tech in ["api", "version", "supports", "requires", "compatible"]):
                elements["technical_facts"].append(sentence.strip())
                
        return elements
        
    async def _validate_code_blocks(
        self,
        code_blocks: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> List[ValidationIssue]:
        """Validate code blocks for syntax and best practices."""
        issues = []
        
        for block in code_blocks:
            code = block["code"]
            language = block["language"].lower()
            
            # Language-specific validation
            if language == "python":
                block_issues = await self._validate_python_code(code, block.get("context", ""))
                issues.extend(block_issues)
            elif language == "javascript" or language == "typescript":
                block_issues = await self._validate_javascript_code(code, block.get("context", ""))
                issues.extend(block_issues)
            elif language == "yaml":
                block_issues = await self._validate_yaml_code(code, block.get("context", ""))
                issues.extend(block_issues)
            elif language == "json":
                block_issues = await self._validate_json_code(code, block.get("context", ""))
                issues.extend(block_issues)
            elif language == "bash" or language == "shell":
                block_issues = await self._validate_shell_code(code, block.get("context", ""))
                issues.extend(block_issues)
            else:
                # Generic validation using LLM
                block_issues = await self._validate_generic_code(code, language, block.get("context", ""))
                issues.extend(block_issues)
                
        return issues
        
    async def _validate_python_code(self, code: str, context: str) -> List[ValidationIssue]:
        """Validate Python code for syntax and best practices."""
        issues = []
        
        # Syntax validation
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append(ValidationIssue(
                dimension=QualityDimension.TECHNICAL_ACCURACY,
                severity=SeverityLevel.CRITICAL,
                title="Python Syntax Error",
                description=f"Syntax error in Python code: {str(e)}",
                location={"type": "code", "language": "python", "line": e.lineno},
                suggested_fix=f"Fix syntax error at line {e.lineno}: {e.msg}",
                auto_fixable=False
            ))
            
        # Check for deprecated features
        deprecated_patterns = [
            (r'\bprint\s+[^(]', "Use print() function instead of print statement"),
            (r'\bxrange\(', "Use range() instead of xrange() in Python 3"),
            (r'\braw_input\(', "Use input() instead of raw_input() in Python 3"),
        ]
        
        for pattern, message in deprecated_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    title="Deprecated Python Feature",
                    description=message,
                    location={"type": "code", "language": "python"},
                    suggested_fix=message,
                    auto_fixable=True
                ))
                
        # Check for security issues
        security_patterns = [
            (r'eval\(', "Avoid using eval() for security reasons"),
            (r'exec\(', "Avoid using exec() for security reasons"),
            (r'__import__\(', "Avoid using __import__() directly"),
            (r'pickle\.loads?\(', "Be careful with pickle - only load trusted data"),
        ]
        
        for pattern, message in security_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    title="Security Concern",
                    description=message,
                    location={"type": "code", "language": "python"},
                    suggested_fix=message,
                    auto_fixable=False
                ))
                
        return issues
        
    async def _validate_javascript_code(self, code: str, context: str) -> List[ValidationIssue]:
        """Validate JavaScript/TypeScript code."""
        issues = []
        
        # Check for common issues
        js_patterns = [
            (r'var\s+\w+', "Use 'let' or 'const' instead of 'var'", SeverityLevel.MEDIUM),
            (r'==(?!=)', "Use '===' instead of '==' for comparison", SeverityLevel.MEDIUM),
            (r'!=(?!=)', "Use '!==' instead of '!=' for comparison", SeverityLevel.MEDIUM),
            (r'console\.(log|error|warn)', "Remove console statements in production", SeverityLevel.LOW),
        ]
        
        for pattern, message, severity in js_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=severity,
                    title="JavaScript Best Practice",
                    description=message,
                    location={"type": "code", "language": "javascript"},
                    suggested_fix=message,
                    auto_fixable=severity != SeverityLevel.LOW
                ))
                
        return issues
        
    async def _validate_yaml_code(self, code: str, context: str) -> List[ValidationIssue]:
        """Validate YAML configuration."""
        issues = []
        
        try:
            import yaml
            yaml.safe_load(code)
        except yaml.YAMLError as e:
            issues.append(ValidationIssue(
                dimension=QualityDimension.TECHNICAL_ACCURACY,
                severity=SeverityLevel.CRITICAL,
                title="YAML Syntax Error",
                description=f"YAML parsing error: {str(e)}",
                location={"type": "code", "language": "yaml"},
                suggested_fix="Fix YAML syntax according to error message",
                auto_fixable=False
            ))
            
        # Check for Kubernetes-specific issues if applicable
        if "apiVersion" in code and "kind" in code:
            k8s_issues = await self._validate_kubernetes_yaml(code)
            issues.extend(k8s_issues)
            
        return issues
        
    async def _validate_json_code(self, code: str, context: str) -> List[ValidationIssue]:
        """Validate JSON syntax."""
        issues = []
        
        try:
            json.loads(code)
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                dimension=QualityDimension.TECHNICAL_ACCURACY,
                severity=SeverityLevel.CRITICAL,
                title="JSON Syntax Error",
                description=f"JSON parsing error: {str(e)}",
                location={"type": "code", "language": "json", "line": e.lineno, "column": e.colno},
                suggested_fix=f"Fix JSON syntax at line {e.lineno}, column {e.colno}",
                auto_fixable=False
            ))
            
        return issues
        
    async def _validate_shell_code(self, code: str, context: str) -> List[ValidationIssue]:
        """Validate shell/bash commands."""
        issues = []
        
        # Check for dangerous commands
        dangerous_patterns = [
            (r'rm\s+-rf\s+/', "Dangerous rm -rf command on root directory"),
            (r'chmod\s+777', "Avoid chmod 777 - use more restrictive permissions"),
            (r'curl.*\|\s*bash', "Avoid piping curl directly to bash for security"),
            (r'wget.*\|\s*sh', "Avoid piping wget directly to shell for security"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    title="Dangerous Shell Command",
                    description=message,
                    location={"type": "code", "language": "bash"},
                    suggested_fix=message,
                    auto_fixable=False
                ))
                
        return issues
        
    async def _validate_generic_code(self, code: str, language: str, context: str) -> List[ValidationIssue]:
        """Use LLM to validate code in any language."""
        issues = []
        
        try:
            # Use LLM for validation
            prompt = f"""
            Validate the following {language} code for:
            1. Syntax errors
            2. Best practice violations
            3. Security issues
            4. Deprecated features
            
            Code:
            ```{language}
            {code}
            ```
            
            Context: {context}
            
            Return a JSON array of issues found, each with:
            - severity: "critical", "high", "medium", or "low"
            - title: Brief title
            - description: Detailed description
            - suggested_fix: How to fix it
            """
            
            response = await self.llm.generate([MultimodalMessage(text=prompt)])
            response_text = response.text
            
            # Parse LLM response
            try:
                llm_issues = json.loads(response_text)
                for issue in llm_issues:
                    issues.append(ValidationIssue(
                        dimension=QualityDimension.TECHNICAL_ACCURACY,
                        severity=SeverityLevel(issue["severity"]),
                        title=issue["title"],
                        description=issue["description"],
                        location={"type": "code", "language": language},
                        suggested_fix=issue.get("suggested_fix"),
                        auto_fixable=False
                    ))
            except:
                logger.warning(f"Failed to parse LLM validation response for {language} code")
                
        except Exception as e:
            logger.error(f"Error validating {language} code with LLM: {e}")
            
        return issues
        
    async def _validate_commands(self, commands: List[str]) -> List[ValidationIssue]:
        """Validate shell commands and CLI usage."""
        issues = []
        
        for command in commands:
            # Check if command exists (simplified)
            base_command = command.split()[0].strip("$")
            
            # Check for typos in common commands
            common_commands = ["ls", "cd", "pwd", "mkdir", "rm", "cp", "mv", "cat", "grep", "find", "docker", "kubectl", "git", "npm", "pip", "python", "java", "node"]
            if base_command not in common_commands and self._is_likely_typo(base_command, common_commands):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    title="Possible Command Typo",
                    description=f"'{base_command}' might be a typo",
                    location={"type": "command", "command": command},
                    suggested_fix=f"Did you mean one of: {', '.join(self._find_similar_commands(base_command, common_commands))}?",
                    auto_fixable=False
                ))
                
        return issues
        
    async def _validate_technical_facts(
        self,
        facts: List[str],
        context: Optional[str] = None
    ) -> List[ValidationIssue]:
        """Validate technical facts and statements."""
        issues = []
        
        for fact in facts:
            # Use LLM to verify technical facts
            try:
                prompt = f"""
                Verify the technical accuracy of this statement:
                "{fact}"
                
                Context: {context or 'General technical content'}
                
                Is this statement:
                1. Technically accurate?
                2. Up-to-date?
                3. Complete (not missing important context)?
                
                If there are any issues, provide:
                - What's incorrect or outdated
                - The correct information
                - Severity of the issue
                
                Format response as JSON.
                """
                
                response = await self.llm.generate([MultimodalMessage(text=prompt)])
                response_text = response.text
                
                # Parse response and create issues if needed
                try:
                    validation = json.loads(response_text)
                    if not validation.get("accurate", True):
                        issues.append(ValidationIssue(
                            dimension=QualityDimension.TECHNICAL_ACCURACY,
                            severity=SeverityLevel(validation.get("severity", "medium")),
                            title="Inaccurate Technical Statement",
                            description=validation.get("issue", "Statement may be inaccurate"),
                            location={"type": "fact", "statement": fact},
                            suggested_fix=validation.get("correction", "Verify and correct this statement"),
                            auto_fixable=False
                        ))
                except:
                    logger.warning(f"Failed to parse fact validation response")
                    
            except Exception as e:
                logger.error(f"Error validating technical fact: {e}")
                
        return issues
        
    async def _validate_configurations(self, configs: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Validate configuration files and settings."""
        issues = []
        
        for config in configs:
            # Validate based on configuration type
            if config.get("type") == "kubernetes":
                issues.extend(await self._validate_kubernetes_config(config))
            elif config.get("type") == "docker":
                issues.extend(await self._validate_docker_config(config))
            elif config.get("type") == "aws":
                issues.extend(await self._validate_aws_config(config))
            # Add more configuration types as needed
                
        return issues
        
    async def _validate_kubernetes_yaml(self, yaml_content: str) -> List[ValidationIssue]:
        """Validate Kubernetes YAML configuration."""
        issues = []
        
        try:
            import yaml
            k8s_obj = yaml.safe_load(yaml_content)
            
            # Check API version
            api_version = k8s_obj.get("apiVersion", "")
            if api_version in ["extensions/v1beta1", "apps/v1beta1", "apps/v1beta2"]:
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.HIGH,
                    title="Deprecated Kubernetes API Version",
                    description=f"API version '{api_version}' is deprecated",
                    location={"type": "kubernetes", "field": "apiVersion"},
                    suggested_fix="Use 'apps/v1' for Deployments, StatefulSets, and DaemonSets",
                    auto_fixable=True
                ))
                
            # Check for required fields
            kind = k8s_obj.get("kind", "")
            if kind == "Deployment":
                if not k8s_obj.get("spec", {}).get("selector"):
                    issues.append(ValidationIssue(
                        dimension=QualityDimension.TECHNICAL_ACCURACY,
                        severity=SeverityLevel.CRITICAL,
                        title="Missing Required Field",
                        description="Deployment must have spec.selector",
                        location={"type": "kubernetes", "kind": "Deployment"},
                        suggested_fix="Add spec.selector.matchLabels",
                        auto_fixable=False
                    ))
                    
        except Exception as e:
            logger.error(f"Error validating Kubernetes YAML: {e}")
            
        return issues
        
    async def _check_deprecations(self, elements: Dict[str, List[Any]]) -> List[ValidationIssue]:
        """Check for deprecated features across all technologies."""
        issues = []
        
        # Check each technology for deprecations
        for tech, info in self.known_technologies.items():
            deprecated = info.get("deprecated", [])
            
            # Search for deprecated features in all elements
            all_text = str(elements)  # Simple approach - could be improved
            
            for dep_feature in deprecated:
                if dep_feature.lower() in all_text.lower():
                    issues.append(ValidationIssue(
                        dimension=QualityDimension.TECHNICAL_ACCURACY,
                        severity=SeverityLevel.HIGH,
                        title=f"Deprecated {tech.upper()} Feature",
                        description=f"'{dep_feature}' is deprecated in {tech}",
                        location={"type": "deprecation", "technology": tech},
                        suggested_fix=f"Update to use current {tech} features",
                        auto_fixable=False
                    ))
                    
        return issues
        
    async def _check_best_practices(self, elements: Dict[str, List[Any]]) -> List[ValidationIssue]:
        """Check if content follows best practices."""
        issues = []
        
        # Check security best practices
        all_code = "\n".join([
            block["code"] for block in elements.get("code_blocks", [])
            if isinstance(block, dict) and "code" in block
        ])
        
        # Check for hardcoded credentials
        credential_patterns = [
            (r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'(api_key|apikey)\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
            (r'(secret|token)\s*=\s*["\'][^"\']+["\']', "Hardcoded secret/token detected"),
        ]
        
        for pattern, message in credential_patterns:
            if re.search(pattern, all_code, re.IGNORECASE):
                issues.append(ValidationIssue(
                    dimension=QualityDimension.TECHNICAL_ACCURACY,
                    severity=SeverityLevel.CRITICAL,
                    title="Security Best Practice Violation",
                    description=message,
                    location={"type": "security", "pattern": "credential"},
                    suggested_fix="Use environment variables or secure credential management",
                    auto_fixable=False
                ))
                
        return issues
        
    async def _gather_reference_sources(
        self,
        elements: Dict[str, List[Any]],
        context: Optional[str] = None
    ) -> List[str]:
        """Gather reference sources used for validation."""
        sources = [
            "Internal technology database",
            "Best practices knowledge base",
        ]
        
        # Add technology-specific sources
        if any("aws" in str(elem).lower() for elem in elements.values()):
            sources.append("AWS Documentation (https://docs.aws.amazon.com)")
            
        if any("kubernetes" in str(elem).lower() for elem in elements.values()):
            sources.append("Kubernetes Documentation (https://kubernetes.io/docs)")
            
        if any("python" in str(elem).lower() for elem in elements.values()):
            sources.append("Python Documentation (https://docs.python.org)")
            
        return sources
        
    def _is_likely_typo(self, word: str, valid_words: List[str]) -> bool:
        """Check if a word is likely a typo of valid words."""
        for valid in valid_words:
            if self._edit_distance(word, valid) <= 2:
                return True
        return False
        
    def _find_similar_commands(self, word: str, valid_words: List[str]) -> List[str]:
        """Find similar valid commands."""
        similar = []
        for valid in valid_words:
            if self._edit_distance(word, valid) <= 2:
                similar.append(valid)
        return similar[:3]  # Return top 3
        
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
        
    async def _validate_kubernetes_config(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Kubernetes-specific configuration."""
        # Implement Kubernetes-specific validation
        return []
        
    async def _validate_docker_config(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate Docker-specific configuration."""
        # Implement Docker-specific validation
        return []
        
    async def _validate_aws_config(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate AWS-specific configuration."""
        # Implement AWS-specific validation
        return []
