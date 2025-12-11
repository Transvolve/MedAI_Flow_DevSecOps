"""
Mock analyzer for testing and development.

Use this when:
- Writing unit tests
- Mocking external dependencies
- Testing without flake8/bandit installed
- Development/demo mode

Always returns predictable, controlled results.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from .interfaces import (
    CodeAnalyzer,
    AnalysisResult,
    Violation,
    ComplexityMetrics,
    CoverageMetrics,
    SeverityLevel,
)


class MockAnalyzer(CodeAnalyzer):
    """Mock analyzer for testing"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize mock analyzer"""
        self.config = config or {}
        self.call_count = 0

    def analyze_file(self, filepath: str) -> AnalysisResult:
        """Return mock analysis result"""
        self.call_count += 1

        # Mock violations
        violations = [
            Violation(
                rule_id="E501",
                rule_name="line-too-long",
                message="line too long (120 > 79 characters)",
                file_path=filepath,
                line_number=42,
                severity=SeverityLevel.MEDIUM,
            ),
            Violation(
                rule_id="F841",
                rule_name="local-variable-assigned-but-never-used",
                message="local variable 'x' is assigned to but never used",
                file_path=filepath,
                line_number=15,
                severity=SeverityLevel.LOW,
            ),
        ]

        complexity = ComplexityMetrics(
            cyclomatic_complexity=5.0,
            lines_of_code=250,
            functions=8,
            classes=2,
            maintainability_index=75.0,
        )

        return AnalysisResult(
            violations=violations,
            complexity=complexity,
            analyzer_name="mock",
            file_path=filepath,
            timestamp=datetime.now().isoformat(),
            metadata={"mock": True, "call_count": self.call_count},
        )

    def analyze_directory(self, dirpath: str, recursive: bool = True) -> AnalysisResult:
        """Return mock directory analysis"""
        result = self.analyze_file(dirpath)
        result.metadata["is_directory"] = True
        return result

    def get_coverage_report(self, source_path: str = ".") -> CoverageMetrics:
        """Return mock coverage"""
        return CoverageMetrics(
            line_coverage=0.92,
            branch_coverage=0.85,
            lines_covered=450,
            lines_total=490,
        )

    def get_complexity_metrics(self, filepath: str) -> ComplexityMetrics:
        """Return mock complexity"""
        return ComplexityMetrics(
            cyclomatic_complexity=6.0,
            lines_of_code=300,
            functions=10,
            classes=3,
            maintainability_index=70.0,
        )

    def generate_compliance_report(self, output_format: str = "json") -> str:
        """Return mock compliance report"""
        return """{
  "status": "compliant",
  "standards": ["FDA_21CFR11", "IEC62304", "ISO27001"],
  "ready_for_submission": true
}"""
