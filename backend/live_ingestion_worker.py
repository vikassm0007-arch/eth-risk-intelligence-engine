"""
Live Ethereum Web3 Async WebSocket Ingestion Worker
AI-Powered Real-Time EVM Risk Intelligence Platform
"""

import json
import asyncio
import time
import logging
from typing import Callable, Optional, Dict, Any

from web3 import AsyncWeb3
from web3.providers import AsyncBaseProvider
from backend.oracle_service import oracle_service

logger = logging.getLogger("LiveWeb3Ingestion")
logging.basicConfig(level=logging.INFO)

# Public Live Ethereum Mainnet WebSocket RPC Endpoints
PUBLIC_WS_RPCS = [
    "wss://ethereum-rpc.publicnode.com",
    "wss://eth.drpc.org",
    "wss://rpc.payload.de"
]

class LiveWeb3IngestionWorker:
    """
    Async Web3 WebSocket Ingestion Worker.
    Streams real-time live Ethereum mempool and block transactions directly into the Risk Engine.
    Features automatic RPC reconnection with exponential backoff and contract creation filtering.
    """
    def __init__(self, callback: Callable[[Dict[str, Any]], Any]):
        self.callback = callback
        self.is_running: bool = False
        self.w3: Optional[AsyncWeb3] = None
        self.active_rpc_index: int = 0
        self.processed_tx_count: int = 0

    async def connect_web3(self) -> Optional[AsyncWeb3]:
        """Attempts connection to active public WebSocket RPC endpoint."""
        for attempt in range(len(PUBLIC_WS_RPCS)):
            rpc_url = PUBLIC_WS_RPCS[self.active_rpc_index]
            try:
                logger.info(f"Connecting to Live Ethereum WebSocket RPC: {rpc_url}")
                w3 = AsyncWeb3(AsyncWeb3.WebSocketProvider(rpc_url))
                if await w3.is_connected():
                    logger.info(f"Successfully connected to Ethereum RPC ({rpc_url})")
                    return w3
            except Exception as e:
                logger.warning(f"RPC connection failed for {rpc_url}: {e}")
                self.active_rpc_index = (self.active_rpc_index + 1) % len(PUBLIC_WS_RPCS)
                await asyncio.sleep(1.0)
        return None

    async def start(self):
        """Main lifecycle loop with exponential backoff reconnection logic."""
        self.is_running = True
        backoff_seconds = 2.0

        while self.is_running:
            try:
                self.w3 = await self.connect_web3()
                if not self.w3:
                    logger.warning("All public RPC nodes unreachable. Retrying in background...")
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds = min(60.0, backoff_seconds * 1.5)
                    continue

                backoff_seconds = 2.0  # Reset backoff on successful connection
                await self._listen_mempool_stream()

            except Exception as e:
                logger.error(f"Live Web3 Ingestion loop error: {e}. Reconnecting in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(60.0, backoff_seconds * 1.5)

    async def _listen_mempool_stream(self):
        """Listens for newHeads / pending transaction hashes and dispatches task workers."""
        if not self.w3:
            return

        # Subscribe to new block headers for real-time mined transaction ingestion
        subscription_id = await self.w3.eth.subscribe("newHeads")
        logger.info(f"Subscribed to live Ethereum block stream (ID: {subscription_id})")

        async for block_header in self.w3.eth.listen(subscription_id):
            if not self.is_running:
                break
            
            block_number = block_header.get("number")
            if block_number:
                # Spawn non-blocking background task to process full block transactions
                asyncio.create_task(self._process_block_transactions(block_number))

    async def _process_block_transactions(self, block_number: int):
        """Fetches full block details and dispatches transactions to Risk Engine."""
        try:
            block = await self.w3.eth.get_block(block_number, full_transactions=True)
            if not block or "transactions" not in block:
                return

            inr_rate, usd_rate = await oracle_service.fetch_live_rates()

            for tx in block["transactions"][:15]:  # Process top 15 transactions per block
                # Filter null / contract creation transactions
                to_addr = tx.get("to")
                if not to_addr:
                    continue  # Gracefully skip contract creation transactions without crashing

                tx_hash_hex = tx["hash"].hex() if hasattr(tx["hash"], "hex") else str(tx["hash"])
                from_addr_hex = str(tx["from"]).lower()
                to_addr_hex = str(to_addr).lower()
                val_wei = int(tx.get("value", 0))
                val_eth = oracle_service.wei_to_eth(val_wei)
                gas_price_gwei = float(tx.get("gasPrice", 20000000000)) / 1e9
                gas_limit = int(tx.get("gas", 21000))

                val_inr = oracle_service.calculate_inr_value(val_eth, inr_rate)
                gas_inr = oracle_service.calculate_gas_inr(gas_price_gwei, gas_limit, inr_rate)

                raw_payload = {
                    "hash": tx_hash_hex,
                    "tx_hash": tx_hash_hex,
                    "blockNumber": block_number,
                    "block_number": block_number,
                    "from": from_addr_hex,
                    "from_address": from_addr_hex,
                    "to": to_addr_hex,
                    "to_address": to_addr_hex,
                    "value": hex(val_wei),
                    "value_wei": val_wei,
                    "value_eth": val_eth,
                    "value_usd": round(val_eth * usd_rate, 2),
                    "value_inr": val_inr,
                    "gasPrice": hex(int(gas_price_gwei * 1e9)),
                    "gas_price_gwei": gas_price_gwei,
                    "gas_inr": gas_inr,
                    "gas": hex(gas_limit),
                    "nonce": hex(int(tx.get("nonce", 0))),
                    "input": tx.get("input", "0x").hex() if hasattr(tx.get("input"), "hex") else str(tx.get("input", "0x")),
                    "timestamp": time.time()
                }

                self.processed_tx_count += 1
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(raw_payload)
                else:
                    self.callback(raw_payload)

        except Exception as e:
            logger.debug(f"Block transaction fetch error: {e}")

    def stop(self):
        """Stops live ingestion worker loop."""
        self.is_running = False
        logger.info("Stopped Live Ethereum Web3 Ingestion Worker.")
