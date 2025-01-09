"""Tests for the currency conversion service."""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from unittest.mock import Mock, patch
from forex_python.converter import RatesNotAvailableError

from cloud_cost_normalization.currency import CurrencyService
from cloud_cost_normalization.models import CurrencyConversion
from cloud_cost_normalization.exceptions import (
    InvalidCurrencyError,
    CurrencyConversionError,
    RateNotFoundError,
)


@pytest.fixture
def mock_currency_rates():
    """Create a mock CurrencyRates instance."""
    with patch("cloud_cost_normalization.currency.CurrencyRates") as mock:
        yield mock.return_value


@pytest.fixture
def currency_service(mock_currency_rates):
    """Create a CurrencyService instance with mocked rates."""
    return CurrencyService()


def test_initialization():
    """Test currency service initialization."""
    service = CurrencyService(
        cache_ttl=7200,
        base_currency="EUR",
        fallback_source="test"
    )
    assert service.cache_ttl == 7200
    assert service.base_currency == "EUR"
    assert service.fallback_source == "test"
    assert service._rate_cache == {}


def test_get_exchange_rate_success(currency_service, mock_currency_rates):
    """Test successful exchange rate retrieval."""
    mock_currency_rates.get_rate.return_value = 1.25

    conversion = currency_service.get_exchange_rate("USD", "EUR")

    assert isinstance(conversion, CurrencyConversion)
    assert conversion.source_currency == "USD"
    assert conversion.target_currency == "EUR"
    assert conversion.exchange_rate == Decimal("1.25")
    mock_currency_rates.get_rate.assert_called_once_with("USD", "EUR")


def test_get_exchange_rate_caching(currency_service, mock_currency_rates):
    """Test that exchange rates are cached."""
    mock_currency_rates.get_rate.return_value = 1.25

    # First call should hit the API
    first_conversion = currency_service.get_exchange_rate("USD", "EUR")
    assert mock_currency_rates.get_rate.call_count == 1

    # Second call should use cache
    second_conversion = currency_service.get_exchange_rate("USD", "EUR")
    assert mock_currency_rates.get_rate.call_count == 1
    assert first_conversion.exchange_rate == second_conversion.exchange_rate


def test_get_exchange_rate_cache_expiry(currency_service, mock_currency_rates):
    """Test that cached rates expire after TTL."""
    mock_currency_rates.get_rate.return_value = 1.25
    currency_service.cache_ttl = 0  # Immediate expiry

    # First call
    currency_service.get_exchange_rate("USD", "EUR")
    
    # Second call should hit API again due to expired cache
    currency_service.get_exchange_rate("USD", "EUR")
    
    assert mock_currency_rates.get_rate.call_count == 2


def test_get_historical_rate(currency_service, mock_currency_rates):
    """Test historical exchange rate retrieval."""
    mock_currency_rates.get_rate.return_value = 1.15
    date = datetime(2023, 1, 1)

    conversion = currency_service.get_historical_rate("USD", "EUR", date)

    assert conversion.exchange_rate == Decimal("1.15")
    mock_currency_rates.get_rate.assert_called_once_with("USD", "EUR", date)


def test_convert_amount_success(currency_service, mock_currency_rates):
    """Test successful amount conversion."""
    mock_currency_rates.get_rate.return_value = 2.0
    amount = Decimal("100.00")

    result = currency_service.convert_amount(amount, "USD", "EUR")

    assert result == Decimal("200.00")


def test_convert_amount_same_currency(currency_service, mock_currency_rates):
    """Test conversion with same source and target currency."""
    amount = Decimal("100.00")

    result = currency_service.convert_amount(amount, "USD", "USD")

    assert result == amount
    mock_currency_rates.get_rate.assert_not_called()


def test_normalize_to_base(currency_service, mock_currency_rates):
    """Test normalization to base currency."""
    mock_currency_rates.get_rate.return_value = 0.85
    amount = Decimal("100.00")

    result = currency_service.normalize_to_base(amount, "EUR")

    assert result == Decimal("85.00")
    mock_currency_rates.get_rate.assert_called_once_with("EUR", "USD")


def test_invalid_currency_code(currency_service, mock_currency_rates):
    """Test handling of invalid currency codes."""
    mock_currency_rates.get_rate.side_effect = RatesNotAvailableError("Invalid currency")

    with pytest.raises(InvalidCurrencyError):
        currency_service.get_exchange_rate("INVALID", "EUR")


def test_rate_not_found(currency_service, mock_currency_rates):
    """Test handling of unavailable exchange rates."""
    mock_currency_rates.get_rate.side_effect = RatesNotAvailableError("Rate not found")

    with pytest.raises(RateNotFoundError):
        currency_service.get_exchange_rate("USD", "EUR")


def test_conversion_error(currency_service, mock_currency_rates):
    """Test handling of conversion errors."""
    mock_currency_rates.get_rate.side_effect = Exception("API Error")

    with pytest.raises(CurrencyConversionError):
        currency_service.get_exchange_rate("USD", "EUR")


def test_clear_cache(currency_service, mock_currency_rates):
    """Test cache clearing."""
    mock_currency_rates.get_rate.return_value = 1.25

    # Populate cache
    currency_service.get_exchange_rate("USD", "EUR")
    assert len(currency_service._rate_cache) == 1

    # Clear cache
    currency_service.clear_cache()
    assert len(currency_service._rate_cache) == 0


def test_currency_case_insensitive(currency_service, mock_currency_rates):
    """Test that currency codes are case insensitive."""
    mock_currency_rates.get_rate.return_value = 1.25

    # Test with different cases
    result1 = currency_service.get_exchange_rate("usd", "eur")
    result2 = currency_service.get_exchange_rate("USD", "EUR")

    assert result1.exchange_rate == result2.exchange_rate
    assert mock_currency_rates.get_rate.call_count == 1  # Should use cache


@pytest.mark.parametrize("amount,rate,expected", [
    (Decimal("100.00"), 1.5, Decimal("150.00")),
    (Decimal("0.00"), 1.5, Decimal("0.00")),
    (Decimal("0.01"), 2.0, Decimal("0.02")),
    (Decimal("999999.99"), 1.0, Decimal("999999.99")),
])
def test_convert_amount_various_values(
    currency_service,
    mock_currency_rates,
    amount,
    rate,
    expected
):
    """Test amount conversion with various values."""
    mock_currency_rates.get_rate.return_value = rate

    result = currency_service.convert_amount(amount, "USD", "EUR")

    assert result == expected


def test_concurrent_cache_access(currency_service, mock_currency_rates):
    """Test cache behavior with concurrent access simulation."""
    mock_currency_rates.get_rate.side_effect = [1.25, 1.26]  # Different rates

    # Simulate concurrent access by forcing cache misses
    currency_service.cache_ttl = 0

    result1 = currency_service.get_exchange_rate("USD", "EUR")
    result2 = currency_service.get_exchange_rate("USD", "EUR")

    assert result1.exchange_rate != result2.exchange_rate
    assert mock_currency_rates.get_rate.call_count == 2
