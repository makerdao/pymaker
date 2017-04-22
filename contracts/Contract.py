import json


class Contract:

    @staticmethod
    def _load_abi(path):
        with open(path) as f:
            abi = json.load(f)
        return abi
