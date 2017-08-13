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

import asyncio
import threading


def synchronize(futures) -> list:
    if len(futures) > 0:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(asyncio.gather(*futures, loop=loop))
        finally:
            loop.close()
    else:
        return []


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
    assert(isinstance(value, bytes) or isinstance(value, bytearray))
    return "0x" + "".join(map(lambda b: format(b, "02x"), value))


def hexstring_to_bytes(value: str) -> bytes:
    assert(isinstance(value, str))
    assert(value.startswith("0x"))
    return bytes.fromhex(value.replace("0x", ""))


class AsyncCallback:
    def __init__(self, callback):
        self.callback = callback
        self.thread = None

    def trigger(self) -> bool:
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.callback)
            self.thread.start()
            return True
        else:
            return False

    def wait(self):
        if self.thread is not None:
            self.thread.join()
