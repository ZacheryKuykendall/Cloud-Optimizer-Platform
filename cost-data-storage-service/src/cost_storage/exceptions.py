"""Custom exceptions for Cost Data Storage Service.

This module defines exceptions specific to cost data storage operations,
including storage backend errors and data validation issues.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID


class CostStorageError(Exception):
    """Base exception for all cost storage errors."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(CostStorageError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(CostStorageError):
    """Raised when there are configuration issues."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.config_value = config_value


class StorageBackendError(CostStorageError):
    """Raised when there are issues with storage backends."""

    def __init__(
        self,
        message: str,
        backend: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.backend = backend
        self.operation = operation
        self.details = details or {}


class ConnectionError(StorageBackendError):
    """Raised when there are connection issues with storage backend."""

    def __init__(
        self,
        message: str,
        backend: str,
        connection_string: str,
        retry_count: Optional[int] = None
    ):
        super().__init__(message, backend, "connect")
        self.connection_string = connection_string
        self.retry_count = retry_count


class QueryError(StorageBackendError):
    """Raised when there are issues with database queries."""

    def __init__(
        self,
        message: str,
        backend: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, backend, "query")
        self.query = query
        self.parameters = parameters or {}


class DataImportError(CostStorageError):
    """Raised when there are issues importing cost data."""

    def __init__(
        self,
        message: str,
        source: str,
        record_count: int,
        failed_records: List[Dict[str, Any]]
    ):
        super().__init__(message)
        self.source = source
        self.record_count = record_count
        self.failed_records = failed_records


class DataExportError(CostStorageError):
    """Raised when there are issues exporting cost data."""

    def __init__(
        self,
        message: str,
        destination: str,
        format: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.destination = destination
        self.format = format
        self.details = details or {}


class RetentionPolicyError(CostStorageError):
    """Raised when there are issues with retention policies."""

    def __init__(
        self,
        message: str,
        policy_id: UUID,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.policy_id = policy_id
        self.operation = operation
        self.details = details or {}


class PartitionError(CostStorageError):
    """Raised when there are issues with data partitioning."""

    def __init__(
        self,
        message: str,
        partition_key: str,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.partition_key = partition_key
        self.operation = operation
        self.details = details or {}


class BackupError(CostStorageError):
    """Raised when there are issues with data backups."""

    def __init__(
        self,
        message: str,
        backup_id: UUID,
        storage_location: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.backup_id = backup_id
        self.storage_location = storage_location
        self.details = details or {}


class MaintenanceError(CostStorageError):
    """Raised when there are issues with maintenance operations."""

    def __init__(
        self,
        message: str,
        task: str,
        window: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.task = task
        self.window = window
        self.details = details or {}


class AggregationError(CostStorageError):
    """Raised when there are issues with cost aggregation."""

    def __init__(
        self,
        message: str,
        dimensions: List[str],
        time_range: Optional[Dict[str, date]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.dimensions = dimensions
        self.time_range = time_range
        self.details = details or {}


class StorageQuotaError(CostStorageError):
    """Raised when storage quotas are exceeded."""

    def __init__(
        self,
        message: str,
        backend: str,
        current_size: int,
        quota_limit: int
    ):
        super().__init__(message)
        self.backend = backend
        self.current_size = current_size
        self.quota_limit = quota_limit


class DataCorruptionError(CostStorageError):
    """Raised when data corruption is detected."""

    def __init__(
        self,
        message: str,
        record_ids: List[UUID],
        corruption_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.record_ids = record_ids
        self.corruption_type = corruption_type
        self.details = details or {}


class PerformanceError(CostStorageError):
    """Raised when performance thresholds are exceeded."""

    def __init__(
        self,
        message: str,
        operation: str,
        duration_ms: float,
        threshold_ms: float
    ):
        super().__init__(message)
        self.operation = operation
        self.duration_ms = duration_ms
        self.threshold_ms = threshold_ms
