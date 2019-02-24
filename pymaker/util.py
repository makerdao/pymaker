# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2017-2018 reverendus
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

import asyncio
import logging
import threading

from web3 import Web3

from pymaker.numeric import Wad


def chain(web3: Web3) -> str:
    block_0 = web3.eth.getBlock(0)['hash']
    if block_0 == "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3":
        return "ethlive"
    elif block_0 == "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9":
        return "kovan"
    elif block_0 == "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d":
        return "ropsten"
    elif block_0 == "0x0cd786a2425d16f152c658316c423e6ce1181e15c3295826d7c9904cba9ce303":
        return "morden"
    else:
        return "unknown"


def http_response_summary(response) -> str:
    text = response.text.replace('\r', '').replace('\n', '')[:2048]
    return f"{response.status_code} {response.reason} ({text})"


def synchronize(futures) -> list:
    if len(futures) > 0:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(asyncio.gather(*futures, loop=loop))
        finally:
            loop.close()
    else:
        return []


def eth_balance(web3: Web3, address) -> Wad:
    return Wad(web3.eth.getBalance(address.address))


def is_contract_at(web3: Web3, address):
    code = web3.eth.getCode(address.address)
    return (code is not None) and (code != "0x") and (code != "0x0") and (code != b"\x00") and (code != b"")


def int_to_bytes32(value: int) -> bytes:
    assert(isinstance(value, int))
    return value.to_bytes(32, byteorder='big')


def bytes_to_int(value) -> int:
    if isinstance(value, bytes) or isinstance(value, bytearray):
        return int.from_bytes(value, byteorder='big')
    elif isinstance(value, str):
        b = bytearray()
        b.extend(map(ord, value))
        return int.from_bytes(b, byteorder='big')
    else:
        raise AssertionError


def bytes_to_hexstring(value) -> str:
    if isinstance(value, bytes) or isinstance(value, bytearray):
        return "0x" + "".join(map(lambda b: format(b, "02x"), value))
    elif isinstance(value, str):
        b = bytearray()
        b.extend(map(ord, value))
        return "0x" + "".join(map(lambda b: format(b, "02x"), b))
    else:
        raise AssertionError


def hexstring_to_bytes(value: str) -> bytes:
    assert(isinstance(value, str))
    assert(value.startswith("0x"))
    return Web3.toBytes(hexstr=value)


class AsyncCallback:
    """Decouples callback invocation from the web3.py filter.

    Decouples callback invocation from the web3.py filter by executing the callback
    in a dedicated thread. If we make web3.py trigger the callback directly, and the callback
    execution takes more than 60 seconds, the `eth_getFilterChanges` call also will not
    get called for 60 seconds and more which will make the filter expire in Parity side.
    It's 60 seconds for Parity, this could be a different value for other nodes,
    but the filter will eventually expire sooner or later anyway.

    Invoking the callback logic in a separate thread allows the web3.py Filter thread
    to keep calling `eth_getFilterChanges` regularly, so the filter stays active.

    Attributes:
        callback: The callback function to be invoked in a separate thread.
    """
    def __init__(self, callback):
        self.callback = callback
        self.thread = None

    def trigger(self, on_start=None, on_finish=None) -> bool:
        """Invokes the callback in a separate thread, unless one is already running.

        If callback isn't currently running, invokes it in a separate thread and returns `True`.
        If the previous callback invocation still hasn't finished, doesn't do anything
        and returns `False`.

        Arguments:
            on_start: Optional method to be called before the actual callback. Can be `None`.
            on_finish: Optional method to be called after the actual callback. Can be `None`.

        Returns:
            `True` if callback has been invoked, or if it invocation attempt failed.
            `False` if the previous callback invocation still hasn't finished.
        """
        if self.thread is None or not self.thread.is_alive():
            def thread_target():
                if on_start is not None:
                    on_start()
                self.callback()
                if on_finish is not None:
                    on_finish()

            self.thread = threading.Thread(target=thread_target)

            try:
                self.thread.start()
            except Exception as e:
                self.thread = None

                logging.critical(f"Failed to start the async callback thread ({e})")

            return True
        else:
            return False

    def wait(self):
        """Waits for the currently running callback to finish.

        If the callback isn't running or hasn't even been invoked once, returns instantly."""
        if self.thread is not None:
            self.thread.join()
