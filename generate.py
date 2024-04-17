import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from absl import app
from polygon import RESTClient

import params

TICKER = "TSLA"


@dataclass
class Datum:
    news: list[str]
    ema_short: float | None
    ema_long: float | None
    macd_value: float | None
    macd_signal: float | None
    rsi: float | None


def date_from_utc(utc: str):
    return datetime.fromisoformat(utc.rstrip("Z")).date().isoformat()


def get_news(start: str, ticker: str, polygon: RESTClient):
    return (
        pd.DataFrame(
            [
                {"date": date_from_utc(news.published_utc), "news": news.title}
                for news in polygon.list_ticker_news(
                    ticker, published_utc_gt=start
                )
            ]
        )
        .set_index("date")
        .groupby("date")["news"]
        .agg(list)
        .reset_index()
        .set_index("date")
    )


def date_from_milliseconds(milliseconds: int):
    return datetime.fromtimestamp(milliseconds / 1000).date().isoformat()


def get_ema(start: str, ticker: str, polygon: RESTClient):
    short = pd.DataFrame(
        [
            {
                "date": date_from_milliseconds(value.timestamp),
                "ema_short": value.value,
            }
            for value in polygon.get_ema(
                ticker=ticker,
                timespan="day",
                window=50,
                series_type="close",
                timestamp_gt=start,
            ).values
        ]
    )

    long = pd.DataFrame(
        [
            {
                "date": date_from_milliseconds(value.timestamp),
                "ema_long": value.value,
            }
            for value in polygon.get_ema(
                ticker=ticker,
                timespan="day",
                window=200,
                series_type="close",
                timestamp_gt=start,
            ).values
        ]
    )

    return pd.merge(short, long, on="date").set_index("date")


def get_macd(start: str, ticker: str, polygon: RESTClient):
    return pd.DataFrame(
        [
            {
                "date": date_from_milliseconds(value.timestamp),
                "value": value.value,
                "signal": value.signal,
            }
            for value in polygon.get_macd(
                ticker=ticker,
                timespan="day",
                short_window=12,
                long_window=26,
                signal_window=9,
                series_type="close",
                timestamp_gt=start,
            ).values
        ]
    ).set_index("date")


def get_rsi(start: str, ticker: str, polygon: RESTClient):
    return pd.DataFrame(
        [
            {
                "date": date_from_milliseconds(value.timestamp),
                "rsi": value.value,
            }
            for value in polygon.get_rsi(
                ticker=ticker,
                timespan="day",
                window=14,
                series_type="close",
                timestamp_gt=start,
            ).values
        ]
    ).set_index("date")


def main(argv):
    logging.basicConfig(level=logging.INFO)
    polygon = RESTClient(params.POLYGON)
    start = date.today() - timedelta(days=365)

    data = get_news(start, TICKER, polygon).join(
        [
            get_ema(start, TICKER, polygon),
            get_macd(start, TICKER, polygon),
            get_rsi(start, TICKER, polygon),
        ],
        how="outer",
    )

    with open(
        Path(os.environ["BUILD_WORKSPACE_DIRECTORY"]) / "data.json", "w"
    ) as f:
        data.to_json(f, orient="index", indent=4)


if __name__ == "__main__":
    app.run(main)
