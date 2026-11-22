import json
from datetime import datetime, timezone, timedelta
import yfinance as yf

# 港股通自選清單（可自行增減，格式為 4位數代號.HK）
STOCKS = {
    "0700.HK": "騰訊控股",
    "9988.HK": "阿里巴巴-W",
    "3690.HK": "美團-W",
    "1810.HK": "小米集團-W",
    "0941.HK": "中國移動",
    "0883.HK": "中國海洋石油",
    "1211.HK": "比亞迪股份",
    "0388.HK": "香港交易所",
    "0981.HK": "中芯國際",
    "0005.HK": "匯豐控股",
}

def fetch_all():
    results = []
    for symbol, name in STOCKS.items():
        try:
            ticker = yf.Ticker(symbol)
            # 抓取過去 6 個月日線數據以確保足夠計算 MA60
            df = ticker.history(period="6mo", auto_adjust=False)
            if len(df) < 61:
                continue

            df["MA5"] = df["Close"].rolling(window=5).mean()
            df["MA60"] = df["Close"].rolling(window=60).mean()
            df["Diff"] = df["MA5"] - df["MA60"]

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            close_price = round(float(latest["Close"]), 2)
            prev_close = round(float(prev["Close"]), 2)
            change_pct = round(((close_price - prev_close) / prev_close) * 100, 2)
            ma5 = round(float(latest["MA5"]), 2)
            ma60 = round(float(latest["MA60"]), 2)
            diff = round(float(latest["Diff"]), 2)
            prev_diff = float(prev["Diff"])

            # 判斷 MA5 / MA60 狀態與交叉訊號
            if prev_diff <= 0 and diff > 0:
                signal = "黃金交叉 (買)"
            elif prev_diff >= 0 and diff < 0:
                signal = "死亡交叉 (賣)"
            elif diff > 0:
                signal = "多頭排列"
            else:
                signal = "空頭排列"

            results.append({
                "symbol": symbol,
                "name": name,
                "price": close_price,
                "change_pct": change_pct,
                "ma5": ma5,
                "ma60": ma60,
                "diff": diff,
                "signal": signal,
                "date": df.index[-1].strftime("%Y-%m-%d")
            })
        except Exception as e:
            print(f"抓取 {symbol} 失敗: {e}")

    hkt = timezone(timedelta(hours=8))
    output = {
        "updated_at": datetime.now(hkt).strftime("%Y-%m-%d %H:%M:%S HKT"),
        "stocks": results
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_all()
