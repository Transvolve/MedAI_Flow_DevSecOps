"""
Analysis module for code quality, coverage, and compliance

This module provides a clean architecture for integrating various analysis tools:
- Static analysis (flake8, bandit, custom)
- Test automation (pytest, LDRA-generated)
- Traceability mapping
- Compliance reporting

Supports:
- LocalAnalyzer: Built-in using existing tools (no external dependencies)
- LDRAAdapter: Industrial-grade analysis (when LDRA licensed)
- MockAnalyzer: Testing and mocking

Usage:
    from backend.app.analysis import get_available_analyzer

    analyzer = get_available_analyzer(preferred="local")  # or "ldra"
    result = analyzer.analyze_file("backend/app/main.py")
    print(result)
"""

from .interfaces import (
    CodeAnalyzer,
    TestAutomator,
    TraceabilityMapper,
    AnalysisResult,
)
from .factory import AnalyzerFactory, get_available_analyzer, create_analyzer
from .local_analyzer import LocalAnalyzer

__all__ = [
    "CodeAnalyzer",
    "TestAutomator",
    "TraceabilityMapper",
    "AnalysisResult",
    "AnalyzerFactory",
    "get_available_analyzer",
    "create_analyzer",
    "LocalAnalyzer",
]
