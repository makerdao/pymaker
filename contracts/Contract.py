import json
import time


class Contract:

    def _wait_for_receipt(self, transaction_hash):
        while True:
            receipt = self.web3.eth.getTransactionReceipt(transaction_hash)
            if receipt is not None and receipt['blockNumber'] is not None:
                return receipt
            time.sleep(0.25)


    @staticmethod
    def _load_abi(path):
        with open(path) as f:
            abi = json.load(f)
        return abi
