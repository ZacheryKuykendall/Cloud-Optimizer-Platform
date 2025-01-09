"""Cost Data Storage Service

A service for storing and managing cloud cost data with support for multiple
storage backends and data formats.
"""

from cost_storage.models import (
    StorageBackend,
    StorageFormat,
    CloudProvider,
    CostType,
    StorageConfig,
    RetentionPolicy,
    CostRecord,
    CostBatch,
    StorageMetrics,
    QueryFilter,
    AggregationLevel,
    AggregationDimension,
    AggregationConfig,
    AggregatedCost,
    PartitionConfig,
    BackupConfig,
    MaintenanceWindow,
)
from cost_storage.exceptions import (
    CostStorageError,
    ValidationError,
    ConfigurationError,
    StorageBackendError,
    ConnectionError,
    QueryError,
    DataImportError,
    DataExportError,
    RetentionPolicyError,
    PartitionError,
    BackupError,
    MaintenanceError,
    AggregationError,
    StorageQuotaError,
    DataCorruptionError,
    PerformanceError,
)

__version__ = "0.1.0"

__all__ = [
    # Storage Configuration
    "StorageBackend",
    "StorageFormat",
    "StorageConfig",
    "RetentionPolicy",
    "PartitionConfig",
    "BackupConfig",
    "MaintenanceWindow",

    # Cost Data Models
    "CloudProvider",
    "CostType",
    "CostRecord",
    "CostBatch",
    "StorageMetrics",

    # Query and Aggregation
    "QueryFilter",
    "AggregationLevel",
    "AggregationDimension",
    "AggregationConfig",
    "AggregatedCost",

    # Base Exceptions
    "CostStorageError",
    "ValidationError",
    "ConfigurationError",

    # Storage Exceptions
    "StorageBackendError",
    "ConnectionError",
    "QueryError",
    "StorageQuotaError",

    # Data Operation Exceptions
    "DataImportError",
    "DataExportError",
    "DataCorruptionError",

    # Management Exceptions
    "RetentionPolicyError",
    "PartitionError",
    "BackupError",
    "MaintenanceError",
    "AggregationError",
    "PerformanceError",
]

# Configure logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
