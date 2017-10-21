# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017 reverendus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import time
import json
import logging
import threading

import pytz


class Logger:
    _logger = logging.getLogger('keeper')

    def __init__(self,
                 keeper_name: str,
                 chain: str,
                 json_filename: str = None,
                 debug: bool = False,
                 trace: bool = False):
        self.lock = threading.Lock()
        self.keeper_name = keeper_name
        self.chain = chain
        self.json_filename = json_filename
        self._setup_logging(debug, trace)

    def _setup_logging(self, debug: bool, trace: bool):
        # if `--trace` is enabled, we set DEBUG logging level for the root logger
        # which will make us see a lot output from the `urllib3.connectionpool` library etc.
        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                            level=(logging.DEBUG if trace else logging.INFO))

        # if only `--debug` is enabled, we set DEBUG logging level for our own loggers only
        # this significantly limits the output comparing to when `--trace` is enabled
        if debug and not trace:
            self._logger.setLevel(logging.DEBUG)

    def debug(self, msg: str = None, event: dict = None):
        assert(isinstance(msg, str) or msg is None)
        assert(isinstance(event, dict) or event is None)

        with self.lock:
            if msg is not None:
                self._logger.debug(msg)

            self._write_event_as_json("DEBUG", msg, event)

    def info(self, msg: str = None, event: dict = None):
        assert(isinstance(msg, str) or msg is None)
        assert(isinstance(event, dict) or event is None)

        with self.lock:
            if msg is not None:
                self._logger.info(msg)

            self._write_event_as_json("INFO", msg, event)

    def warning(self, msg: str = None, event: dict = None):
        assert(isinstance(msg, str) or msg is None)
        assert(isinstance(event, dict) or event is None)

        with self.lock:
            if msg is not None:
                self._logger.warning(msg)

            self._write_event_as_json("WARNING", msg, event)

    def fatal(self, msg: str = None, event: dict = None):
        assert(isinstance(msg, str) or msg is None)
        assert(isinstance(event, dict) or event is None)

        with self.lock:
            if msg is not None:
                self._logger.fatal(msg)

            self._write_event_as_json("FATAL", msg, event)

    def _event_template(self, level: str, msg: str = None):
        assert(isinstance(level, str))
        assert(isinstance(msg, str) or msg is None)

        return {
            "timestamp": datetime.datetime.now(tz=pytz.utc).isoformat(),
            "source": "keeper",
            "keeperName": self.keeper_name,
            "chain": self.chain,
            "level": level,
            "message": msg
        }

    def _write_event_as_json(self, level: str, msg: str = None, event: dict = None):
        assert(isinstance(level, str))
        assert(isinstance(msg, str) or msg is None)
        assert(isinstance(event, dict) or event is None)

        if self.json_filename is not None:
            if event is None:
                event = {}

            event.update(self._event_template(level, msg))
            with open(self.json_filename, "a") as logfile:
                logfile.write(json.dumps(event) + "\n")


class Event:
    @staticmethod
    def _as_string(value):
        if value is None:
            return None
        elif isinstance(value, bytes):
            return value.decode("utf-8")
        elif isinstance(value, str):
            return value
        else:
            raise Exception(f"Unknown type of {value}")

    @staticmethod
    def transaction_mined(name, transaction, receipt, initial_time, last_time):
        assert(transaction["hash"] is not None)

        event_time = time.time()
        return {
            "eventType": "transactionMined",
            "chainId": transaction["chainId"] if "chainId" in transaction else None,
            "networkId": transaction["networkId"] if "networkId" in transaction else None,
            "blockNumber": transaction["blockNumber"],
            "blockHash": Event._as_string(transaction["blockHash"]),
            "transactionHash": transaction["hash"],
            "transactionName": name,
            "successful": receipt.successful,
            "from": transaction["from"],
            "to": transaction["to"],
            "creates": transaction["creates"] if "creates" in transaction else None,
            "input": Event._as_string(transaction["input"]),
            "raw": transaction["raw"] if "raw" in transaction else None,
            "value": transaction["value"],
            "nonce": transaction["nonce"],
            "startGas": transaction["gas"],
            "gasUsed": receipt.raw_receipt["gasUsed"],
            "gasPrice": transaction["gasPrice"],
            "gasCost": transaction["gasPrice"]*receipt.raw_receipt["gasUsed"],
            "totalConfirmationTime": int(event_time - initial_time),
            "lastConfirmationTime": int(event_time - last_time)
        }

    @staticmethod
    def eth_balance(address, balance):
        return {
            "eventType": "ethBalance",
            "address": address.address.lower(),
            "balance": float(balance)
        }

    @staticmethod
    def token_balance(address, token_address, token_name, balance):
        return {
            "eventType": "tokenBalance",
            "address": address.address.lower(),
            "tokenAddress": token_address.address.lower(),
            "tokenName": token_name,
            "balance": float(balance)
        }
