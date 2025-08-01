"""
Decision Layer - A framework for managing business decision logic

This module provides the core functionality for the Decision Layer framework,
including decision functions, validation, tracing, and cross-domain integration.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import DecisionContext, DecisionEngine, DecisionFunction, DecisionPlugin
from .config import DecisionLayerConfig, load_config
from .errors import (
    DecisionLayerError,
    DeploymentError,
    ExecutionError,
    FunctionNotFoundError,
    RegistryError,
    ShadowExecutionError,
    StorageError,
    ValidationError,
)
from .knowledge_graph_integration import (
    KnowledgeGraphIntegration,
    create_knowledge_graph_integration,
)
from .llm_integration import LLMIntegration, create_llm_integration
from .natural_language_interface import (
    CrossDomainResponse,
    QueryIntent,
    UnifiedNaturalLanguageInterface,
    create_unified_interface,
)
from .ontology_integration import OntologyIntegration, create_ontology_integration
from .registry import FunctionRegistry, FunctionStatus
from .schemas import DecisionSchema, FieldType, SchemaField, create_schema_from_dict
from .shadow_runner import ShadowRunner
from .storage import FileStorage, PostgreSQLStorage, StorageBackend
from .yaml_interface import (
    YAMLDecisionParser,
    load_decision_from_yaml,
    create_yaml_template,
    validate_yaml_decision,
)

__version__ = "1.0.0"
__author__ = "Decision Layer Team"
__email__ = "team@decision-layer.com"

# Core components
__all__ = [
    # Core functionality
    "DecisionContext",
    "DecisionEngine",
    "DecisionFunction",
    "DecisionPlugin",
    # Configuration
    "DecisionLayerConfig",
    "load_config",
    # Registry and storage
    "FunctionRegistry",
    "FunctionStatus",
    "StorageBackend",
    "FileStorage",
    "PostgreSQLStorage",
    # Schemas and validation
    "DecisionSchema",
    "SchemaField",
    "FieldType",
    "create_schema_from_dict",
    # Shadow testing
    "ShadowRunner",
    # YAML interface
    "YAMLDecisionParser",
    "load_decision_from_yaml",
    "create_yaml_template",
    "validate_yaml_decision",
    # Cross-domain integration
    "LLMIntegration",
    "OntologyIntegration",
    "KnowledgeGraphIntegration",
    "UnifiedNaturalLanguageInterface",
    "QueryIntent",
    "CrossDomainResponse",
    # Factory functions
    "create_llm_integration",
    "create_ontology_integration",
    "create_knowledge_graph_integration",
    "create_unified_interface",
    # Error classes
    "DecisionLayerError",
    "ValidationError",
    "ExecutionError",
    "DeploymentError",
    "FunctionNotFoundError",
    "StorageError",
    "RegistryError",
    "ShadowExecutionError",
]


def create_decision_engine(
    storage_backend: Optional[StorageBackend] = None,
    trace_sink: Optional[Any] = None,
) -> DecisionEngine:
    """
    Create a DecisionEngine instance with optional storage and trace configuration.

    Args:
        storage_backend: Optional storage backend for function persistence
        trace_sink: Optional trace sink for execution logging

    Returns:
        Configured DecisionEngine instance
    """
    if storage_backend is None:
        storage_backend = FileStorage()

    return DecisionEngine(storage_backend=storage_backend, trace_sink=trace_sink)


def create_function_registry(
    storage_backend: Optional[StorageBackend] = None,
) -> FunctionRegistry:
    """
    Create a FunctionRegistry instance with optional storage configuration.

    Args:
        storage_backend: Optional storage backend for function persistence

    Returns:
        Configured FunctionRegistry instance
    """
    if storage_backend is None:
        storage_backend = FileStorage()

    return FunctionRegistry(storage_backend=storage_backend)


async def execute_decision(
    function_id: str,
    input_data: Dict[str, Any],
    version: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    engine: Optional[DecisionEngine] = None,
) -> Dict[str, Any]:
    """
    Execute a decision function with the given input data.

    Args:
        function_id: Identifier of the decision function to execute
        input_data: Input data for the decision function
        version: Optional version of the function to execute
        context: Optional execution context
        engine: Optional DecisionEngine instance

    Returns:
        Decision result as a dictionary

    Raises:
        FunctionNotFoundError: If the function is not found
        ValidationError: If input validation fails
        ExecutionError: If execution fails
    """
    if engine is None:
        engine = create_decision_engine()

    decision_context = DecisionContext(
        function_id=function_id,
        version=version,
        timestamp=datetime.now(timezone.utc),
        caller="api",
        metadata=context or {},
    )

    return await engine.execute(input_data, decision_context)


def deploy_function(
    function_id: str,
    version: str,
    function_code: str,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    registry: Optional[FunctionRegistry] = None,
) -> None:
    """
    Deploy a decision function to the registry.

    Args:
        function_id: Unique identifier for the function
        version: Version string for the function
        function_code: Python code implementing the function
        input_schema: JSON schema for input validation
        output_schema: JSON schema for output validation
        metadata: Optional metadata for the function
        registry: Optional FunctionRegistry instance

    Raises:
        DeploymentError: If deployment fails
    """
    if registry is None:
        registry = create_function_registry()

    registry.deploy_function(
        function_id=function_id,
        version=version,
        function_code=function_code,
        input_schema=input_schema,
        output_schema=output_schema,
        metadata=metadata or {},
    )


def list_functions(
    registry: Optional[FunctionRegistry] = None,
    status: Optional[FunctionStatus] = None,
) -> List[Dict[str, Any]]:
    """
    List all functions in the registry.

    Args:
        registry: Optional FunctionRegistry instance
        status: Optional status filter

    Returns:
        List of function metadata dictionaries
    """
    if registry is None:
        registry = create_function_registry()

    return registry.list_functions(status=status)


def get_function_info(
    function_id: str,
    registry: Optional[FunctionRegistry] = None,
) -> Dict[str, Any]:
    """
    Get detailed information about a function.

    Args:
        function_id: Identifier of the function
        registry: Optional FunctionRegistry instance

    Returns:
        Function metadata dictionary

    Raises:
        FunctionNotFoundError: If the function is not found
    """
    if registry is None:
        registry = create_function_registry()

    return registry.get_function_info(function_id)


# Convenience function for quick setup
def init_system(config_path: Optional[str] = None) -> None:
    """
    Initialize the Decision Layer system with default configuration.

    Args:
        config_path: Optional path to configuration file
    """
    # Create necessary directories
    Path("./registry").mkdir(exist_ok=True)
    Path("./traces").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)

    # Create default config if not provided
    if config_path is None:
        config_path = "./config.yaml"

    if not Path(config_path).exists():
        default_config = {
            "storage": {"backend": "file", "path": "./registry"},
            "tracing": {"enabled": True, "level": "INFO"},
            "security": {"enable_auth": False},
        }
        with open(config_path, "w") as f:
            import yaml

            yaml.dump(default_config, f, default_flow_style=False)
