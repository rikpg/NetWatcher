#
# core.py
#
# Copyright (C) 2009 Riccardo Poggi <rik.poggi@gmail.com>
#
# Basic plugin template created by:
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007-2009 Andrew Resch <andrewresch@gmail.com>
# Copyright (C) 2009 Damien Churchill <damoxc@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import deluge.configmanager
from deluge.core.rpcserver import export
from twisted.internet import reactor, utils, defer

import os.path
import re

DEFAULT_PREFS = {
    "scan_type": "Complete Scan",
    "ip_addresses": [],
    "check_rate": 5,   # minutes
    "custom_log": False,
    "log_dir": os.path.expanduser('~'),
    "download_limit": 0,    # zero as dl limit means pausing
    "upload_limit": 0,
}

CONTROLLED_SETTINGS = [
    "max_download_speed",
    "max_upload_speed"
]


# custom logging
import logging
logger = logging.getLogger("NetWatcher")
logger.parent = 0
logger.setLevel(logging.INFO)


class Core(CorePluginBase):

    def enable(self):
        self.config = deluge.configmanager.ConfigManager("netwatcher.conf",
                                                         DEFAULT_PREFS)

        if self.config["custom_log"]:
            #TODO: The changes are applied at startup, so there's need for
            #      a restart in order to log correctly
            file_path = os.path.join(self.config["log_dir"], 'netwatcher_log.txt')
            fh = logging.FileHandler(file_path)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter("[%(asctime)s] %(message)s",
                                          datefmt="%b-%d %H:%M")
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        else:
            logger.addHandler(logging.NullHandler())

        logger.info('## Starting New Session ##')

        self.do_schedule()

    def disable(self):
        try:
            self.timer.cancel()
        except AttributeError:
            pass
        self.__apply_set_functions()

    def update(self):
        pass

    def __apply_set_functions(self):
        """Have the core apply its bandwidth settings as specified in core.conf.
        """
        core_config = deluge.configmanager.ConfigManager("core.conf")
        for setting in CONTROLLED_SETTINGS:
            core_config.apply_set_functions(setting)
        # Resume the session if necessary
        component.get("Core").session.resume()

    def regulate_torrents(self, scan_result):
        """Regulate torrents activity depending on `scan_result` string value,
        either 'Free' or 'Busy'.

        With the max download speed parameter set to either 0 or -1 torrents
        will be paused, otherwise the global max download/upload rate will be
        accordingly limited.
        """
        session = component.get("Core").session
        if scan_result == 'Free':
            session.set_download_rate_limit(-1)
            session.set_upload_rate_limit(-1)
            self._wake_torrents()
            return

        if int(self.config["download_limit"]) == 0:
            session.set_download_rate_limit(-1)
            session.set_upload_rate_limit(-1)
            self._sleep_torrents()
        else:
            # here self.config["download_limit"] is > than 0
            session.set_download_rate_limit(int(self.config["download_limit"] * 1024))
            session.set_upload_rate_limit(int(self.config["upload_limit"] * 1024))
            self._wake_torrents()

    @staticmethod
    def _wake_torrents():
        for torrent in component.get("Core").torrentmanager.torrents.values():
            status = torrent.get_status([])     # empty keys -> full status
            if status['state'] == 'Paused':
                msg = ("Resuming '{status[name]}' from state: {status[state]}"
                      .format(status=status))
                log.info(msg)
                logger.info(msg)

                torrent.resume()

    @staticmethod
    def _pause_torrents():
        for torrent in component.get("Core").torrentmanager.torrents.values():
            status = torrent.get_status([])     # empty keys -> full status
            if status['state'] != 'Paused':
                msg = ("Pausing '{status[name]}' from state: {status[state]}"
                      .format(status=status))
                log.info(msg)
                logger.info(msg)

                torrent.pause()

    def do_schedule(self, timer=True):
        """Schedule of network scan and subsequent torrent regulation."""
        if self.config["scan_type"] == "Complete Scan":
            d = self.complete_scan()
        elif self.config["scan_type"] == "Quick Scan":
            d = self.quick_scan()
        else:
            log.warning("Not expected scan_type option.")

        d.addCallback(self.regulate_torrents)

        if timer:
            self.timer = reactor.callLater(self.config["check_rate"] * 60,
                                           self.do_schedule)

    def quick_scan(self):
        """Performing a scan only on the addresses specified from the gui."""
        log.info("performing a quick scan...")
        return self._scan(self.config["ip_addresses"])

    def complete_scan(self):
        """Performing a complete scan on the range 192.168.1.2-255."""
        log.info("performing a complete scan...")
        d = self._find_my_ip_addr()
        # building the complete range of ip-addr to be scanned: 192.168.1.2-255
        d.addCallback(lambda x: ['192.168.1.{}'.format(i)
                                 for i in xrange(2, 256) if i != int(x)])
        d.addCallback(self._scan)
        return d

    @staticmethod
    def _scan(addr_list):
        """Return 'Busy' if any of the adreesses in `addr_list` is alive, 'Free'
        otherwise.

        The scan is performed through ping requests.
        """
        # Ping exit codes:
        # 0 - the address is alive (online)
        # 1 - the address is not alive (offline)
        # 2 - an error occured
        log.debug("spawning ping requests...")
        options = "{} -c1 -w1 -q"
        outputs = [utils.getProcessValue("ping", options.format(addr).split())
                   for addr in addr_list]

        # XXX: the following two lines will shadow ping errors (exit == 2)
        d = defer.gatherResults(outputs)
        d.addCallback(lambda x: 'Free' if all(x) else 'Busy')
        return d

    @staticmethod
    def _find_my_ip_addr(pattern=re.compile("inet addr:(192.168.1.(\d+))")):
        """Find the machine ip-addr on which the deluge client is running."""
        d = utils.getProcessOutput("/sbin/ifconfig")
        d.addCallback(lambda s: pattern.search(s).group(2))
        return d

    @export
    def set_config(self, config):
        """Sets the config dictionary"""
        for key in config.keys():
            self.config[key] = config[key]
        self.config.save()

        self.timer.cancel()
        self.do_schedule()

    @export
    def get_config(self):
        """Returns the config dictionary"""
        return self.config.config
