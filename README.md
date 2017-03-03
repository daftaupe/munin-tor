munin-tor
=========

Munin plugin to render various values taken from the a tor daemon.

Requires the stem library (https://stem.torproject.org/).

Resolve dependencies for example by using pip:
`pip install -r requirements.txt`

#### tor_bandwidth
![alt_tor_bandwidth](https://cloud.githubusercontent.com/assets/22810624/23546800/85d9da72-0001-11e7-8577-a1697b14c68b.png)
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_bandwidth`

#### tor_connections
![alt tor_connections](https://i.imgur.com/LAkcKD0.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_connections`

#### tor_countries
![alt tor_countries](http://i.imgur.com/6bVsHrN.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_countries`

#### tor_dormant
![alt tor_dormant](http://i.imgur.com/UCQr6MX.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_dormant`

#### tor_flags
![alt_tor_flags](https://cloud.githubusercontent.com/assets/22810624/23546797/835729b2-0001-11e7-9d25-2b3cae4ace8e.png)
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_flags`

#### tor_traffic
![alt tor_traffic](https://i.imgur.com/YXLZHGa.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_traffic`

#### Using password authentication

Create a hashed password:

    $ tor --hash-password MyVeryStrongPassword

Add the hashed password to /etc/tor/torrc and reload Tor:

    HashedControlPassword 16:<long_hex_string>

Create /etc/munin/plugin-conf.d/tor_

    [tor_*]
    env.torpassword MyVeryStrongPassword

#### Configuring the connection to Tor

By default, the plugin connects to Tor using TCP on port 9051. This can be
changed by setting env.port.

The plugin can also connect using a socket file. This is done by setting
env.connectmethod to 'socket'. The default path for the socket file is
/var/run/tor/control, but it can be changed using env.socket.



#### Adding new graphs
You can query infos from the tor daemon via its GETINFO¹ command. The get_info.py script helps you to look up the return values/format quickly, to see if the desired information can be efficiently extracted.

[1] 3.9 GETINFO - https://gitweb.torproject.org/torspec.git/blob/HEAD:/control-spec.txt
