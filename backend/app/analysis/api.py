"""
FastAPI endpoints for code analysis.

Provides REST API interface to LocalAnalyzer:
- POST /api/analysis/files - Analyze single file
- POST /api/analysis/directories - Analyze directory
- GET /api/analysis/metrics - Get cached metrics
- POST /api/analysis/report - Generate compliance report
- GET /api/analysis/status - Check analysis status
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, File, UploadFile, BackgroundTasks
from pydantic import BaseModel, Field

from backend.app.analysis import LocalAnalyzer, create_analyzer
from backend.app.analysis.interfaces import SeverityLevel, AnalysisResult, Violation


# ============================================================================
# Request/Response Models
# ============================================================================

class ViolationResponse(BaseModel):
    """Violation response model"""
    rule_id: str
    message: str
    file_path: str
    line_number: int
    severity: str
    fix_suggestion: Optional[str] = None

    class Config:
        from_attributes = True


class ComplexityMetricsResponse(BaseModel):
    """Complexity metrics response"""
    cyclomatic_complexity: float
    cognitive_complexity: float
    lines_of_code: int
    logical_lines: int
    functions: int
    classes: int
    max_function_complexity: float
    maintainability_index: float

    class Config:
        from_attributes = True


class CoverageMetricsResponse(BaseModel):
    """Coverage metrics response"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    lines_covered: int
    lines_total: int
    branches_covered: int
    branches_total: int
    missing_lines: List[int] = []
    missing_branches: List[str] = []

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    """Request to analyze a file or directory"""
    path: str = Field(..., description="File or directory path to analyze")
    recursive: bool = Field(True, description="For directories: analyze recursively")
    analyzer_type: str = Field("local", description="Analyzer type: 'local', 'ldra', or 'mock'")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "backend/app/main.py",
                "recursive": True,
                "analyzer_type": "local"
            }
        }


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint"""
    analyzer: str
    file: str
    timestamp: str
    violation_count: int
    critical_count: int
    high_count: int
    violations: List[ViolationResponse]
    complexity: Optional[ComplexityMetricsResponse] = None
    coverage: Optional[CoverageMetricsResponse] = None
    warnings: List[str] = []
    errors: List[str] = []
    metadata: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "analyzer": "local",
                "file": "backend/app/main.py",
                "timestamp": "2025-11-19T15:00:00",
                "violation_count": 5,
                "critical_count": 0,
                "high_count": 2,
                "violations": [],
                "complexity": {
                    "cyclomatic_complexity": 3.0,
                    "cognitive_complexity": 0.0,
                    "lines_of_code": 134,
                    "logical_lines": 93,
                    "functions": 6,
                    "classes": 0,
                    "max_function_complexity": 3.0,
                    "maintainability_index": 83.66
                },
                "coverage": {
                    "line_coverage": 0.95,
                    "branch_coverage": 0.90,
                    "function_coverage": 1.0,
                    "lines_covered": 127,
                    "lines_total": 134,
                    "branches_covered": 18,
                    "branches_total": 20
                }
            }
        }


class MetricsRequest(BaseModel):
    """Request for metrics calculation"""
    path: str = Field(..., description="File path for metrics")
    analyzer_type: str = Field("local", description="Analyzer type")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "backend/app/main.py",
                "analyzer_type": "local"
            }
        }


class MetricsResponse(BaseModel):
    """Complexity metrics response"""
    file: str
    timestamp: str
    complexity: ComplexityMetricsResponse
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    """Request to generate compliance report"""
    path: str = Field(..., description="File or directory to analyze")
    output_format: str = Field("text", description="Output format: 'text', 'json', 'html'")
    include_violations: bool = Field(True, description="Include violations in report")
    include_metrics: bool = Field(True, description="Include metrics in report")
    analyzer_type: str = Field("local", description="Analyzer type")

    class Config:
        json_schema_extra = {
            "example": {
                "path": "backend/app",
                "output_format": "text",
                "include_violations": True,
                "include_metrics": True,
                "analyzer_type": "local"
            }
        }


class ReportResponse(BaseModel):
    """Compliance report response"""
    file: str
    timestamp: str
    format: str
    report: str
    metadata: Dict[str, Any] = {}


class StatusResponse(BaseModel):
    """Analysis status response"""
    status: str = Field(..., description="Status: 'ready', 'analyzing', 'error'")
    timestamp: str
    message: str
    supported_analyzers: List[str]
    available_tools: List[str]


# ============================================================================
# Analysis API Router
# ============================================================================

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
    responses={404: {"description": "Not found"}},
)


def _convert_analysis_result(result: AnalysisResult) -> AnalysisResponse:
    """Convert AnalysisResult to AnalysisResponse"""
    violations = []
    if result.violations:
        violations = [
            ViolationResponse(
                rule_id=v.rule_id,
                message=v.message,
                file_path=v.file_path,
                line_number=v.line_number,
                severity=v.severity.name,
                fix_suggestion=v.fix_suggestion,
            )
            for v in result.violations
        ]

    complexity = None
    if result.complexity:
        complexity = ComplexityMetricsResponse(
            cyclomatic_complexity=result.complexity.cyclomatic_complexity,
            cognitive_complexity=result.complexity.cognitive_complexity,
            lines_of_code=result.complexity.lines_of_code,
            logical_lines=result.complexity.logical_lines,
            functions=result.complexity.functions,
            classes=result.complexity.classes,
            max_function_complexity=result.complexity.max_function_complexity,
            maintainability_index=result.complexity.maintainability_index,
        )

    coverage = None
    if result.coverage:
        coverage = CoverageMetricsResponse(
            line_coverage=result.coverage.line_coverage,
            branch_coverage=result.coverage.branch_coverage,
            function_coverage=result.coverage.function_coverage,
            lines_covered=result.coverage.lines_covered,
            lines_total=result.coverage.lines_total,
            branches_covered=result.coverage.branches_covered,
            branches_total=result.coverage.branches_total,
            missing_lines=result.coverage.missing_lines,
            missing_branches=result.coverage.missing_branches,
        )

    return AnalysisResponse(
        analyzer=result.analyzer_name,
        file=str(result.file_path),
        timestamp=result.timestamp,
        violation_count=result.violation_count,
        critical_count=result.critical_count,
        high_count=result.high_count,
        violations=violations,
        complexity=complexity,
        coverage=coverage,
        warnings=result.warnings,
        errors=result.errors,
        metadata=result.metadata,
    )


@router.post(
    "/files",
    response_model=AnalysisResponse,
    summary="Analyze a single file",
    description="Analyze a single Python file for violations, metrics, and compliance issues.",
)
async def analyze_file(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a single Python file.

    **Parameters:**
    - `path`: File path to analyze (relative or absolute)
    - `analyzer_type`: Type of analyzer ('local', 'ldra', 'mock')

    **Returns:**
    - Violations found
    - Complexity metrics
    - Coverage information
    - Compliance warnings/errors

    **Example:**
    ```json
    {
        "path": "backend/app/main.py",
        "analyzer_type": "local"
    }
    ```
    """
    try:
        analyzer = create_analyzer(request.analyzer_type)
        result = analyzer.analyze_file(request.path)
        return _convert_analysis_result(result)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.path}"
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid file request"
        )
    except Exception as analysis_error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(analysis_error)}"
        )


@router.post(
    "/directories",
    response_model=AnalysisResponse,
    summary="Analyze a directory",
    description="Analyze all Python files in a directory (recursively or non-recursively).",
)
async def analyze_directory(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze all Python files in a directory.

    **Parameters:**
    - `path`: Directory path to analyze
    - `recursive`: Recursively analyze subdirectories (default: true)
    - `analyzer_type`: Type of analyzer ('local', 'ldra', 'mock')

    **Returns:**
    - Aggregated violations from all files
    - Combined metrics
    - Compliance report

    **Example:**
    ```json
    {
        "path": "backend/app",
        "recursive": true,
        "analyzer_type": "local"
    }
    ```
    """
    try:
        analyzer = create_analyzer(request.analyzer_type)
        result = analyzer.analyze_directory(request.path, recursive=request.recursive)
        return _convert_analysis_result(result)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Directory not found: {request.path}"
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid directory request"
        )
    except Exception as analysis_error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(analysis_error)}"
        )


@router.post(
    "/metrics",
    response_model=MetricsResponse,
    summary="Calculate complexity metrics",
    description="Calculate complexity metrics for a Python file.",
)
async def get_metrics(request: MetricsRequest) -> MetricsResponse:
    """
    Calculate complexity metrics for a file.

    **Parameters:**
    - `path`: File path to analyze
    - `analyzer_type`: Type of analyzer

    **Returns:**
    - Cyclomatic complexity
    - Cognitive complexity
    - Lines of code
    - Function and class counts
    - Maintainability index

    **Example:**
    ```json
    {
        "path": "backend/app/main.py",
        "analyzer_type": "local"
    }
    ```
    """
    try:
        analyzer = create_analyzer(request.analyzer_type)
        metrics = analyzer.get_complexity_metrics(request.path)
        return MetricsResponse(
            file=request.path,
            timestamp=datetime.utcnow().isoformat(),
            complexity=ComplexityMetricsResponse(
                cyclomatic_complexity=metrics.cyclomatic_complexity,
                cognitive_complexity=metrics.cognitive_complexity,
                lines_of_code=metrics.lines_of_code,
                logical_lines=metrics.logical_lines,
                functions=metrics.functions,
                classes=metrics.classes,
                max_function_complexity=metrics.max_function_complexity,
                maintainability_index=metrics.maintainability_index,
            ),
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.path}"
        )
    except Exception as analysis_error:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(analysis_error)}"
        )


@router.post(
    "/report",
    response_model=ReportResponse,
    summary="Generate compliance report",
    description="Generate formatted compliance report for audit and documentation.",
)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """
    Generate compliance report.

    **Parameters:**
    - `path`: File or directory to analyze
    - `output_format`: Format ('text', 'json', 'html')
    - `include_violations`: Include violations in report
    - `include_metrics`: Include metrics in report
    - `analyzer_type`: Type of analyzer

    **Returns:**
    - Formatted compliance report
    - Suitable for FDA/ISO documentation

    **Example:**
    ```json
    {
        "path": "backend/app",
        "output_format": "text",
        "include_violations": true,
        "include_metrics": true,
        "analyzer_type": "local"
    }
    ```
    """
    try:
        analyzer = create_analyzer(request.analyzer_type)

        # Analyze first
        if Path(request.path).is_dir():
            result = analyzer.analyze_directory(request.path, recursive=True)
        else:
            result = analyzer.analyze_file(request.path)

        # Generate report
        report = analyzer.generate_compliance_report(output_format=request.output_format)

        return ReportResponse(
            file=request.path,
            timestamp=datetime.utcnow().isoformat(),
            format=request.output_format,
            report=report or f"Analysis completed: {result.violation_count} violations found",
            metadata={
                "violations": result.violation_count,
                "critical": result.critical_count,
                "high": result.high_count,
                "analyzer": result.analyzer_name,
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Check analysis service status",
    description="Get status of analysis service and available analyzers.",
)
async def get_status() -> StatusResponse:
    """
    Get analysis service status.

    **Returns:**
    - Service status
    - Available analyzers
    - Available analysis tools

    **Example Response:**
    ```json
    {
        "status": "ready",
        "timestamp": "2025-11-19T15:00:00",
        "message": "Analysis service is operational",
        "supported_analyzers": ["local", "ldra", "mock"],
        "available_tools": ["flake8", "bandit", "ast", "pytest-cov"]
    }
    ```
    """
    return StatusResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat(),
        message="Analysis service is operational",
        supported_analyzers=["local", "ldra", "mock"],
        available_tools=["flake8", "bandit", "ast", "pytest-cov"],
    )


@router.get(
    "/health",
    summary="Health check",
    description="Simple health check endpoint.",
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Additional utility endpoints
# ============================================================================

@router.post(
    "/batch",
    summary="Analyze multiple files",
    description="Analyze multiple files in a batch request.",
)
async def analyze_batch(
    paths: List[str] = Query(..., description="List of file paths to analyze"),
    analyzer_type: str = Query("local", description="Analyzer type"),
) -> List[AnalysisResponse]:
    """
    Analyze multiple files in batch.

    **Parameters:**
    - `paths`: List of file paths
    - `analyzer_type`: Analyzer type

    **Returns:**
    - List of analysis results
    """
    try:
        analyzer = create_analyzer(analyzer_type)
        results = []

        for path in paths:
            try:
                result = analyzer.analyze_file(path)
                results.append(_convert_analysis_result(result))
            except Exception as e:
                results.append(
                    AnalysisResponse(
                        analyzer=analyzer_type,
                        file=path,
                        timestamp=datetime.utcnow().isoformat(),
                        violation_count=0,
                        critical_count=0,
                        high_count=0,
                        violations=[],
                        errors=[f"Analysis failed: {str(e)}"],
                    )
                )

        return results
    except Exception as batch_error:
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(batch_error)}"
        )


# ============================================================================
# Export router for integration with main app
# ============================================================================

__all__ = ["router"]
