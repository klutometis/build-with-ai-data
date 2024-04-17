import datetime
import json
import logging
import os
import pprint
from dataclasses import asdict, dataclass
from pathlib import Path

from absl import app
from polygon import RESTClient
from polygon.rest.models.indicators import IndicatorValue, MACDIndicatorValue

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


def get_news(now: str, ticker: str, polygon: RESTClient):
    return [
        news.title
        for news in polygon.list_ticker_news(
            ticker, limit=10, published_utc=now
        )
    ]


def get_ema(now: str, ticker: str, polygon: RESTClient):
    short, *rest = polygon.get_ema(
        ticker=ticker,
        timespan="day",
        window=50,
        series_type="close",
        timestamp=now,
    ).values or [IndicatorValue()]

    long, *rest = polygon.get_ema(
        ticker=ticker,
        timespan="day",
        window=200,
        series_type="close",
        timestamp=now,
    ).values or [IndicatorValue()]

    return (short.value, long.value)


def get_macd(now: str, ticker: str, polygon: RESTClient):
    macd, *rest = polygon.get_macd(
        ticker=ticker,
        timespan="day",
        short_window=12,
        long_window=26,
        signal_window=9,
        series_type="close",
        timestamp=now,
    ).values or [MACDIndicatorValue()]

    return (macd.value, macd.signal)


def get_rsi(now: str, ticker: str, polygon: RESTClient):
    rsi, *rest = polygon.get_rsi(
        ticker=ticker,
        timespan="day",
        window=14,
        series_type="close",
        timestamp=now,
    ).values or [IndicatorValue()]

    return rsi.value


def main(argv):
    logging.basicConfig(level=logging.INFO)
    polygon = RESTClient(params.POLYGON)
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=3)
    current_date = one_year_ago

    data = {}

    while current_date <= today:
        iso = current_date.isoformat()

        ema_short, ema_long = get_ema(iso, TICKER, polygon)
        macd_value, macd_signal = get_macd(iso, TICKER, polygon)

        datum = Datum(
            news=get_news(iso, TICKER, polygon),
            ema_short=ema_short,
            ema_long=ema_long,
            macd_value=macd_value,
            macd_signal=macd_signal,
            rsi=get_rsi(iso, TICKER, polygon),
        )

        logging.info(pprint.pformat(datum))

        data[iso] = asdict(datum)

        current_date += datetime.timedelta(days=1)

    with open(
        Path(os.environ["BUILD_WORKSPACE_DIRECTORY"]) / "data.json", "w"
    ) as f:
        pprint.pp(data)
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    app.run(main)
