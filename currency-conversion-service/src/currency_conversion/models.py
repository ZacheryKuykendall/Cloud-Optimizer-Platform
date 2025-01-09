"""Data models for Currency Conversion Service.

This module provides data models for working with currencies, exchange rates,
and money amounts in the context of cloud cost data.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class RateSource(str, Enum):
    """Sources of exchange rate data."""
    FOREX = "FOREX"
    ECB = "ECB"  # European Central Bank
    OPEN_EXCHANGE = "OPEN_EXCHANGE"
    CUSTOM = "CUSTOM"


class RateType(str, Enum):
    """Types of exchange rates."""
    SPOT = "SPOT"
    FORWARD = "FORWARD"
    AVERAGE = "AVERAGE"
    CUSTOM = "CUSTOM"


class UpdateFrequency(str, Enum):
    """Frequency of exchange rate updates."""
    REALTIME = "REALTIME"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class CacheStrategy(str, Enum):
    """Strategies for caching exchange rates."""
    NONE = "NONE"
    MEMORY = "MEMORY"
    REDIS = "REDIS"
    DATABASE = "DATABASE"


class Money(BaseModel):
    """Model for money amounts."""
    amount: Decimal
    currency: str

    @validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()

    def __add__(self, other: "Money") -> "Money":
        """Add two money amounts."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two money amounts."""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: Union[int, float, Decimal]) -> "Money":
        """Multiply money amount by a factor."""
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)


class ExchangeRate(BaseModel):
    """Model for exchange rates."""
    id: UUID = Field(default_factory=uuid4)
    source_currency: str
    target_currency: str
    rate: Decimal
    source: RateSource
    type: RateType = RateType.SPOT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    provider_data: Dict[str, str] = Field(default_factory=dict)

    @validator("source_currency", "target_currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()

    @validator("rate")
    def validate_rate(cls, v: Decimal) -> Decimal:
        """Validate exchange rate."""
        if v <= 0:
            raise ValueError("Exchange rate must be positive")
        return v


class ConversionRequest(BaseModel):
    """Model for conversion requests."""
    amount: Money
    target_currency: str
    reference_date: Optional[date] = None
    rate_type: RateType = RateType.SPOT
    rate_source: Optional[RateSource] = None
    context: Dict[str, str] = Field(default_factory=dict)

    @validator("target_currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class ConversionResult(BaseModel):
    """Model for conversion results."""
    id: UUID = Field(default_factory=uuid4)
    request: ConversionRequest
    result: Money
    rate_used: ExchangeRate
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateProviderConfig(BaseModel):
    """Model for rate provider configuration."""
    provider: RateSource
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    update_frequency: UpdateFrequency = UpdateFrequency.DAILY
    cache_strategy: CacheStrategy = CacheStrategy.MEMORY
    timeout_seconds: int = 30
    retry_attempts: int = 3
    supported_currencies: List[str] = Field(default_factory=list)
    provider_settings: Dict[str, str] = Field(default_factory=dict)


class ConversionBatch(BaseModel):
    """Model for batch conversions."""
    id: UUID = Field(default_factory=uuid4)
    requests: List[ConversionRequest]
    target_currency: str
    reference_date: Optional[date] = None
    rate_type: RateType = RateType.SPOT
    rate_source: Optional[RateSource] = None
    context: Dict[str, str] = Field(default_factory=dict)

    @validator("target_currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v.isalpha() or len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class BatchResult(BaseModel):
    """Model for batch conversion results."""
    batch_id: UUID
    results: List[ConversionResult]
    summary: Dict[str, Money] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RateAlert(BaseModel):
    """Model for exchange rate alerts."""
    id: UUID = Field(default_factory=uuid4)
    source_currency: str
    target_currency: str
    threshold: Decimal
    condition: str  # "above", "below", "change_percent"
    notification_channels: List[str]
    is_active: bool = True
    last_triggered: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversionMetrics(BaseModel):
    """Model for conversion metrics."""
    period_start: datetime
    period_end: datetime
    total_conversions: int
    total_amount_base: Money
    conversion_by_currency: Dict[str, int]
    average_response_time: float  # milliseconds
    error_count: int
    rate_provider_stats: Dict[str, Dict[str, Union[int, float]]]
