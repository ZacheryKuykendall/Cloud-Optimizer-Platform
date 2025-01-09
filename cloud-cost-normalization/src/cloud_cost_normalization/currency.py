"""Currency conversion service for cloud cost normalization.

This module provides functionality for currency conversion and exchange rate management,
including rate caching and historical rate support.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, Tuple
from forex_python.converter import CurrencyRates, RatesNotAvailableError
from pydantic import ValidationError

from cloud_cost_normalization.models import CurrencyConversion
from cloud_cost_normalization.exceptions import (
    CurrencyConversionError,
    InvalidCurrencyError,
    RateNotFoundError,
)

logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for handling currency conversions and exchange rate management."""

    def __init__(
        self,
        cache_ttl: int = 3600,
        base_currency: str = "USD",
        fallback_source: Optional[str] = None
    ):
        """Initialize the currency service.

        Args:
            cache_ttl: Time to live for cached exchange rates in seconds.
            base_currency: Base currency for conversions.
            fallback_source: Optional fallback source for exchange rates.
        """
        self.cache_ttl = cache_ttl
        self.base_currency = base_currency.upper()
        self.fallback_source = fallback_source
        self.currency_rates = CurrencyRates()
        self._rate_cache: Dict[Tuple[str, str, datetime], CurrencyConversion] = {}

    def _get_cached_rate(
        self,
        source_currency: str,
        target_currency: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[CurrencyConversion]:
        """Get cached exchange rate if available and not expired.

        Args:
            source_currency: Source currency code.
            target_currency: Target currency code.
            timestamp: Optional timestamp for historical rates.

        Returns:
            Cached CurrencyConversion if available, None otherwise.
        """
        cache_key = (source_currency, target_currency, timestamp or datetime.utcnow())
        if cache_key in self._rate_cache:
            conversion = self._rate_cache[cache_key]
            if (datetime.utcnow() - conversion.timestamp).total_seconds() < self.cache_ttl:
                return conversion
            else:
                del self._rate_cache[cache_key]
        return None

    def _cache_rate(self, conversion: CurrencyConversion) -> None:
        """Cache an exchange rate.

        Args:
            conversion: CurrencyConversion to cache.
        """
        cache_key = (
            conversion.source_currency,
            conversion.target_currency,
            conversion.timestamp
        )
        self._rate_cache[cache_key] = conversion

    def get_exchange_rate(
        self,
        source_currency: str,
        target_currency: str,
        timestamp: Optional[datetime] = None
    ) -> CurrencyConversion:
        """Get exchange rate between two currencies.

        Args:
            source_currency: Source currency code.
            target_currency: Target currency code.
            timestamp: Optional timestamp for historical rates.

        Returns:
            CurrencyConversion object containing the exchange rate.

        Raises:
            InvalidCurrencyError: If currency codes are invalid.
            RateNotFoundError: If exchange rate is not available.
            CurrencyConversionError: If conversion fails.
        """
        source_currency = source_currency.upper()
        target_currency = target_currency.upper()

        # Check cache first
        cached_rate = self._get_cached_rate(source_currency, target_currency, timestamp)
        if cached_rate:
            return cached_rate

        try:
            # Get current or historical rate
            if timestamp:
                rate = self.currency_rates.get_rate(
                    source_currency,
                    target_currency,
                    timestamp
                )
            else:
                rate = self.currency_rates.get_rate(
                    source_currency,
                    target_currency
                )

            conversion = CurrencyConversion(
                source_currency=source_currency,
                target_currency=target_currency,
                exchange_rate=Decimal(str(rate)),
                timestamp=timestamp or datetime.utcnow()
            )

            # Cache the rate
            self._cache_rate(conversion)
            return conversion

        except RatesNotAvailableError as e:
            logger.error(
                "Exchange rate not available for %s to %s: %s",
                source_currency,
                target_currency,
                str(e)
            )
            raise RateNotFoundError(
                f"Exchange rate not available for {source_currency} to {target_currency}"
            )
        except ValidationError as e:
            logger.error(
                "Invalid currency codes - source: %s, target: %s: %s",
                source_currency,
                target_currency,
                str(e)
            )
            raise InvalidCurrencyError(
                f"Invalid currency codes: {source_currency}, {target_currency}"
            )
        except Exception as e:
            logger.error(
                "Currency conversion error for %s to %s: %s",
                source_currency,
                target_currency,
                str(e)
            )
            raise CurrencyConversionError(
                f"Failed to convert {source_currency} to {target_currency}: {str(e)}"
            )

    def convert_amount(
        self,
        amount: Decimal,
        source_currency: str,
        target_currency: str,
        timestamp: Optional[datetime] = None
    ) -> Decimal:
        """Convert an amount from one currency to another.

        Args:
            amount: Amount to convert.
            source_currency: Source currency code.
            target_currency: Target currency code.
            timestamp: Optional timestamp for historical rates.

        Returns:
            Converted amount in target currency.

        Raises:
            InvalidCurrencyError: If currency codes are invalid.
            RateNotFoundError: If exchange rate is not available.
            CurrencyConversionError: If conversion fails.
        """
        if source_currency.upper() == target_currency.upper():
            return amount

        conversion = self.get_exchange_rate(
            source_currency,
            target_currency,
            timestamp
        )
        return amount * conversion.exchange_rate

    def get_historical_rate(
        self,
        source_currency: str,
        target_currency: str,
        date: datetime
    ) -> CurrencyConversion:
        """Get historical exchange rate for a specific date.

        Args:
            source_currency: Source currency code.
            target_currency: Target currency code.
            date: Date for historical rate.

        Returns:
            CurrencyConversion object containing the historical exchange rate.

        Raises:
            InvalidCurrencyError: If currency codes are invalid.
            RateNotFoundError: If historical rate is not available.
            CurrencyConversionError: If conversion fails.
        """
        return self.get_exchange_rate(source_currency, target_currency, date)

    def normalize_to_base(
        self,
        amount: Decimal,
        source_currency: str,
        timestamp: Optional[datetime] = None
    ) -> Decimal:
        """Convert an amount to the base currency.

        Args:
            amount: Amount to convert.
            source_currency: Source currency code.
            timestamp: Optional timestamp for historical rates.

        Returns:
            Amount converted to base currency.

        Raises:
            InvalidCurrencyError: If currency codes are invalid.
            RateNotFoundError: If exchange rate is not available.
            CurrencyConversionError: If conversion fails.
        """
        return self.convert_amount(
            amount,
            source_currency,
            self.base_currency,
            timestamp
        )

    def clear_cache(self) -> None:
        """Clear the exchange rate cache."""
        self._rate_cache.clear()
        logger.info("Exchange rate cache cleared")
