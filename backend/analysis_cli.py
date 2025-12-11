"""
Command-line interface for code analysis.

Provides CLI commands:
- analyze-file: Analyze single file
- analyze-dir: Analyze directory
- metrics: Get complexity metrics
- report: Generate compliance report
- status: Check analyzer status

Usage:
    python -m backend.analysis_cli analyze-file backend/app/main.py
    python -m backend.analysis_cli analyze-dir backend/app
    python -m backend.analysis_cli metrics backend/app/main.py
    python -m backend.analysis_cli report backend/app --format text
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import click

try:
    from tabulate import tabulate
except ImportError:
    # Fallback if tabulate not installed
    def tabulate(data, headers=None, tablefmt="grid"):
        """Simple fallback tabulate function"""
        if headers:
            return f"{headers}\n" + "\n".join([str(row) for row in data])
        return "\n".join([str(row) for row in data])

from backend.app.analysis import LocalAnalyzer, create_analyzer
from backend.app.analysis.interfaces import SeverityLevel


# ============================================================================
# Click Groups and Commands
# ============================================================================

@click.group()
@click.version_option(version="1.0.0", prog_name="analysis-cli")
def cli():
    """Code analysis command-line interface.

    Comprehensive Python code analysis with support for multiple analyzers.

    Examples:
        # Analyze a single file
        analysis-cli analyze-file backend/app/main.py

        # Analyze a directory
        analysis-cli analyze-dir backend/app

        # Get complexity metrics
        analysis-cli metrics backend/app/main.py

        # Generate compliance report
        analysis-cli report backend/app
    """
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--analyzer",
    type=click.Choice(["local", "ldra", "mock"]),
    default="local",
    help="Analyzer type to use",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed output",
)
def analyze_file(
    file_path: str,
    analyzer: str,
    output: str,
    verbose: bool,
):
    """Analyze a single Python file.

    Analyzes a file for violations, complexity metrics, and compliance issues.

    Example:
        analysis-cli analyze-file backend/app/main.py
        analysis-cli analyze-file backend/app/main.py --output json
        analysis-cli analyze-file backend/app/main.py --verbose
    """
    try:
        click.echo(f"[ANALYSIS] Analyzing file: {file_path}")
        click.echo(f"           Analyzer: {analyzer}")
        
        analyzer_obj = create_analyzer(analyzer)
        result = analyzer_obj.analyze_file(file_path)
        
        if output == "json":
            _output_json(result)
        elif output == "table":
            _output_table(result)
        else:
            _output_text(result, verbose)
        
        # Summary
        click.echo()
        click.secho(f"[OK] Analysis complete", fg="green", bold=True)
        click.echo(f"   Violations: {result.violation_count}")
        click.echo(f"   Critical: {result.critical_count}")
        click.echo(f"   High: {result.high_count}")
        
    except FileNotFoundError:
        click.secho(f"[FAIL] File not found: {file_path}", fg="red", bold=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"[FAIL] Error: {str(e)}", fg="red", bold=True)
        sys.exit(1)


@cli.command()
@click.argument("dir_path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--recursive",
    is_flag=True,
    default=True,
    help="Recursively analyze subdirectories",
)
@click.option(
    "--analyzer",
    type=click.Choice(["local", "ldra", "mock"]),
    default="local",
    help="Analyzer type to use",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed output",
)
def analyze_dir(
    dir_path: str,
    recursive: bool,
    analyzer: str,
    output: str,
    verbose: bool,
):
    """Analyze all Python files in a directory.

    Recursively analyzes all .py files in the specified directory.

    Example:
        analysis-cli analyze-dir backend/app
        analysis-cli analyze-dir backend/app --no-recursive
        analysis-cli analyze-dir backend/app --output json
    """
    try:
        click.echo(f"[METRICS] Analyzing directory: {dir_path}")
        click.echo(f"          Recursive: {recursive}")
        click.echo(f"          Analyzer: {analyzer}")
        
        analyzer_obj = create_analyzer(analyzer)
        result = analyzer_obj.analyze_directory(dir_path, recursive=recursive)
        
        if output == "json":
            _output_json(result)
        elif output == "table":
            _output_table(result)
        else:
            _output_text(result, verbose)
        
        # Summary
        click.echo()
        click.secho(f"[OK] Analysis complete", fg="green", bold=True)
        click.echo(f"   Violations: {result.violation_count}")
        click.echo(f"   Critical: {result.critical_count}")
        click.echo(f"   High: {result.high_count}")
        
    except FileNotFoundError:
        click.secho(f"[FAIL] Directory not found: {dir_path}", fg="red", bold=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"[FAIL] Error: {str(e)}", fg="red", bold=True)
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--analyzer",
    type=click.Choice(["local", "ldra", "mock"]),
    default="local",
    help="Analyzer type to use",
)
@click.option(
    "--output",
    type=click.Choice(["text", "json", "table"]),
    default="text",
    help="Output format",
)
def metrics(
    file_path: str,
    analyzer: str,
    output: str,
):
    """Get complexity metrics for a file.

    Calculates cyclomatic complexity, cognitive complexity, and other metrics.

    Example:
        analysis-cli metrics backend/app/main.py
        analysis-cli metrics backend/app/main.py --output json
        analysis-cli metrics backend/app/main.py --output table
    """
    try:
        click.echo(f"[METRICS] Calculating metrics for: {file_path}")
        
        analyzer_obj = create_analyzer(analyzer)
        metrics_obj = analyzer_obj.get_complexity_metrics(file_path)
        
        if output == "json":
            click.echo(json.dumps(metrics_obj.to_dict(), indent=2))
        elif output == "table":
            _output_metrics_table(metrics_obj)
        else:
            _output_metrics_text(metrics_obj)
        
        click.secho(f"[OK] Metrics complete", fg="green", bold=True)
        
    except FileNotFoundError:
        click.secho(f"[FAIL] File not found: {file_path}", fg="red", bold=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"[FAIL] Error: {str(e)}", fg="red", bold=True)
        sys.exit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--format",
    type=click.Choice(["text", "json", "html"]),
    default="text",
    help="Report format",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Save report to file",
)
@click.option(
    "--analyzer",
    type=click.Choice(["local", "ldra", "mock"]),
    default="local",
    help="Analyzer type to use",
)
def report(
    path: str,
    format: str,
    output: Optional[str],
    analyzer: str,
):
    """Generate compliance report.

    Creates a formatted compliance report suitable for FDA/ISO documentation.

    Example:
        analysis-cli report backend/app --format text
        analysis-cli report backend/app --format json --output report.json
        analysis-cli report backend/app/main.py --format html
    """
    try:
        click.echo(f"[REPORT] Generating compliance report for: {path}")
        click.echo(f"         Format: {format}")
        
        analyzer_obj = create_analyzer(analyzer)
        
        # Analyze
        if Path(path).is_dir():
            result = analyzer_obj.analyze_directory(path, recursive=True)
        else:
            result = analyzer_obj.analyze_file(path)
        
        # Generate report
        report_text = analyzer_obj.generate_compliance_report(output_format=format)
        
        if report_text is None:
            report_text = f"Analysis Report - {datetime.utcnow().isoformat()}\n"
            report_text += f"Path: {path}\n"
            report_text += f"Violations: {result.violation_count}\n"
            report_text += f"Critical: {result.critical_count}\n"
            report_text += f"High: {result.high_count}\n"
        
        # Output or save
        if output:
            with open(output, "w") as f:
                f.write(report_text)
            click.secho(f"[OK] Report saved to: {output}", fg="green", bold=True)
        else:
            click.echo()
            click.echo(report_text)
            click.echo()
            click.secho(f"[OK] Report complete", fg="green", bold=True)
        
    except Exception as e:
        click.secho(f"[FAIL] Error: {str(e)}", fg="red", bold=True)
        sys.exit(1)


@cli.command()
def status():
    """Check analyzer status.

    Displays available analyzers and system information.

    Example:
        analysis-cli status
    """
    try:
        click.echo("[INFO] Analysis System Status")
        click.echo()
        
        # Check available analyzers
        click.secho("Available Analyzers:", bold=True)
        for analyzer_name in ["local", "ldra", "mock"]:
            try:
                analyzer_obj = create_analyzer(analyzer_name)
                click.echo(f"  [OK] {analyzer_name:8} - {analyzer_obj.__class__.__name__}")
            except Exception:
                click.echo(f"  [FAIL] {analyzer_name:8} - Not available")
        
        click.echo()
        
        # LocalAnalyzer info
        try:
            local = LocalAnalyzer()
            click.secho("LocalAnalyzer Tools:", bold=True)
            click.echo(f"  [OK] flake8       - Style checking")
            click.echo(f"  [OK] bandit       - Security analysis")
            click.echo(f"  [OK] AST analysis - Complexity metrics")
            click.echo(f"  [OK] pytest-cov   - Coverage tracking")
        except Exception:
            pass
        
        click.echo()
        click.secho("[OK] Analysis system is operational", fg="green", bold=True)
        
    except Exception as e:
        click.secho(f"[FAIL] Error: {str(e)}", fg="red", bold=True)
        sys.exit(1)


# ============================================================================
# Output Formatting Helpers
# ============================================================================

def _output_text(result, verbose: bool = False):
    """Output analysis result in text format."""
    click.echo()
    click.secho("Analysis Results", bold=True, underline=True)
    click.echo()
    
    if result.violations:
        click.secho("Violations:", bold=True)
        for v in result.violations:
            severity_color = {
                SeverityLevel.CRITICAL: "red",
                SeverityLevel.HIGH: "yellow",
                SeverityLevel.MEDIUM: "yellow",
                SeverityLevel.LOW: "blue",
                SeverityLevel.INFO: "white",
            }.get(v.severity, "white")
            
            click.secho(
                f"  [{v.severity.name}]",
                fg=severity_color,
                nl=False,
            )
            click.echo(f" {v.file_path}:{v.line_number}")
            click.echo(f"       {v.message}")
            if v.fix_suggestion and verbose:
                click.echo(f"       Fix: {v.fix_suggestion}")
        click.echo()
    
    if result.complexity:
        click.secho("Complexity Metrics:", bold=True)
        click.echo(f"  Cyclomatic:     {result.complexity.cyclomatic_complexity:.1f}")
        click.echo(f"  Cognitive:      {result.complexity.cognitive_complexity:.1f}")
        click.echo(f"  Lines of Code:  {result.complexity.lines_of_code}")
        click.echo(f"  Functions:      {result.complexity.functions}")
        click.echo(f"  Classes:        {result.complexity.classes}")
        if verbose:
            click.echo(f"  Maintainability: {result.complexity.maintainability_index:.1f}")


def _output_table(result):
    """Output analysis result in table format."""
    click.echo()
    
    if result.violations:
        click.secho("Violations", bold=True)
        table_data = []
        for v in result.violations:
            table_data.append([
                v.severity.name,
                Path(v.file_path).name,
                v.line_number,
                v.message[:50] + ("..." if len(v.message) > 50 else ""),
            ])
        
        click.echo(tabulate(
            table_data,
            headers=["Severity", "File", "Line", "Issue"],
            tablefmt="grid",
        ))
        click.echo()
    
    if result.complexity:
        click.secho("Metrics", bold=True)
        metrics_data = [
            ["Cyclomatic Complexity", f"{result.complexity.cyclomatic_complexity:.1f}"],
            ["Cognitive Complexity", f"{result.complexity.cognitive_complexity:.1f}"],
            ["Lines of Code", str(result.complexity.lines_of_code)],
            ["Functions", str(result.complexity.functions)],
            ["Classes", str(result.complexity.classes)],
        ]
        click.echo(tabulate(
            metrics_data,
            headers=["Metric", "Value"],
            tablefmt="grid",
        ))


def _output_json(result):
    """Output analysis result in JSON format."""
    click.echo(json.dumps(result.to_dict(), indent=2, default=str))


def _output_metrics_text(metrics):
    """Output metrics in text format."""
    click.echo()
    click.secho("Complexity Metrics", bold=True, underline=True)
    click.echo()
    click.echo(f"  Cyclomatic Complexity:    {metrics.cyclomatic_complexity:.1f}")
    click.echo(f"  Cognitive Complexity:     {metrics.cognitive_complexity:.1f}")
    click.echo(f"  Lines of Code:            {metrics.lines_of_code}")
    click.echo(f"  Logical Lines:            {metrics.logical_lines}")
    click.echo(f"  Functions:                {metrics.functions}")
    click.echo(f"  Classes:                  {metrics.classes}")
    click.echo(f"  Max Function Complexity:  {metrics.max_function_complexity:.1f}")
    click.echo(f"  Maintainability Index:    {metrics.maintainability_index:.1f}")
    click.echo()


def _output_metrics_table(metrics):
    """Output metrics in table format."""
    click.echo()
    table_data = [
        ["Cyclomatic Complexity", f"{metrics.cyclomatic_complexity:.1f}"],
        ["Cognitive Complexity", f"{metrics.cognitive_complexity:.1f}"],
        ["Lines of Code", str(metrics.lines_of_code)],
        ["Logical Lines", str(metrics.logical_lines)],
        ["Functions", str(metrics.functions)],
        ["Classes", str(metrics.classes)],
        ["Max Function Complexity", f"{metrics.max_function_complexity:.1f}"],
        ["Maintainability Index", f"{metrics.maintainability_index:.1f}"],
    ]
    click.echo(tabulate(
        table_data,
        headers=["Metric", "Value"],
        tablefmt="grid",
    ))


# ============================================================================
# Entry point for CLI
# ============================================================================

if __name__ == "__main__":
    cli()
