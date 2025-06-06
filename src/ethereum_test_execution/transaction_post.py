"""Simple transaction-send then post-check execution format."""

from typing import ClassVar, List

import pytest

from ethereum_test_base_types import Alloc, Hash
from ethereum_test_forks import Fork
from ethereum_test_rpc import EngineRPC, EthRPC, SendTransactionExceptionError
from ethereum_test_types import Transaction

from .base import BaseExecute


class TransactionPost(BaseExecute):
    """Represents a simple transaction-send then post-check execution format."""

    blocks: List[List[Transaction]]
    post: Alloc

    format_name: ClassVar[str] = "transaction_post_test"
    description: ClassVar[str] = (
        "Simple transaction sending, then post-check after all transactions are included"
    )

    def execute(self, fork: Fork, eth_rpc: EthRPC, engine_rpc: EngineRPC | None):
        """Execute the format."""
        assert not any(tx.ty == 3 for block in self.blocks for tx in block), (
            "Transaction type 3 is not supported in execute mode."
        )
        for block in self.blocks:
            if any(tx.error is not None for tx in block):
                for transaction in block:
                    if transaction.error is None:
                        eth_rpc.send_wait_transaction(transaction.with_signature_and_sender())
                    else:
                        with pytest.raises(SendTransactionExceptionError):
                            eth_rpc.send_transaction(transaction.with_signature_and_sender())
            else:
                eth_rpc.send_wait_transactions([tx.with_signature_and_sender() for tx in block])

        for address, account in self.post.root.items():
            balance = eth_rpc.get_balance(address)
            code = eth_rpc.get_code(address)
            nonce = eth_rpc.get_transaction_count(address)
            if account is None:
                assert balance == 0, f"Balance of {address} is {balance}, expected 0."
                assert code == b"", f"Code of {address} is {code}, expected 0x."
                assert nonce == 0, f"Nonce of {address} is {nonce}, expected 0."
            else:
                if "balance" in account.model_fields_set:
                    assert balance == account.balance, (
                        f"Balance of {address} is {balance}, expected {account.balance}."
                    )
                if "code" in account.model_fields_set:
                    assert code == account.code, (
                        f"Code of {address} is {code}, expected {account.code}."
                    )
                if "nonce" in account.model_fields_set:
                    assert nonce == account.nonce, (
                        f"Nonce of {address} is {nonce}, expected {account.nonce}."
                    )
                if "storage" in account.model_fields_set:
                    for key, value in account.storage.items():
                        storage_value = eth_rpc.get_storage_at(address, Hash(key))
                        assert storage_value == value, (
                            f"Storage value at {key} of {address} is {storage_value},"
                            f"expected {value}."
                        )
