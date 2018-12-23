"""
Remember Last Position - Totem Plugin (see README.md)

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
try:
    # Python 3
    from configparser import ConfigParser
except:
    # Python 2
    from ConfigParser import ConfigParser


import os
import sys
from ast import literal_eval
from pprint import pprint
from collections import OrderedDict
from threading import Timer

from gi.repository import GLib, GObject, Peas, Totem

from plugin_logger import plugin_logger


def normalize_path(path):
    """
    :param path: A path
    :return: A normalize path
    """
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    path = os.path.normcase(path)
    path = os.path.realpath(path)
    path = os.path.normpath(path)
    return path


def get_module_path():
    """
    :return: The current module path
    """
    module = sys.modules[__name__]
    module_file = normalize_path(module.__file__)
    path, file_name = os.path.split(module_file)
    name, ext = os.path.splitext(file_name)
    return path, name


class RememberLastPositionPlugin(GObject.Object, Peas.Activatable):
    __gtype_name__ = 'RememberLastPositionPlugin'

    object = GObject.property(type=GObject.Object)

    default_conf = {
        'load-on-start': False,
        'load-on-start-delay': 5,
        'history-length': 20,
        'update-interval': 3,
    }

    def __init__(self):
        GObject.Object.__init__(self)
        self.data_folder, self.name = get_module_path()
        self.data_path = os.path.join(self.data_folder, "%s.pydata" % self.name)
        self.conf_path = os.path.join(self.data_folder, "%s.conf" % self.name)

        self.current_file = None
        self.current_time = 0

        self._totem = None

        self.config = ConfigParser(defaults=self.default_conf)
        self.load_on_start = None
        self.load_on_start_delay = None
        self.history_length = None
        self.update_interval = None

        self.update_time_timer = None
        self.restore_last_file_timer = None

        self.__data_queue__ = None

    ###########################################################################
    # Configuration
    ###########################################################################

    def load_config(self):
        """ Load configuration from conf file """
        try:
            self.config.read(self.conf_path)
        except Exception as e:
            plugin_logger.exception("Failed to read config file: %s", e)

    def read_config_value(self, key, cfg_type=int):
        """ Read specific value from the configuration """
        try:
            val = self.config.get('DEFAULT', key)
            val = cfg_type(val)
            if cfg_type == int:
                assert val > 0
            return val
        except Exception as e:
            plugin_logger.warning("Failed to read config value: %s", e)
            return self.defaults_conf[key]

    ###########################################################################
    # Totem plugin methods
    ###########################################################################

    def do_activate(self):
        self._totem = self.object

        self.load_config()
        self.load_on_start = self.read_config_value('load-on-start', lambda x: x == 'true' or x == '1')
        self.load_on_start_delay = self.read_config_value('load-on-start-delay')
        self.history_length = self.read_config_value('history-length')
        self.update_interval = self.read_config_value('update-interval')

        # Register handlers
        self._totem.connect('file-closed', self.on_file_closed)
        self._totem.get_main_window().connect('destroy', self.on_file_closed)
        self._totem.connect('file-has-played', self.on_file_played)
        self._totem.connect('file-opened', self.on_file_opened)

        # Attempt to restore the last played file
        if self.load_on_start:
            self.delayed_restore_last_file()

    def do_deactivate(self):
        self._totem = None

    ###########################################################################
    # Handlers
    ###########################################################################

    def on_file_opened(self, _to, file_path):
        self.cancel_restore_last_file()
        self.stop_update_current_time()
        self.current_file = file_path
        self.current_time = self.last_time

    def on_file_played(self, _to, _file_path):
        self.go_to_last_position()
        self.start_update_current_time()

    def on_file_closed(self, _to):
        self.stop_update_current_time()
        self.set_time(self.current_file, self.current_time)
        self.current_file = None
        self.current_time = 0

    ###########################################################################
    # Handlers Helpers
    ###########################################################################

    def go_to_last_position(self):
        """ Attempts to seek to the last known time of the opened file """
        if not self.last_time:
            return

        def go_to_last_position_thread(totem, last_time):
            if not last_time:
                return False
            if not totem.is_seekable():
                # Wait for the object to be seekable
                return True

            # Seek to the last known time (False: force accurate seek)
            totem.seek_time(last_time, True)
            return False

        # Run on a different thread to avoid delay
        GLib.timeout_add(50, go_to_last_position_thread, self._totem, self.last_time)

    def update_current_time(self):
        """ Read the current seek position """
        try:
            self.current_time = self._totem.get_property('current_time')
        except Exception as e:
            plugin_logger.warning("Failed to read current time: %s", e)

    def start_update_current_time(self):
        """ Read the current seek position in intervals """
        self.update_time_timer = Timer(self.update_interval, self.start_update_current_time)
        self.update_time_timer.start()
        self.update_current_time()

    def stop_update_current_time(self):
        """ Stop the update seek position timer """
        if self.update_time_timer is None:
            return

        try:
            self.update_time_timer.cancel()
        except Exception as e:
            plugin_logger.warning("Failed to stop update: %s", e)

    def restore_last_file(self):
        """ Restore the last played file """
        last_file = self.last_file()
        if not last_file:
            return
        self._totem.remote_command(Totem.RemoteCommand.REPLACE, last_file)

    def delayed_restore_last_file(self):
        """ Restore the last played file in delay """
        self.restore_last_file_timer = Timer(self.load_on_start_delay, self.restore_last_file)
        self.restore_last_file_timer.start()

    def cancel_restore_last_file(self):
        """ Cancel the timer for restore last file """
        if self.restore_last_file_timer is None:
            return

        try:
            self.restore_last_file_timer.cancel()
        except Exception as e:
            plugin_logger.warning("Failed to cancel restore: %s", e)

    ###########################################################################
    # Data Queue
    ###########################################################################

    @property
    def data_queue(self):
        """ Read the data queue property from a file """
        if self.__data_queue__ is None:
            try:
                self.__data_queue__ = self.__read_data_queue()
            except Exception as e:
                plugin_logger.warning("Failed to read data queue from file: %s", e)
                self.__data_queue__ = self.__default_data_queue()

        return self.__data_queue__

    def last_file(self):
        """ Retrieve the last file that was played """
        if not self.data_queue:
            return None
        try:
            return next(reversed(self.data_queue))
        except Exception as e:
            plugin_logger.warning("Failed to read last file from queue: %s", e)
            return None

    @property
    def last_time(self):
        """ Retrieve the last seek position of the current file """
        if self.current_file:
            return self.get_time(self.current_file)
        else:
            return None

    def get_time(self, file_name):
        """ Retrieve the last seek position of a specific file """
        return self.data_queue.get(file_name, None)

    def set_time(self, file_name, file_time):
        """ Set the last known seek position of a specific file and write it """
        if not file_name or file_time <= 0:
            return

        self.data_queue.pop(file_name, None)
        self.data_queue[file_name] = file_time
        if len(self.data_queue) > self.history_length:
            self.data_queue.popitem(last=False)
        self.__write_data_queue()

    ###########################################################################
    # Data Queue Helpers
    ###########################################################################

    @staticmethod
    def __default_data_queue(*args, **kwargs):
        return OrderedDict(*args, **kwargs)

    def __read_data_queue(self):
        with open(self.data_path, 'r') as f:
            list_data_queue = literal_eval(f.read())

        return self.__default_data_queue(list_data_queue)

    def __write_data_queue(self):
        if not os.path.isdir(self.data_folder):
            os.makedirs(self.data_folder)

        list_data_queue = list(self.data_queue.items())
        with open(self.data_path, 'w+') as f:
            pprint(list_data_queue, f)
