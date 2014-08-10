=================
Deluge NetWatcher
=================

_NetWatcher_ is a plugin for the [Deluge bittorrent client](http://deluge-torrent.org/) that can limits the torrent activity in case other ip-addresses were to be found connected on the same network.

Features:

- Ip-adress scanning.  
  With either one of the following options:
    1. Complete scan on the range `192.168.1.2-255`.
    2. Quick scan only on a specific list of ip-addresses.
- Set the checking rate.
- Set up/download speed limits.
- Option to enable logging to a file.


Usage
-----

Working rationale as follow:

- At least one ip-address is on-line => apply restrictions
- All the ip-addresses are off-line => resume all

### Quick Scan

A list of comma separated ip-addresses can be inserted in the __Ip Addresses__ field (e.g., `192.168.1.45, 192.168.1.128, 192.168.1.149`). These addresses only (and no others) will be cheked every X minutes.

### Complete Scan

A complete scan on the range `192.168.1.2-255` will be performed every X minutes.

**Note:** In both cases the ip-addresses will be checked through ping requests.

### Bandwidth Limits

A value of 0 will cause the torrents to be paused in case of a _busy_ network. Otherwise the setted limits will be applied.

### Custom logging

It's also possibile to log the NetWatcher activity into a file.

This might come in handy if combined with a Dropbox-like service, making it very easy to monitor the torrents status without having to access the web-interface. For this reason the log-file format is `.txt`.


Installation
------------

1. Download the source code (available [here](https://github.com/rikpg/NetWatcher)):

        $ git clone git@github.com:rikpg/NetWatcher.git

2. Build the egg and copy it into the deluge _plugins_ directory:

        $ cd NetWatcher
        $ python setup.py bdist_egg
        $ cp dist/*.egg ~/.config/deluge/plugins

__For developers:__

As an alternative to copying, the egg can be linked with the following setuptools develop command:

        $ python setup.py develop -mxd ~/.config/deluge/plugins

----

Development
-----------

The Netwatcher source code is [hosted on GitHub](https://github.com/rikpg/NetWatcher) and documented at my best ;)

Please feel free to submit Pull Requests and report bugs on the [issue tracker](https://github.com/rikpg/NetWatcher/issues).
