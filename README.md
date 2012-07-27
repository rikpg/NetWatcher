=================
Deluge NetWatcher
=================

_NetWatcher_ is a plugin for the [Deluge bittorrent client](http://deluge-torrent.org/) that pause/resume all torrents if there is someone connected to the same network.

Features:

- Set a custom ip list.
- Set the check rate.
- Option to enable logging to a file.


Usage
-----

### Ip Addresses

Insert a list of comma separated ip addresses in the __Ip Addresses__ field, like `192.168.1.45, 192.168.1.128, 192.168.1.149`, and these addresses will be cheked every X minutes.

Working rationale as follow:

- At least one ip address is on-line => pause all
- All the ip-addresses are off-line => resume all

**Note:** The ip-addresses status is checked through ping requests.

### Custom logging

It's also possibile to log the NetWatcher activity into a file.

Other than knowing what happend when we weren't at the computer, the use of this feature combined with a Dropbox-like service makes it very easy to monitor torrents status without having to access the web-interface.  
To support this combined usage the log extension is `.txt`.


Install the plugin
------------------

There are various ways to do it:

1. Download the egg from [here](https://github.com/rikpg/NetWatcher/downloads) and follow one of [these instructions](http://dev.deluge-torrent.org/wiki/Plugins#InstallingPlugins).

2. Or download the source code (available [here](https://github.com/rikpg/NetWatcher)), build the egg and then copy it in the deluge _plugins_ directory:

        $ python setup.py bdist_egg
        $ cp dist/*.egg ~/.config/deluge/plugins

3. Or like a developer, link to the egg with setuptools develop command:

        $ python setup.py develop -mxd ~/.config/deluge/plugins
