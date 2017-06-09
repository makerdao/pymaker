import json
import pkg_resources
import time


class Contract:

    def _assert_contract_exists(self, web3, address):
        code = web3.eth.getCode(address.address)
        if (code == "0x") or (code is None):
            raise Exception(f"No contract found at {address}")

    def _wait_for_receipt(self, transaction_hash):
        while True:
            receipt = self._web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            time.sleep(0.25)

    @staticmethod
    def _has_any_log_message(receipt):
        receipt_logs = receipt['logs']
        return (receipt_logs is not None) and (len(receipt_logs) > 0)

    @staticmethod
    def _load_abi(package, resource):
        return json.loads(pkg_resources.resource_string(package, resource))
