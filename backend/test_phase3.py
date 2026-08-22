"""
Verification Script for Phase 3: INR Localization, Persistent History & REST APIs
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.currency_service import currency_service
from backend.db import init_db, AsyncSessionLocal, TransactionsHistoryModel, RiskExplanationsModel, WalletProfilesModel
from sqlalchemy import select, func

import time

async def test_phase3():
    print("=" * 70)
    print("VERIFYING PHASE 3 INR LOCALIZATION & PERSISTENT HISTORY ENGINE")
    print("=" * 70)

    # 1. Test INR Currency Engine
    rate = await currency_service.get_eth_inr_rate()
    print(f"[INR Test] Current ETH/INR Exchange Rate: {currency_service.format_inr(rate)} / ETH")

    val_eth = 1.25
    val_inr = currency_service.convert_eth_to_inr(val_eth, rate)
    formatted = currency_service.format_inr(val_inr)
    print(f"[INR Test] {val_eth} ETH -> {formatted} ({val_inr} INR)")
    assert val_inr > 300000.0, "INR conversion error"

    # Test Lakh & Crore Formatting
    crore_fmt = currency_service.format_inr(15000000.0)
    lakh_fmt = currency_service.format_inr(450000.0)
    print(f"[INR Test] Formatting Check: 1.5 Cr -> '{crore_fmt}', 4.5 Lakh -> '{lakh_fmt}'")
    assert "Cr" in crore_fmt and "Lakh" in lakh_fmt, "Indian formatting error"

    # 2. Test DB Persistence Models
    unique_tx = f"0xphase3_test_tx_hash_{int(time.time() * 1000)}"
    unique_wallet = f"0x{int(time.time()*1000):040x}"[:42]
    await init_db()
    async with AsyncSessionLocal() as session:
        # Seed test history record
        test_tx = TransactionsHistoryModel(
            tx_hash=unique_tx,
            block_number=19283746,
            from_addr=unique_wallet,
            to_addr="0x2222222222222222222222222222222222222222",
            value_eth=50.0,
            value_inr=13750000.0,
            gas_price_gwei=25.0,
            gas_inr=275.0,
            risk_score=94.5,
            risk_level="CRITICAL"
        )
        session.add(test_tx)

        exp = RiskExplanationsModel(
            tx_hash=unique_tx,
            feature_name="High INR Volume (> ₹1 Cr)",
            shap_value=0.45,
            explanation_text="Transaction value ₹1.38 Cr exceeds ₹1 Crore threshold"
        )
        session.add(exp)

        w_prof = WalletProfilesModel(
            address=unique_wallet,
            total_tx_count=5,
            high_risk_tx_count=2,
            total_volume_inr=25000000.0,
            is_sanctioned=True
        )
        session.add(w_prof)
        await session.commit()

        # Query back
        res = await session.execute(select(func.count(TransactionsHistoryModel.id)))
        count = res.scalar()
        print(f"[DB Test] Total Historical Audit Logs Saved: {count}")
        assert count > 0, "DB persistent history failed"

    print("=" * 70)
    print("ALL PHASE 3 INR LOCALIZATION & DB PERSISTENCE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_phase3())
