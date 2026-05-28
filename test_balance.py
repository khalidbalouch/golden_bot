# test_balance_sync.py — Simple sync test with requests
import hmac, hashlib, time, requests, os
from dotenv import load_dotenv

load_dotenv()


def test_balance():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    base_url = "https://testnet.binancefuture.com"

    if not api_key or not api_secret:
        print("❌ No API keys found")
        return

    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = hmac.new(
        api_secret.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f"{base_url}/fapi/v2/account"
    headers = {"X-MBX-APIKEY": api_key}
    params = {"timestamp": timestamp, "signature": signature}

    print(f"🔗 Testing: {url}")

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"📥 Status: {resp.status_code}")
        print(f"📄 Response: {resp.text[:500]}")

        if resp.status_code == 200:
            data = resp.json()
            for asset in data.get("assets", []):
                if asset.get("asset") == "USDT":
                    balance = float(asset.get("walletBalance", 0))
                    print(f"✅ USDT Balance: ${balance:.2f}")
                    return
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_balance()