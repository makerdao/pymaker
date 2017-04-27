import json
import pkg_resources
import time


class Contract:

    def _wait_for_receipt(self, transaction_hash):
        while True:
            receipt = self._web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            time.sleep(0.25)

    @staticmethod
    def _load_abi(package, resource):
        return json.loads(pkg_resources.resource_string(package, resource))
