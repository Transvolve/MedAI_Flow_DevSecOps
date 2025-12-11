"""
Abstract interfaces for analysis plugins

Defines the contracts that all analyzer implementations must fulfill.
This enables clean architecture and easy plugin swapping.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum


class SeverityLevel(Enum):
    """Violation severity levels"""
    CRITICAL = "critical"      # Safety-critical violations
    HIGH = "high"              # Major issues
    MEDIUM = "medium"          # Moderate issues
    LOW = "low"                # Minor issues
    INFO = "info"              # Informational only


@dataclass
class Violation:
    """Represents a single code violation"""
    rule_id: str                           # e.g., "E501", "S101"
    message: str                           # Human-readable message
    file_path: str                         # File containing violation
    line_number: int                       # Line number
    column: int = 0                        # Column number (if available)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    rule_name: str = ""                    # e.g., "line-too-long"
    fix_suggestion: str = ""               # Optional fix suggestion
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "message": self.message,
            "file": self.file_path,
            "line": self.line_number,
            "column": self.column,
            "severity": self.severity.value,
            "fix_suggestion": self.fix_suggestion,
            "metadata": self.metadata,
        }


@dataclass
class ComplexityMetrics:
    """Code complexity measurements"""
    cyclomatic_complexity: float = 0.0      # Cyclomatic complexity
    cognitive_complexity: float = 0.0       # Cognitive complexity
    lines_of_code: int = 0                  # Total lines
    logical_lines: int = 0                  # Non-blank, non-comment lines
    functions: int = 0                      # Function count
    classes: int = 0                        # Class count
    max_function_complexity: float = 0.0    # Highest function complexity
    maintainability_index: float = 0.0      # 0-100 score (higher is better)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "lines_of_code": self.lines_of_code,
            "logical_lines": self.logical_lines,
            "functions": self.functions,
            "classes": self.classes,
            "max_function_complexity": self.max_function_complexity,
            "maintainability_index": self.maintainability_index,
            "metadata": self.metadata,
        }


@dataclass
class CoverageMetrics:
    """Test coverage measurements"""
    line_coverage: float = 0.0              # 0.0-1.0 (0-100%)
    branch_coverage: float = 0.0            # 0.0-1.0
    function_coverage: float = 0.0          # 0.0-1.0
    lines_covered: int = 0                  # Number of covered lines
    lines_total: int = 0                    # Total lines
    branches_covered: int = 0               # Covered branches
    branches_total: int = 0                 # Total branches
    missing_lines: List[int] = field(default_factory=list)  # Uncovered line numbers
    missing_branches: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_coverage": self.line_coverage,
            "branch_coverage": self.branch_coverage,
            "function_coverage": self.function_coverage,
            "lines_covered": self.lines_covered,
            "lines_total": self.lines_total,
            "branches_covered": self.branches_covered,
            "branches_total": self.branches_total,
            "missing_lines": self.missing_lines,
            "missing_branches": self.missing_branches,
            "metadata": self.metadata,
        }


@dataclass
class AnalysisResult:
    """Unified result from any analyzer"""
    violations: List[Violation] = field(default_factory=list)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    analyzer_name: str = "unknown"          # Which analyzer produced this
    file_path: str = ""                     # File or directory analyzed
    timestamp: str = ""                     # When analysis ran
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "analyzer": self.analyzer_name,
            "file": self.file_path,
            "timestamp": self.timestamp,
            "violations": [v.to_dict() for v in self.violations],
            "complexity": self.complexity.to_dict(),
            "coverage": self.coverage.to_dict(),
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @property
    def violation_count(self) -> int:
        """Total violations"""
        return len(self.violations)

    @property
    def critical_count(self) -> int:
        """Number of critical violations"""
        return sum(1 for v in self.violations if v.severity == SeverityLevel.CRITICAL)

    @property
    def high_count(self) -> int:
        """Number of high severity violations"""
        return sum(1 for v in self.violations if v.severity == SeverityLevel.HIGH)


class CodeAnalyzer(ABC):
    """
    Abstract base class for code analyzers.
    
    Implementations:
    - LocalAnalyzer: Uses flake8, bandit, pytest coverage (no external dependencies)
    - LDRAAdapter: Uses LDRA Test Master (when licensed)
    - MockAnalyzer: For testing
    """

    @abstractmethod
    def analyze_file(self, filepath: str) -> AnalysisResult:
        """
        Analyze a single file for violations and metrics.

        Args:
            filepath: Absolute path to Python file

        Returns:
            AnalysisResult with violations, metrics, coverage

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not Python
        """
        pass

    @abstractmethod
    def analyze_directory(self, dirpath: str, recursive: bool = True) -> AnalysisResult:
        """
        Analyze entire directory.

        Args:
            dirpath: Directory path
            recursive: Include subdirectories

        Returns:
            Aggregated AnalysisResult

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        pass

    @abstractmethod
    def get_coverage_report(self, source_path: str = ".") -> CoverageMetrics:
        """
        Get current test coverage metrics.

        Args:
            source_path: Path to analyze coverage for

        Returns:
            CoverageMetrics with line, branch, function coverage
        """
        pass

    @abstractmethod
    def get_complexity_metrics(self, filepath: str) -> ComplexityMetrics:
        """
        Calculate code complexity metrics.

        Args:
            filepath: File to analyze

        Returns:
            ComplexityMetrics with cyclomatic, cognitive, etc.
        """
        pass

    @abstractmethod
    def generate_compliance_report(self, output_format: str = "json") -> str:
        """
        Generate regulatory compliance report.

        Args:
            output_format: "json", "xml", "pdf", "html"

        Returns:
            Report content as string

        Compliance standards covered:
        - FDA 21 CFR 11
        - IEC 62304 (medical device lifecycle)
        - IEC 61508 (safety-critical systems)
        - ISO 13485 (medical device quality)
        - ISO 27001 (information security)
        """
        pass


class TestAutomator(ABC):
    """
    Abstract base class for test generation.
    
    Implementations:
    - LDRAAdapter: Generates tests from code (when LDRA licensed)
    - LocalAutomator: Generates test stubs
    - MockAutomator: For testing
    """

    @abstractmethod
    def generate_unit_tests(self, filepath: str) -> List[str]:
        """
        Generate unit test cases for a file.

        Args:
            filepath: Python file to generate tests for

        Returns:
            List of test code strings (one per function/class)

        Use case:
        - LDRA: Generates comprehensive test cases
        - Local: Generates test stubs with TODOs
        """
        pass

    @abstractmethod
    def generate_coverage_tests(
        self,
        filepath: str,
        target_coverage: float = 0.95,
    ) -> List[str]:
        """
        Generate tests targeting specific coverage levels.

        Args:
            filepath: File to target
            target_coverage: Target coverage percentage (0.0-1.0)

        Returns:
            List of test code strings

        Use case:
        - LDRA: Generates tests for exact coverage requirements
        - Local: Analyzes gaps and suggests test cases
        """
        pass


class TraceabilityMapper(ABC):
    """
    Abstract base class for requirements traceability.
    
    Implementations:
    - LDRAAdapter: Full traceability matrix from LDRA
    - LocalMapper: Manual/automated mapping
    - MockMapper: For testing
    """

    @abstractmethod
    def map_requirement_to_code(self, requirement_id: str) -> List[str]:
        """
        Map requirement ID to implementing code files/functions.

        Args:
            requirement_id: Requirement identifier (e.g., "REQ-001")

        Returns:
            List of code locations implementing requirement

        Example output:
        [
            "backend/app/auth.py::authenticate_user",
            "backend/app/auth.py::verify_jwt_token",
        ]
        """
        pass

    @abstractmethod
    def generate_traceability_matrix(self) -> Dict[str, List[str]]:
        """
        Generate complete requirements-to-code traceability matrix.

        Returns:
            Dict mapping requirements to code locations

        Example:
        {
            "REQ-001": ["backend/app/auth.py::authenticate"],
            "REQ-002": ["backend/app/auth.py::verify_jwt", "tests/test_jwt.py"],
            ...
        }

        Regulatory value:
        - FDA submission requirement
        - IEC 62304 requirement
        - Audit trail
        """
        pass

    @abstractmethod
    def generate_impact_analysis(self, code_change: str) -> Dict[str, List[str]]:
        """
        Analyze impact of code change on requirements.

        Args:
            code_change: Code file/function that changed

        Returns:
            Dict of affected requirements and tests

        Use case:
        - Risk assessment
        - Change control
        - Regression testing
        """
        pass
