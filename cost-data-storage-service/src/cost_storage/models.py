"""Data models for Cost Data Storage Service.

This module provides data models for storing and managing cloud cost data
across different storage backends and data formats.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class StorageBackend(str, Enum):
    """Supported storage backends."""
    POSTGRESQL = "POSTGRESQL"
    MONGODB = "MONGODB"
    CLICKHOUSE = "CLICKHOUSE"
    ELASTICSEARCH = "ELASTICSEARCH"
    CASSANDRA = "CASSANDRA"
    INFLUXDB = "INFLUXDB"
    TIMESCALEDB = "TIMESCALEDB"
    DUCKDB = "DUCKDB"


class StorageFormat(str, Enum):
    """Supported data storage formats."""
    JSON = "JSON"
    PARQUET = "PARQUET"
    AVRO = "AVRO"
    ORC = "ORC"
    CSV = "CSV"
    ARROW = "ARROW"


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"
    ORACLE = "ORACLE"
    ALIBABA = "ALIBABA"
    OTHER = "OTHER"


class CostType(str, Enum):
    """Types of cloud costs."""
    COMPUTE = "COMPUTE"
    STORAGE = "STORAGE"
    NETWORK = "NETWORK"
    DATABASE = "DATABASE"
    ANALYTICS = "ANALYTICS"
    SERVERLESS = "SERVERLESS"
    SUPPORT = "SUPPORT"
    OTHER = "OTHER"


class StorageConfig(BaseModel):
    """Configuration for storage backend."""
    backend: StorageBackend
    format: StorageFormat
    connection_string: str
    database_name: str
    table_name: Optional[str] = None
    schema_name: Optional[str] = None
    credentials: Dict[str, str] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class RetentionPolicy(BaseModel):
    """Data retention policy."""
    duration_days: int
    archive_after_days: Optional[int] = None
    delete_after_days: Optional[int] = None
    archive_storage: Optional[StorageConfig] = None
    compression_enabled: bool = True
    exceptions: List[str] = Field(default_factory=list)


class CostRecord(BaseModel):
    """Individual cost record."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    provider: CloudProvider
    account_id: str
    region: str
    service: str
    resource_id: str
    resource_type: str
    cost_type: CostType
    amount: Decimal
    currency: str
    unit: Optional[str] = None
    quantity: Optional[Decimal] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("amount", "quantity")
    def validate_decimal(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate decimal values."""
        if v is not None and v < 0:
            raise ValueError("Value must be non-negative")
        return v


class CostBatch(BaseModel):
    """Batch of cost records."""
    id: UUID = Field(default_factory=uuid4)
    records: List[CostRecord]
    source: str
    import_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageMetrics(BaseModel):
    """Storage metrics."""
    backend: StorageBackend
    total_records: int
    total_size_bytes: int
    oldest_record: datetime
    newest_record: datetime
    record_count_by_provider: Dict[str, int]
    size_by_provider: Dict[str, int]
    compression_ratio: float
    query_latency_ms: float
    write_latency_ms: float


class QueryFilter(BaseModel):
    """Query filter parameters."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    providers: Optional[List[CloudProvider]] = None
    accounts: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    services: Optional[List[str]] = None
    cost_types: Optional[List[CostType]] = None
    tags: Dict[str, List[str]] = Field(default_factory=dict)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


class AggregationLevel(str, Enum):
    """Levels of cost aggregation."""
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"


class AggregationDimension(str, Enum):
    """Dimensions for cost aggregation."""
    PROVIDER = "PROVIDER"
    ACCOUNT = "ACCOUNT"
    REGION = "REGION"
    SERVICE = "SERVICE"
    RESOURCE_TYPE = "RESOURCE_TYPE"
    COST_TYPE = "COST_TYPE"
    TAG = "TAG"


class AggregationConfig(BaseModel):
    """Configuration for cost aggregation."""
    time_level: AggregationLevel
    dimensions: List[AggregationDimension]
    include_tags: List[str] = Field(default_factory=list)
    metrics: List[str] = ["amount", "quantity"]
    having: Optional[Dict[str, Any]] = None


class AggregatedCost(BaseModel):
    """Aggregated cost data."""
    period_start: datetime
    period_end: datetime
    dimensions: Dict[str, str]
    metrics: Dict[str, Decimal]
    record_count: int


class PartitionConfig(BaseModel):
    """Configuration for data partitioning."""
    enabled: bool = True
    strategy: str = "time"  # time, provider, region, etc.
    interval: str = "month"  # day, week, month, year
    compression_codec: Optional[str] = None
    max_partition_size: Optional[int] = None


class BackupConfig(BaseModel):
    """Configuration for data backup."""
    enabled: bool = True
    frequency: str = "daily"
    retention_days: int = 30
    storage: StorageConfig
    encryption_enabled: bool = True
    compression_enabled: bool = True


class MaintenanceWindow(BaseModel):
    """Configuration for maintenance windows."""
    enabled: bool = True
    day_of_week: str = "sunday"
    start_time: str = "00:00"
    duration_hours: int = 4
    tasks: List[str] = ["vacuum", "analyze", "backup"]
