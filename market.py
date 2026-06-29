"""Market data helpers: TradingView technical analysis + real-time price.
- TA via `tradingview-ta` (pure-Python, Termux-friendly), imported lazily so the
  bot still runs even if the package is not installed yet.
- Price via Binance public REST API (no key needed)."""
import requests

_INTERVAL_KEYS = {
    "1m": "INTERVAL_1_MINUTE",
    "5m": "INTERVAL_5_MINUTES",
    "15m": "INTERVAL_15_MINUTES",
    "30m": "INTERVAL_30_MINUTES",
    "1h": "INTERVAL_1_HOUR",
    "2h": "INTERVAL_2_HOURS",
    "4h": "INTERVAL_4_HOURS",
    "1d": "INTERVAL_1_DAY",
    "1w": "INTERVAL_1_WEEK",
    "1M": "INTERVAL_1_MONTH",
}


def get_ta(symbol, interval="1h", exchange="BINANCE", screener="crypto"):
    """Return a formatted TradingView technical-analysis summary (Markdown)."""
    try:
        from tradingview_ta import TA_Handler, Interval
    except ImportError:
        return (
            "\u26a0\ufe0f *Library `tradingview-ta` belum terinstal.*\n\n"
            "Jalankan di Termux:\n"
            "```bash\npip install tradingview-ta\n```\n"
            "atau `pip install -r requirements.txt`, lalu coba lagi."
        )

    itv = getattr(Interval, _INTERVAL_KEYS.get(interval, "INTERVAL_1_HOUR"))
    handler = TA_Handler(
        symbol=symbol.upper(),
        exchange=exchange.upper(),
        screener=screener.lower(),
        interval=itv,
    )
    a = handler.get_analysis()
    s = a.summary
    ind = a.indicators

    emoji = {"STRONG_BUY": "\U0001f7e2\U0001f7e2", "BUY": "\U0001f7e2",
             "NEUTRAL": "\u26aa", "SELL": "\U0001f534",
             "STRONG_SELL": "\U0001f534\U0001f534"}
    rec = s.get("RECOMMENDATION", "NEUTRAL")

    price = ind.get("close")
    rsi = ind.get("RSI")
    macd = ind.get("MACD.macd")

    txt = (
        f"\U0001f4ca *Analisa Teknikal TradingView*\n"
        f"*{symbol.upper()}* \u00b7 `{exchange.upper()}` \u00b7 TF `{interval}`\n\n"
        f"{emoji.get(rec, '\u26aa')} *Rekomendasi:* `{rec}`\n\n"
        f"\U0001f4c8 *Ringkasan Sinyal:*\n"
        f"\u2022 Beli: `{s.get('BUY', 0)}`  |  Jual: `{s.get('SELL', 0)}`  |  Netral: `{s.get('NEUTRAL', 0)}`\n\n"
        f"\U0001f50d *Indikator Kunci:*\n"
        f"\u2022 Harga: `{price}`\n"
        f"\u2022 RSI(14): `{round(rsi, 2) if rsi is not None else 'N/A'}`\n"
        f"\u2022 MACD: `{round(macd, 4) if macd is not None else 'N/A'}`\n\n"
        f"_Sumber: TradingView \u2014 bukan saran finansial._"
    )
    return txt


def get_price(symbol):
    """Return formatted real-time price + 24h stats from Binance (Markdown)."""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    r = requests.get(url, params={"symbol": symbol.upper()}, timeout=20)
    r.raise_for_status()
    d = r.json()

    last = float(d["lastPrice"])
    change = float(d["priceChangePercent"])
    high = float(d["highPrice"])
    low = float(d["lowPrice"])
    vol = float(d["quoteVolume"])
    arrow = "\U0001f4c8" if change >= 0 else "\U0001f4c9"
    sign = "+" if change >= 0 else ""

    txt = (
        f"\U0001f4b0 *Harga Real-Time* \u00b7 Binance\n"
        f"*{symbol.upper()}*\n\n"
        f"{arrow} *Harga:* `{last:,.4f}`\n"
        f"\U0001f4ca *24j:* `{sign}{change:.2f}%`\n"
        f"\U0001f53c *High:* `{high:,.4f}`\n"
        f"\U0001f53d *Low:* `{low:,.4f}`\n"
        f"\U0001f4a7 *Volume:* `{vol:,.0f}`\n\n"
        f"_Sumber: Binance \u2014 bukan saran finansial._"
    )
    return txt
