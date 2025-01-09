"""Terraform Cost Analyzer

A tool for analyzing Terraform plans and estimating cloud infrastructure costs.
This library integrates with AWS Cost Explorer and Cloud Cost Normalization
to provide accurate cost estimates across different cloud providers.
"""

from terraform_cost_analyzer.models import (
    TerraformPlan,
    TerraformResource,
    ModuleCall,
    PlanMetadata,
    ResourceAttribute,
    ResourceChange,
    ResourceDependency,
    TerraformActionType,
    TerraformProviderType,
    CostEstimate,
    CostBreakdown,
    AnalysisResult,
)
from terraform_cost_analyzer.parser import TerraformPlanParser
from terraform_cost_analyzer.exceptions import (
    TerraformCostAnalyzerError,
    PlanParsingError,
    ResourceParsingError,
    UnsupportedResourceError,
    CostEstimationError,
    ProviderError,
    ConfigurationError,
    ValidationError,
    DependencyError,
    ModuleError,
    WorkspaceError,
    BackendError,
    VariableError,
    OutputError,
    ExecutionError,
)

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "TerraformPlanParser",

    # Models
    "TerraformPlan",
    "TerraformResource",
    "ModuleCall",
    "PlanMetadata",
    "ResourceAttribute",
    "ResourceChange",
    "ResourceDependency",
    "TerraformActionType",
    "TerraformProviderType",
    "CostEstimate",
    "CostBreakdown",
    "AnalysisResult",

    # Exceptions
    "TerraformCostAnalyzerError",
    "PlanParsingError",
    "ResourceParsingError",
    "UnsupportedResourceError",
    "CostEstimationError",
    "ProviderError",
    "ConfigurationError",
    "ValidationError",
    "DependencyError",
    "ModuleError",
    "WorkspaceError",
    "BackendError",
    "VariableError",
    "OutputError",
    "ExecutionError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
