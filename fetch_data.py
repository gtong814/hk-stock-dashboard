import json
import time
from datetime import datetime, timezone, timedelta
import akshare as ak
import yfinance as yf
import pandas as pd

def get_hk_connect_stocks():
    """自動抓取最新港股通成分股名單"""
    try:
        df = ak.stock_hk_ggt_components_em()
        stocks = {}
        for _, row in df.iterrows():
            raw_code = str(row["代码"]).strip()
            name = str(row["名称"]).strip()
            if raw_code.isdigit():
                # 轉換為 Yahoo Finance 格式（例如 00700 -> 0700.HK）
                symbol = f"{str(int(raw_code)).zfill(4)}.HK"
                stocks[symbol] = name
        if stocks:
            print(f"成功抓取 {len(stocks)} 隻港股通股份")
            return stocks
    except Exception as e:
        print(f"自動抓取港股通名單失敗，改用預設清單: {e}")

    # 備用預設清單（萬一外部接口暫時無法連線）
    return {
        "0700.HK": "騰訊控股", "9988.HK": "阿里巴巴-W", "3690.HK": "美團-W",
        "1810.HK": "小米集團-W", "0941.HK": "中國移動", "0883.HK": "中國海洋石油",
        "1211.HK": "比亞迪股份", "0388.HK": "香港交易所", "0981.HK": "中芯國際",
        "0005.HK": "匯豐控股", "9660.HK": "地平線機器人-W", "0020.HK": "商湯-W",
        "9880.HK": "優必選", "9698.HK": "萬國數據-SW", "0522.HK": "ASMPT"
    }

def fetch_all():
    stocks_dict = get_hk_connect_stocks()
    symbols = list(stocks_dict.keys())
    results = []

    # 每次批次下載 50 隻，避免 Yahoo Finance 限流
    batch_size = 50
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        try:
            data = yf.download(
                batch,
                period="6mo",
                auto_adjust=False,
                group_by="ticker",
                threads=True,
                progress=False
            )
        except Exception as e:
            print(f"批次 {i} 下載失敗: {e}")
            continue

        for symbol in batch:
            try:
                df = data[symbol].dropna(subset=["Close"]) if len(batch) > 1 else data.dropna(subset=["Close"])
                if len(df) < 61:
                    continue

                close_series = df["Close"]
                ma5_series = close_series.rolling(window=5).mean()
                ma60_series = close_series.rolling(window=60).mean()
                diff_series = ma5_series - ma60_series

                close_price = round(float(close_series.iloc[-1]), 2)
                prev_close = round(float(close_series.iloc[-2]), 2)
                change_pct = round(((close_price - prev_close) / prev_close) * 100, 2)
                ma5 = round(float(ma5_series.iloc[-1]), 2)
                ma60 = round(float(ma60_series.iloc[-1]), 2)
                diff = round(float(diff_series.iloc[-1]), 2)
                prev_diff = float(diff_series.iloc[-2])

                if prev_diff <= 0 and diff > 0:
                    signal = "黃金交叉 (買)"
                    priority = 1
                elif prev_diff >= 0 and diff < 0:
                    signal = "死亡交叉 (賣)"
                    priority = 2
                elif diff > 0:
                    signal = "多頭排列"
                    priority = 3
                else:
                    signal = "空頭排列"
                    priority = 4

                results.append({
                    "symbol": symbol,
                    "name": stocks_dict[symbol],
                    "price": close_price,
                    "change_pct": change_pct,
                    "ma5": ma5,
                    "ma60": ma60,
                    "diff": diff,
                    "signal": signal,
                    "priority": priority,
                    "date": df.index[-1].strftime("%Y-%m-%d")
                })
            except Exception:
                continue

        time.sleep(1)  # 批次之間稍微停頓

    # 排序：將「黃金交叉 (買)」和「死亡交叉 (賣)」排在最前面，其餘按漲跌幅由高至低排列
    results.sort(key=lambda x: (x["priority"], -x["change_pct"]))

    hkt = timezone(timedelta(hours=8))
    output = {
        "updated_at": datetime.now(hkt).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "total": len(results),
        "stocks": results
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_all()
