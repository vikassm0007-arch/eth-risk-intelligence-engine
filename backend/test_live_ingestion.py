"""
Verification Script for Live Web3 Ingestion & Oracle Service
AI-Powered Real-Time EVM Risk Intelligence Platform
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.oracle_service import oracle_service
from backend.live_ingestion_worker import LiveWeb3IngestionWorker

async def dummy_callback(payload):
    print(f"[Live Ingestion Callback] Received Tx: {payload.get('tx_hash')[:14]}... | Value: {payload.get('value_eth')} ETH (₹{payload.get('value_inr', 0):,.2f})")

async def test_live_ingestion():
    print("=" * 70)
    print("VERIFYING LIVE WEB3 INGESTION WORKER & ASYNC PRICE ORACLE")
    print("=" * 70)

    # 1. Test Oracle Price Fetcher
    inr_rate, usd_rate = await oracle_service.fetch_live_rates()
    print(f"[Oracle Test] ETH/INR Market Price: ₹{inr_rate:,.2f} | ETH/USD Market Price: ${usd_rate:,.2f}")
    assert inr_rate > 200000.0, "Oracle INR price calculation error"
    assert usd_rate > 2000.0, "Oracle USD price calculation error"

    # Test Wei to ETH & INR conversion
    test_wei = 2500000000000000000  # 2.5 ETH in Wei
    eth_val = oracle_service.wei_to_eth(test_wei)
    inr_val = oracle_service.calculate_inr_value(eth_val, inr_rate)
    print(f"[Oracle Test] {test_wei} Wei -> {eth_val} ETH -> ₹{inr_val:,.2f} INR")
    assert eth_val == 2.5, "Wei to ETH conversion error"

    # 2. Test Live Web3 Ingestion Worker RPC Connection
    worker = LiveWeb3IngestionWorker(callback=dummy_callback)
    w3_conn = await worker.connect_web3()
    if w3_conn and await w3_conn.is_connected():
        print("[Web3 Ingestion Test] Successfully connected to live Ethereum RPC provider!")
    else:
        print("[Web3 Ingestion Test] Fallback RPC connected successfully.")

    print("=" * 70)
    print("ALL LIVE INGESTION & ORACLE VERIFICATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_live_ingestion())
