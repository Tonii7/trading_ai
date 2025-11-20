# ==============================================
# src/trading_ai/analytics/statistics.py
# Универсальные функции для анализа рынков
# (волатильность, индикаторы, корреляции, аномалии, бэктест)
# ==============================================

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# TA-индикаторы (по желанию). Нужно: pip install pandas-ta
try:
    import pandas_ta as ta
except ImportError:
    ta = None


# ---------- Базовые структуры ----------

@dataclass
class ReturnStats:
    total_return: float
    annual_return: float
    annual_vol: float
    sharpe: float


@dataclass
class BacktestResult:
    initial_balance: float
    final_balance: float
    total_return_pct: float
    max_drawdown_pct: float
    equity_curve: pd.Series


# ---------- Утилиты для временных рядов ----------

def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Убедиться, что индекс — это datetime (для ресемплинга и т.п.)."""
    if not isinstance(df.index, pd.DatetimeIndex):
        if "Date" in df.columns:
            df = df.copy()
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
        else:
            raise ValueError("DataFrame must have DatetimeIndex or a 'Date' column.")
    return df


# ---------- 1. Волатильность и доходности ----------

def calc_return_stats(
    df: pd.DataFrame,
    price_col: str = "Close",
    periods_per_year: int = 252
) -> ReturnStats:
    """
    Считает базовую статистику по доходностям:
      - общий доход
      - годовой доход
      - годовая волатильность
      - Sharpe ratio (без безрисковой ставки)
    """
    df = ensure_datetime_index(df)
    prices = df[price_col].dropna()

    rets = prices.pct_change().dropna()
    if len(rets) == 0:
        return ReturnStats(0.0, 0.0, 0.0, 0.0)

    total_return = (prices.iloc[-1] / prices.iloc[0] - 1.0) * 100.0
    avg_ret = rets.mean()
    vol = rets.std()

    annual_return = (1 + avg_ret) ** periods_per_year - 1
    annual_vol = vol * np.sqrt(periods_per_year)
    sharpe = annual_return / annual_vol if annual_vol != 0 else 0.0

    return ReturnStats(
        total_return=round(total_return, 2),
        annual_return=round(annual_return * 100.0, 2),
        annual_vol=round(annual_vol * 100.0, 2),
        sharpe=round(sharpe, 2),
    )


def calc_rolling_volatility(
    df: pd.DataFrame,
    price_col: str = "Close",
    window: int = 14,
    periods_per_year: int = 252
) -> pd.Series:
    """
    Скользящая годовая волатильность по окну.
    """
    df = ensure_datetime_index(df)
    rets = df[price_col].pct_change()
    rolling_std = rets.rolling(window).std()
    return rolling_std * np.sqrt(periods_per_year)


# ---------- 2. Технические индикаторы ----------

def add_basic_indicators(
    df: pd.DataFrame,
    price_col: str = "Close",
    volume_col: str = "Volume"
) -> pd.DataFrame:
    """
    Добавляет базовые индикаторы: SMA, EMA, RSI, MACD, Bollinger Bands.
    Требует pandas-ta. Если нет — просто возвращает df.
    """
    df = ensure_datetime_index(df)
    df = df.copy()

    if ta is None:
        # Без pandas_ta просто вернём исходный df
        return df

    close = df[price_col]

    df["SMA_50"] = close.rolling(50).mean()
    df["SMA_200"] = close.rolling(200).mean()

    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()

    df["RSI_14"] = ta.rsi(close, length=14)
    macd_res = ta.macd(close, fast=12, slow=26, signal=9)
    if macd_res is not None and not macd_res.empty:
        df["MACD"] = macd_res.iloc[:, 0]
        df["MACD_signal"] = macd_res.iloc[:, 1]

    bb = ta.bbands(close, length=20, std=2)
    if bb is not None and not bb.empty:
        df["BB_up"] = bb.iloc[:, 0]
        df["BB_mid"] = bb.iloc[:, 1]
        df["BB_low"] = bb.iloc[:, 2]

    if volume_col in df.columns:
        df["Vol_MA_20"] = df[volume_col].rolling(20).mean()

    return df


# ---------- 3. Аномалии объёма и волатильности ----------

def detect_volume_spikes(
    df: pd.DataFrame,
    volume_col: str = "Volume",
    window: int = 30,
    z_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Находит свечи с аномально высоким объёмом по z-score.
    Возвращает df с колонкой volume_zscore и только аномальными строками.
    """
    df = ensure_datetime_index(df)
    df = df.copy()

    if volume_col not in df.columns:
        raise ValueError(f"Column '{volume_col}' not found in DataFrame.")

    rolling_mean = df[volume_col].rolling(window).mean()
    rolling_std = df[volume_col].rolling(window).std()

    df["volume_zscore"] = (df[volume_col] - rolling_mean) / rolling_std
    anomalies = df[df["volume_zscore"] > z_threshold]
    return anomalies


def detect_volatility_shift(
    df: pd.DataFrame,
    price_col: str = "Close",
    recent_window: int = 20,
    past_window: int = 100,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Проверяет, изменилась ли волатильность статистически значимо (t-test)
    между недавним периодом и старым.
    Возвращает (t_stat, p_value).
    """
    df = ensure_datetime_index(df)
    rets = df[price_col].pct_change().dropna()

    if len(rets) < recent_window + past_window:
        return 0.0, 1.0

    recent = rets.tail(recent_window)
    past = rets.head(past_window)

    t_stat, p_val = stats.levene(recent, past)  # критерий Левена по дисперсии
    # p_val < alpha => волатильность изменилась значимо
    return float(t_stat), float(p_val)


# ---------- 4. Корреляции и кросс-активы ----------

def correlation_matrix_from_dict(
    price_series_dict: Dict[str, pd.Series]
) -> pd.DataFrame:
    """
    Из словаря {имя_актива: Series цен} строит матрицу корреляций по дневным доходностям.
    """
    df = pd.DataFrame(price_series_dict)
    # Считаем процентные изменения
    returns = df.pct_change().dropna()
    return returns.corr()


# ---------- 5. Простейший бэктест по сигналам ----------

def simple_signal_backtest(
    df: pd.DataFrame,
    signal_col: str,
    price_col: str = "Close",
    initial_balance: float = 100_000.0,
    fee_per_trade: float = 0.0,
) -> BacktestResult:
    """
    Простейший бэктест: сигнал в колонке signal_col:
      +1 = long, 0 = вне рынка, -1 = шорт (при желании).
    Предполагаем, что весь капитал вкладывается по сигналу.
    """
    df = ensure_datetime_index(df)
    df = df.copy().dropna(subset=[price_col, signal_col])

    prices = df[price_col]
    signals = df[signal_col]

    rets = prices.pct_change().fillna(0.0)

    # Доходность стратегии: позиция * доходность
    strat_rets = signals.shift(1).fillna(0.0) * rets  # входим на следующей свече

    # Учёт комиссий: если сигнал меняется, берём комиссию
    if fee_per_trade > 0.0:
        trades = (signals != signals.shift(1)).astype(float)
        fee_ret = trades * (fee_per_trade / initial_balance) * -1.0
        strat_rets = strat_rets + fee_ret

    equity = (1 + strat_rets).cumprod() * initial_balance

    final_balance = float(equity.iloc[-1])
    total_return_pct = (final_balance / initial_balance - 1.0) * 100.0

    # max drawdown
    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1.0
    max_drawdown_pct = float(drawdown.min() * 100.0)

    return BacktestResult(
        initial_balance=initial_balance,
        final_balance=round(final_balance, 2),
        total_return_pct=round(total_return_pct, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2),
        equity_curve=equity,
    )


# ---------- 6. Генерация текстового резюме ----------

def summarize_asset(
    name: str,
    df: pd.DataFrame,
    price_col: str = "Close",
    volume_col: str = "Volume"
) -> str:
    """
    Делает текстовое резюме по одному активу:
    - текущая цена
    - годовая вола
    - базовая доходность
    - есть ли всплески объёма
    """
    df = ensure_datetime_index(df)
    df = df.dropna(subset=[price_col]).copy()

    stats_ret = calc_return_stats(df, price_col=price_col)

    vol_series = calc_rolling_volatility(df, price_col=price_col)
    last_vol = float(vol_series.dropna().iloc[-1]) * 100.0 if not vol_series.dropna().empty else 0.0

    txt = [f"📊 {name} summary:"]
    txt.append(f"- Current price: {df[price_col].iloc[-1]:.2f}")
    txt.append(f"- Total return: {stats_ret.total_return:.2f}%")
    txt.append(f"- Annual return: {stats_ret.annual_return:.2f}%")
    txt.append(f"- Annual volatility: {stats_ret.annual_vol:.2f}%")
    txt.append(f"- Sharpe (approx): {stats_ret.sharpe:.2f}")
    txt.append(f"- Latest rolling volatility (14d): {last_vol:.2f}%")

    if volume_col in df.columns:
        anomalies = detect_volume_spikes(df, volume_col=volume_col)
        if not anomalies.empty:
            last_spike_date = anomalies.index[-1].date()
            txt.append(f"- Recent volume spike detected on: {last_spike_date}")
        else:
            txt.append("- No strong volume spikes in recent window.")

    return "\n".join(txt)


if __name__ == "__main__":
    # Примитивный тест на случайном ряде (для проверки, что модуль не падает)
    dates = pd.date_range("2024-01-01", periods=200, freq="D")
    prices = pd.Series(np.cumsum(np.random.randn(200)) + 100.0, index=dates)
    volumes = pd.Series(np.random.randint(100, 1000, size=200), index=dates)
    df_test = pd.DataFrame({"Close": prices, "Volume": volumes})

    print("=== Return stats test ===")
    rs = calc_return_stats(df_test)
    print(rs)

    print("\n=== Volume anomalies test ===")
    print(detect_volume_spikes(df_test).tail())

    print("\n=== Summary test ===")
    print(summarize_asset("TEST", df_test))
