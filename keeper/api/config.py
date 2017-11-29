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

import _jsonnet
import json

import zlib

from keeper import Logger


class ReloadableConfig:
    def __init__(self, filename: str, logger: Logger):
        assert(isinstance(filename, str))
        assert(isinstance(logger, Logger))

        self.filename = filename
        self.logger = logger
        self._checksum = None

    def get_config(self) -> dict:
        with open(self.filename) as data_file:
            content_file = data_file.read()
            content_config = _jsonnet.evaluate_snippet("snippet", content_file, ext_vars={})
            result = json.loads(content_config)

            # Report if file has been newly loaded or reloaded
            checksum = zlib.crc32(content_config.encode('utf-8'))
            if self._checksum is None:
                self.logger.info(f"Loaded configuration from '{self.filename}'")
                self.logger.debug(f"Config file is: " + json.dumps(result, indent=4))
            elif self._checksum != checksum:
                self.logger.info(f"Reloaded configuration from '{self.filename}'")
                self.logger.debug(f"Reloaded config file is: " + json.dumps(result, indent=4))
            self._checksum = checksum

            return result
