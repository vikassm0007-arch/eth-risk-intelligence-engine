"""
Real-Time Transaction Execution & Database Persistence Runner
EVM Risk Intelligence Platform
"""

import os
import sys
import asyncio
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db import init_db
from backend.main import process_raw_transaction, seed_initial_users
from backend.listener import SyntheticTransactionSimulator

async def run_realtime_ingestion():
    print("=" * 70)
    print("EXECUTING REAL-TIME TRANSACTION INGESTION & PERSISTENCE PROCESS")
    print("=" * 70)

    # Initialize DB & schema
    await init_db()
    await seed_initial_users()

    simulator = SyntheticTransactionSimulator()
    modes = [None, None, "TORNADO_SANCTION", "SUDDEN_DRAIN", "VELOCITY_BURST"]

    print("Streaming and persisting 35 real-time EVM transactions to eth_risk.db...")
    for i in range(35):
        attack_mode = random.choice(modes) if i % 4 == 0 else None
        tx_payload = simulator.generate_transaction(attack_mode=attack_mode)
        res = await process_raw_transaction(tx_payload)
        if (i + 1) % 5 == 0:
            print(f" -> Processed {i + 1}/35 transactions | Mode: {attack_mode or 'NORMAL'}")
        await asyncio.sleep(0.05)

    print("=" * 70)
    print("REAL-TIME TRANSACTION INGESTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_realtime_ingestion())
