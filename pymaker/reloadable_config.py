# This file is part of Maker Keeper Framework.
#
# Copyright (C) 2020 MikeHathaway
#
# This is proprietary (closed source) software. Unauthorized copying,
# distributing, downloading, sharing, conveying, modifying, or use, via any
# medium or in any manner whatsoever are strictly prohibited.  No license or
# any other rights are provided with this file.

import json
import _jsonnet
import logging
import os
import zlib

from typing import Optional, List


class ReloadableConfig:
    """Reloadable JSON config file reader.

    This reader will always read most up-to-date version of the config file from disk
    on each call to `get_config()`. In addition to that, whenever the config file changes,
    a log event is emitted.

    Attributes:
        filename: Filename of the configuration file.
    """

    logger = logging.getLogger('reloadable-config')

    def __init__(self, filename: str):
        assert(isinstance(filename, str))

        self.filename = filename
        self._checksum = None
        self._checksum_config = None
        self._config = None
        self._mtime = None
        self._imported_paths_to_mtimes = {}

    def _import_callback(self, paths: list):

        def callback(path, file):
            abs_path = os.path.join(os.path.dirname(self.filename), file)
            paths.append(abs_path)

            with open(abs_path) as file_obj:
                return file, file_obj.read()

        return callback

    def _load_mtimes(self, imported_paths: List[str]) -> dict:
        return {path: os.path.getmtime(path) for path in imported_paths}

    def _mtimes_changed(self, imported_paths_to_mtimes: dict) -> bool:
        try:
            return any(os.path.getmtime(path) != mtime for path, mtime in imported_paths_to_mtimes.items())

        except:
            return True

    def get_config(self):
        """Reads the JSON config file from disk and returns it as a Python object.

        Returns:
            Current configuration as a `dict` or `list` object.
        """

        mtime = os.path.getmtime(self.filename)

        # If the modification time has not changed since the last time we have read the file,
        # we return the last content without opening and parsing it. It saves us around ~ 30ms.
        #
        # Ultimately something like `watchdog` (<https://pythonhosted.org/watchdog/index.html>)
        # should be used to watch the filesystem changes asynchronously.
        if self._config is not None and self._mtime is not None:
            if mtime == self._mtime \
                    and not self._mtimes_changed(self._imported_paths_to_mtimes):
                return self._config

        with open(self.filename) as data_file:
            content_file = data_file.read()
            imported_paths = []

            content_config = _jsonnet.evaluate_snippet("snippet", content_file, ext_vars={},
                                                       import_callback=self._import_callback(imported_paths))
            result = None
            try:
                result = json.loads(content_config)
            except ValueError as ex:
                logging.error(f"Failed to read config: {ex}")
                raise ex

            # Report if file has been newly loaded or reloaded
            checksum = zlib.crc32(content_file.encode('utf-8'))
            checksum_config = zlib.crc32(content_config.encode('utf-8'))

            if self._checksum is None:
                self.logger.info(f"Loaded configuration from '{self.filename}'")
                self.logger.debug(f"Config file is: " + json.dumps(result, indent=4))
            elif self._checksum != checksum:
                self.logger.info(f"Reloaded configuration from '{self.filename}'")
                self.logger.debug(f"Reloaded config file is: " + json.dumps(result, indent=4))
            elif self._imported_paths_to_mtimes != self._load_mtimes(imported_paths):
                self.logger.info(f"Reloaded configuration from '{self.filename}' (due to imported file changed)")
                self.logger.debug(f"Reloaded config file is: " + json.dumps(result, indent=4))
            elif self._checksum_config != checksum_config:
                self.logger.debug(f"Parsed configuration from '{self.filename}'")
                self.logger.debug(f"Parsed config file is: " + json.dumps(result, indent=4))

            self._checksum = checksum
            self._checksum_config = checksum_config
            self._config = result
            self._mtime = mtime
            self._imported_paths_to_mtimes = self._load_mtimes(imported_paths)

            return result
