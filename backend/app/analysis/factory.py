"""
Factory pattern for analyzer plugin selection.

Enables clean architecture:
- Choose analyzer based on configuration/availability
- Auto-detect best available tool
- Easy to add new analyzers
- Zero coupling to application code
"""

from typing import Any, Dict, Literal, Optional

from .interfaces import CodeAnalyzer
from .local_analyzer import LocalAnalyzer


def create_analyzer(
    analyzer_type: Literal["local", "ldra", "mock"] = "local",
    config: Optional[Dict[str, Any]] = None,
) -> CodeAnalyzer:
    """
    Factory function to create appropriate analyzer.

    Args:
        analyzer_type: Type of analyzer to create
            - "local": Built-in analyzer (always available)
            - "ldra": LDRA adapter (requires license)
            - "mock": Mock analyzer (for testing)
        config: Optional configuration dictionary

    Returns:
        CodeAnalyzer instance

    Raises:
        RuntimeError: If LDRA requested but not available
        ValueError: If unknown analyzer type

    Examples:
        # Use local analyzer (no dependencies)
        analyzer = create_analyzer("local")
        result = analyzer.analyze_file("backend/app/main.py")

        # Use LDRA (if licensed)
        analyzer = create_analyzer("ldra")

        # Use mock for testing
        analyzer = create_analyzer("mock")
    """
    from .local_analyzer import LocalAnalyzer

    if analyzer_type == "local":
        return LocalAnalyzer(config)

    elif analyzer_type == "ldra":
        try:
            from .ldra_adapter import LDRAAdapter
            return LDRAAdapter(config)
        except ImportError:
            raise RuntimeError(
                "LDRA analyzer not available. "
                "Install LDRA SDK or use 'local' analyzer. "
                "For now: analyzer = create_analyzer('local')"
            )

    elif analyzer_type == "mock":
        from .mock_analyzer import MockAnalyzer
        return MockAnalyzer(config)

    else:
        raise ValueError(
            f"Unknown analyzer type: {analyzer_type}. "
            f"Must be 'local', 'ldra', or 'mock'"
        )


def get_available_analyzer(
    preferred: Literal["ldra", "local"] = "local",
    config: Optional[Dict[str, Any]] = None,
) -> CodeAnalyzer:
    """
    Auto-detect best available analyzer with fallback.

    Priority order:
    1. If preferred="ldra" and licensed → use LDRA
    2. Otherwise → use LocalAnalyzer

    Args:
        preferred: Preferred analyzer type
        config: Optional configuration

    Returns:
        CodeAnalyzer instance (best available)

    Examples:
        # Try LDRA, fall back to local if not available
        analyzer = get_available_analyzer(preferred="ldra")

        # Always use local
        analyzer = get_available_analyzer(preferred="local")
    """
    if preferred == "ldra":
        try:
            from .ldra_adapter import LDRAAdapter
            print("✓ Using LDRA analyzer (licensed)")
            return LDRAAdapter(config)
        except ImportError:
            print("⚠ LDRA not available, using local analyzer")
            from .local_analyzer import LocalAnalyzer
            return LocalAnalyzer(config)

    # Default to local
    from .local_analyzer import LocalAnalyzer
    return LocalAnalyzer(config)


class AnalyzerFactory:
    """
    Analyzer factory class (alternative to functions above).

    Use this for:
    - Managing multiple analyzer instances
    - Complex configuration
    - Plugin registration
    """

    # Registry of available analyzers
    _analyzers: Dict[str, Any] = {}

    @staticmethod
    def register(name: str, analyzer_class: type) -> None:
        """
        Register a new analyzer implementation.

        Args:
            name: Analyzer name (e.g., "ldra", "sonarqube")
            analyzer_class: Class implementing CodeAnalyzer

        Examples:
            from backend.app.analysis.ldra_adapter import LDRAAdapter
            AnalyzerFactory.register("ldra", LDRAAdapter)
        """
        AnalyzerFactory._analyzers[name] = analyzer_class

    @staticmethod
    def get(
        name: str = "local",
        config: Optional[Dict[str, Any]] = None,
    ) -> CodeAnalyzer:
        """
        Get analyzer by name.

        Args:
            name: Analyzer name
            config: Optional configuration

        Returns:
            CodeAnalyzer instance

        Raises:
            ValueError: If analyzer not registered
        """
        if name not in AnalyzerFactory._analyzers:
            raise ValueError(
                f"Analyzer '{name}' not registered. "
                f"Available: {list(AnalyzerFactory._analyzers.keys())}"
            )

        analyzer_class = AnalyzerFactory._analyzers[name]
        return analyzer_class(config)

    @staticmethod
    def list_available() -> list:
        """List registered analyzers"""
        return list(AnalyzerFactory._analyzers.keys())


# Register default analyzers
AnalyzerFactory.register("local", LocalAnalyzer)

# LDRA will be registered when available
# from .ldra_adapter import LDRAAdapter
# AnalyzerFactory.register("ldra", LDRAAdapter)
