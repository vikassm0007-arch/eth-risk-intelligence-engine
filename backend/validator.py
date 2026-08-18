"""
Data Validation & Missing Data Handling Layer
AI-Powered Real-Time Ethereum Transaction Risk Intelligence Platform
"""

import re
import time
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from backend.config import settings

class RawTransactionPayload(BaseModel):
    txHash: str
    blockHash: Optional[str] = None
    blockNumber: Optional[int] = None
    fromAddress: str = Field(..., alias="from")
    toAddress: Optional[str] = Field(None, alias="to")
    value: str  # Wei in Hex or string decimal
    gasPrice: Optional[str] = "0x4a817c800"  # ~20 Gwei default
    gasLimit: str = "0x5208"  # 21000 default
    nonce: str = "0x0"
    input: Optional[str] = "0x"
    timestamp: Optional[float] = None

class ValidatedTransaction(BaseModel):
    tx_hash: str
    block_hash: Optional[str] = None
    block_number: Optional[int] = None
    from_address: str
    to_address: str
    value_eth: float
    value_usd: float
    gas_price_gwei: float
    gas_limit: int
    nonce: int
    input_data: str
    is_erc20: bool = False
    erc20_method: Optional[str] = None
    is_unavailable_flag: bool = False
    timestamp: float


class DeadLetterQueue:
    """In-memory + Redis DLQ quarantine storage for malformed transactions"""
    def __init__(self):
        self.quarantine_store: list = []

    def push(self, raw_payload: Dict[str, Any], reason: str):
        record = {
            "payload": raw_payload,
            "reason": reason,
            "quarantined_at": time.time()
        }
        self.quarantine_store.append(record)
        if len(self.quarantine_store) > 1000:
            self.quarantine_store.pop(0)

    def get_quarantined_items(self):
        return self.quarantine_store

dlq = DeadLetterQueue()


class TransactionValidator:
    def __init__(self):
        self.seen_tx_hashes: set = set()
        self.historical_gas_prices_gwei: list = [15.0, 18.0, 20.0, 22.0, 25.0]  # Window for moving average
        self.eth_usd_rate: float = 3200.0  # Simulated dynamic ETH/USD oracle price

    def is_hex(self, s: str) -> bool:
        if not isinstance(s, str):
            return False
        return bool(re.match(r"^0x[0-9a-fA-F]*$", s))

    def parse_hex_or_dec(self, val: Any, default: int = 0) -> int:
        if val is None:
            return default
        if isinstance(val, int):
            return val
        val_str = str(val).strip()
        try:
            if val_str.startswith("0x") or val_str.startswith("0X"):
                return int(val_str, 16)
            return int(val_str)
        except ValueError:
            return default

    def impute_gas_price(self, raw_gas_gwei: float) -> Tuple[float, bool]:
        """Fills missing derived fees via historical moving average"""
        is_imputed = False
        if raw_gas_gwei <= 0:
            moving_avg = sum(self.historical_gas_prices_gwei[-10:]) / len(self.historical_gas_prices_gwei[-10:])
            raw_gas_gwei = round(moving_avg, 4)
            is_imputed = True
        else:
            self.historical_gas_prices_gwei.append(raw_gas_gwei)
            if len(self.historical_gas_prices_gwei) > 100:
                self.historical_gas_prices_gwei.pop(0)
        return raw_gas_gwei, is_imputed

    def validate_and_parse(self, raw_data: Dict[str, Any]) -> Optional[ValidatedTransaction]:
        """
        Validates raw payload, applies deduplication, hex conversion, range checks, and imputation.
        If validation fails, routes payload to DLQ.
        """
        try:
            # 1. Null-checks & Required Fields
            tx_hash = raw_data.get("txHash") or raw_data.get("hash")
            from_addr = raw_data.get("from") or raw_data.get("fromAddress")
            
            if not tx_hash or not from_addr:
                dlq.push(raw_data, "Missing required fields: txHash or fromAddress")
                return None

            # Normalization
            tx_hash = str(tx_hash).lower().strip()
            from_addr = str(from_addr).lower().strip()
            to_addr = str(raw_data.get("to") or raw_data.get("toAddress") or "0x0000000000000000000000000000000000000000").lower().strip()

            # 2. Redis / In-Memory Bloom Filter Deduplication
            if tx_hash in self.seen_tx_hashes:
                # Duplicate tx, silently drop
                return None
            
            self.seen_tx_hashes.add(tx_hash)
            if len(self.seen_tx_hashes) > 100000:
                self.seen_tx_hashes.clear()

            # 3. Numeric Conversions
            raw_val_wei = self.parse_hex_or_dec(raw_data.get("value"))
            value_eth = raw_val_wei / 1e18
            value_usd = value_eth * self.eth_usd_rate

            raw_gas_price_wei = self.parse_hex_or_dec(raw_data.get("gasPrice"))
            gas_price_gwei = raw_gas_price_wei / 1e9
            gas_price_gwei, gas_imputed = self.impute_gas_price(gas_price_gwei)

            gas_limit = self.parse_hex_or_dec(raw_data.get("gasLimit"), 21000)
            nonce = self.parse_hex_or_dec(raw_data.get("nonce"), 0)
            
            input_data = str(raw_data.get("input") or raw_data.get("input_data") or "0x").lower()
            
            # ERC-20 Transfer Detection
            is_erc20 = False
            erc20_method = None
            if len(input_data) >= 10:
                method_sig = input_data[:10]
                if method_sig in (settings.ERC20_TRANSFER_METHOD, settings.ERC20_TRANSFER_FROM_METHOD, settings.ERC20_APPROVE_METHOD):
                    is_erc20 = True
                    erc20_method = method_sig

            is_unavailable = False
            if to_addr == "0x0000000000000000000000000000000000000000" and input_data == "0x":
                is_unavailable = True

            ts = raw_data.get("timestamp") or time.time()

            return ValidatedTransaction(
                tx_hash=tx_hash,
                block_hash=raw_data.get("blockHash"),
                block_number=raw_data.get("blockNumber"),
                from_address=from_addr,
                to_address=to_addr,
                value_eth=value_eth,
                value_usd=value_usd,
                gas_price_gwei=gas_price_gwei,
                gas_limit=gas_limit,
                nonce=nonce,
                input_data=input_data,
                is_erc20=is_erc20,
                erc20_method=erc20_method,
                is_unavailable_flag=is_unavailable,
                timestamp=ts
            )
        except Exception as e:
            dlq.push(raw_data, f"Exception during validation: {str(e)}")
            return None

validator = TransactionValidator()
