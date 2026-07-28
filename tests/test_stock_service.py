from unittest.mock import AsyncMock, patch

import pytest

from src.services import stock_service


async def _analyze_with_dividends(dividend_data: dict[str, float]) -> dict:
    with patch.multiple(
        stock_service.yf_client,
        get_history=AsyncMock(return_value=[{"Close": 100.0}, {"Close": 101.0}]),
        get_financials=AsyncMock(return_value={}),
        get_recommendations=AsyncMock(return_value=[]),
        get_news=AsyncMock(return_value=[]),
        get_market_info=AsyncMock(return_value={"currency": "EUR"}),
        get_dividend_data=AsyncMock(return_value=dividend_data),
    ):
        return await stock_service.analyze_stock("TEST")


def test_extract_financial_metrics_success() -> None:
    mock_financials = {
        "income_statement": {
            "2023-12-31": {"Total Revenue": 1000, "Net Income": 200},
            "2022-12-31": {"Total Revenue": 800, "Net Income": 150},
        }
    }

    metrics = stock_service._extract_financial_metrics(mock_financials)
    assert metrics["revenue"] == 1000
    assert metrics["net_income"] == 200
    assert metrics["profit_margin_pct"] == 20.0


def test_extract_financial_metrics_empty() -> None:
    metrics = stock_service._extract_financial_metrics({})
    assert metrics["revenue"] is None
    assert metrics["net_income"] is None
    assert metrics["profit_margin_pct"] is None


def test_extract_financial_metrics_missing_keys() -> None:
    mock_financials = {"income_statement": {"2023-12-31": {"Some Other Key": 1000}}}
    metrics = stock_service._extract_financial_metrics(mock_financials)
    assert metrics["revenue"] is None
    assert metrics["net_income"] is None


@pytest.mark.asyncio
async def test_dividend_yields_are_already_percentage_points() -> None:
    result = await _analyze_with_dividends(
        {"yield": 0.32, "five_year_avg_yield": 0.50}
    )

    assert result["dividends"]["yield_pct"] == 0.32
    assert result["dividends"]["five_year_avg_yield_pct"] == 0.50


@pytest.mark.asyncio
async def test_missing_dividend_values_remain_none() -> None:
    result = await _analyze_with_dividends({})

    assert result["dividends"]["yield_pct"] is None
    assert result["dividends"]["five_year_avg_yield_pct"] is None


@pytest.mark.asyncio
async def test_dividend_yields_greater_than_one_are_not_rescaled() -> None:
    result = await _analyze_with_dividends(
        {"yield": 3.85, "five_year_avg_yield": 4.25}
    )

    assert result["dividends"]["yield_pct"] == 3.85
    assert result["dividends"]["five_year_avg_yield_pct"] == 4.25
