"""
Data Collection & Hybrid Stream Listener (Live Web3 Ingestion + Attack Simulator)
AI-Powered Real-Time EVM Risk Intelligence Platform
"""

import asyncio
import random
import time
import secrets
from typing import Dict, Any, Callable, List, Optional
from backend.config import settings
from backend.live_ingestion_worker import LiveWeb3IngestionWorker

MOCK_WALLETS = [
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    "0x28c6c06298d514db089934071355e5743bf21d60",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
    "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "0x50ec05b22530c029787a74797089408b8b981504",
    "0x1111111254fb6c44bac0bed2854e76f90643097d",
    "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b",
    "0x3cffd56b47b7b41c56258d9c7731abdc360e0739",
]

class SyntheticTransactionSimulator:
    def __init__(self):
        self.block_number = 19500000

    def generate_random_address(self) -> str:
        return "0x" + secrets.token_hex(20)

    def generate_transaction(self, attack_mode: Optional[str] = None) -> Dict[str, Any]:
        self.block_number += random.choice([0, 0, 1])
        tx_hash = "0x" + secrets.token_hex(32)

        if attack_mode == "TORNADO_SANCTION":
            from_addr = self.generate_random_address()
            to_addr = "0xd90e2f925da726b50c4ed8d0fb90ad053324f31b"
            val_wei = hex(int(10 * 1e18))
            gas_price = hex(int(120 * 1e9))
            input_data = "0xb214faa5000000000000000000000000"
        elif attack_mode == "SUDDEN_DRAIN":
            from_addr = self.generate_random_address()
            to_addr = self.generate_random_address()
            val_wei = hex(int(95 * 1e18))
            gas_price = hex(int(180 * 1e9))
            input_data = "0x"
        elif attack_mode == "VELOCITY_BURST":
            from_addr = "0x50ec05b22530c029787a74797089408b8b981504"
            to_addr = self.generate_random_address()
            val_wei = hex(int(0.5 * 1e18))
            gas_price = hex(int(45 * 1e9))
            input_data = "0xa9059cbb000000000000000000000000"
        else:
            from_addr = random.choice(MOCK_WALLETS[:7])
            to_addr = random.choice(MOCK_WALLETS[:7])
            val_wei = hex(int(random.uniform(0.01, 3.5) * 1e18))
            gas_price = hex(int(random.uniform(15, 30) * 1e9))
            input_data = random.choice(["0x", "0xa9059cbb000000000000000000000000", "0x38ed1739"])

        return {
            "txHash": tx_hash,
            "blockHash": "0x" + secrets.token_hex(32),
            "blockNumber": self.block_number,
            "from": from_addr,
            "to": to_addr,
            "value": val_wei,
            "gasPrice": gas_price,
            "gasLimit": hex(21000 if input_data == "0x" else 150000),
            "nonce": hex(random.randint(1, 200)),
            "input": input_data,
            "timestamp": time.time()
        }


class EthereumStreamListener:
    """
    Hybrid Real-Time Stream Listener.
    Launches live Web3 WebSocket Ingestion Worker alongside background attack scenario injection.
    """
    def __init__(self, callback: Callable[[Dict[str, Any]], Any]):
        self.callback = callback
        self.is_running = False
        self.simulator = SyntheticTransactionSimulator()
        self.live_worker = LiveWeb3IngestionWorker(callback=self.callback)

    async def start(self):
        self.is_running = True
        print("Starting Ethereum Real-Time Stream Listener & Live Web3 Ingestion...")

        # 1. Launch Live Web3 RPC WebSocket Ingestion Task
        asyncio.create_task(self.live_worker.start())

        # 2. Baseline Attack Simulator Loop
        while self.is_running:
            try:
                raw_tx = self.simulator.generate_transaction()
                
                if random.random() < 0.15:
                    attack_type = random.choice(["TORNADO_SANCTION", "SUDDEN_DRAIN", "VELOCITY_BURST"])
                    raw_tx = self.simulator.generate_transaction(attack_mode=attack_type)

                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(raw_tx)
                else:
                    self.callback(raw_tx)

                await asyncio.sleep(random.uniform(0.4, 0.9))
            except Exception as e:
                print(f"Stream simulation loop error: {e}")
                await asyncio.sleep(1.0)

    def stop(self):
        self.is_running = False
        self.live_worker.stop()

simulator = SyntheticTransactionSimulator()
