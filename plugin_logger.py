"""
Remember Last Position - Totem Plugin (see README.md)
Logging interface

Created by Yauhen Lazurkin <foryauhen@gmail.com>
Extended by Liran Funaro <fonaro@gmail.com>

Copyright (C) 2006-2018 Liran Funaro

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import logging
import logging.handlers


def start_logging(log_to_file=False):
    logger = logging.getLogger("totem")
    logger.setLevel(logging.DEBUG)

    if log_to_file:
        handler = logging.FileHandler("/tmp/totem-remember-last-position.log", 'w+')

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        logger.addHandler(handler)
    return logger


plugin_logger = start_logging(True)
