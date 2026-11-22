import json
import os
import sys
from datetime import datetime, timezone, timedelta

def main():
    payload = json.loads(os.environ.get("TV_PAYLOAD", "{}"))
    raw_ticker = str(payload.get("ticker", "")).strip()
    signal = payload.get("signal", "黃金交叉 (買)")
    price = payload.get("price")

    if not raw_ticker:
        print("未收到股票代號")
        sys.exit(0)

    # 將 TradingView 代號 (例如 941, 700) 自動補零轉為 0941.HK, 0700.HK
    if raw_ticker.isdigit():
        symbol = f"{raw_ticker.zfill(4)}.HK"
    else:
        symbol = raw_ticker

    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for stock in data.get("stocks", []):
        if stock["symbol"] == symbol:
            stock["signal"] = f"TV {signal}"
            if price is not None:
                stock["price"] = round(float(price), 2)
            updated = True
            break

    if updated:
        hkt = timezone(timedelta(hours=8))
        data["updated_at"] = datetime.now(hkt).strftime("%Y-%m-%d %H:%M:%S HKT (TV同步)")
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已同步更新 {symbol} 訊號為：{signal}")
    else:
        print(f"清單中找不到 {symbol}")

if __name__ == "__main__":
    main()
