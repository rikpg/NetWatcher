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


DEFAULT_PREFS = {
    "ip_addresses": [],
    "check_rate": 10,   # minutes
    "custom_log": False,
    "log_dir": os.path.expanduser('~'),
}


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
            file_path = os.path.join(self.config["log_dir"], 'netwatcher.log')
            fh = logging.FileHandler(file_path)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter("[%(asctime)s] %(message)s",
                                          datefmt="%b-%d %H:%M")
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        self.do_schedule()

    def disable(self):
        self.timer.cancel()

    def update(self):
        pass

    @staticmethod
    def regulate_torrents(scan_result):
        """Resume/Pause all torrents if `scan_result` is 'Free'/'Busy'."""
        for torrent in component.get("Core").torrentmanager.torrents.values():
            status = torrent.get_status([])     # empty keys -> full status
            if scan_result == 'Busy' and status['state'] != 'Paused':
            #if scan_result == 'Busy' and not status['paused']:
                msg = ("Pausing {status[name]!r} from state: {status[state]}"
                      .format(status=status))
                log.info(msg)
                logger.info(msg)

                torrent.pause()

            elif scan_result == 'Free' and status['state'] == 'Paused':
                msg = ("Resuming {status[name]!r} from state: {status[state]}"
                      .format(status=status))
                log.info(msg)
                logger.info(msg)

                torrent.resume()

    def do_schedule(self, timer=True):
        """Schedule of network scan and subsequent torrent regulation."""
        d = self._quick_scan()
        d.addCallback(self.regulate_torrents)

        if timer:
            self.timer = reactor.callLater(self.config["check_rate"] * 60,
                                           self.do_schedule)

    def _quick_scan(self):
        """Return 'Busy' if any of the known addresses is alive, 'Free'
        otherwise.

        The scan is performed through ping requests.

        """
        # Ping exit codes:
        # 0 - the address is alive (online)
        # 1 - the address is not alive (offline)
        # 2 - an error occured
        log.debug("spawning ping requests to all known addresses..")
        options = "{} -c1 -w1 -q"
        outputs = [utils.getProcessValue("ping", options.format(addr).split())
                   for addr in self.config["ip_addresses"]]

        # XXX: the following two lines will shadow ping errors (exit == 2)
        d = defer.gatherResults(outputs)
        d.addCallback(lambda x: 'Free' if all(x) else 'Busy')

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
