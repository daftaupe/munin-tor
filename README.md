munin-tor
=========

## Description

Munin plugin to render various values taken from the a tor daemon.

## Requirements

Requires the stem library (https://stem.torproject.org/).

Resolve dependencies for example by using pip:
`pip install -r requirements.txt`

## Usage

First you have to clone the repository somewhere.

    $ cd /somewhere && git clone https://github.com/daftaupe/munin-plugins-tor.git
    
Then you have to copy the files where your munin installation expects them, and finally "activate them".

    $ cd /somewhere/munin-plugins-tor
    $ # On CentOS for example
    $ cp tor_ /usr/share/munin/plugins
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_bandwidth
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_connections
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_countries
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_dormant
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_flags
    $ ln -s /usr/share/munin/tor_ /etc/munin/plugins/tor_traffic
   
When this is done, you need to configure the way the tor plugin for munin will behave. There are several parameters that can be modified.
In order to do this you have to create a file in /etc/munin/plugin-conf.d/tor or the equivalent location on your system. It has to be filled in this way.

    $ cat /etc/munin/plugin-conf.d/tor
    [tor_*]
    env.user toranon
    env.torpassword mypassword
    env.torcachedir /tmp

When this is configured as required you can test the plugin that the plugin is working the way it should with the following command :

    # In order to test tor_connections, adapt to the desired plugin.
    $ munin-run tor_connections
    new.value 45
    connected.value 4555
    closed.value 0
    launched.value 8
    failed.value 0


## Configuration

What can be modified is below.

#### Connection method to the Tor daemon

By default, the plugin connects to Tor using TCP on port 9051. This can be
changed by setting env.port.

The plugin can also connect using a socket file. This is done by setting
env.connectmethod to 'socket'. The default path for the socket file is
/var/run/tor/control, but it can be changed using env.socket.

So basically either you have :
    
    # if you need to change the regular Tor port
    env.port 9052 

    # if you need to connect via a socket
    env.connectmethod socket
    # if you need to change the socket path
    env.socket /var/run/tor/changedcontrol

#### Using password authentication

Create a hashed password:

    $ tor --hash-password MyVeryStrongPassword

Add the hashed password to /etc/tor/torrc and reload Tor:

    HashedControlPassword 16:<long_hex_string>

Specify your password in the config file of the plugin

    env.torpassword MyVeryStrongPassword


## Examples

#### Adding new graphs
You can query infos from the tor daemon via its GETINFO¹ command. The get_info.py script helps you to look up the return values/format quickly, to see if the desired information can be efficiently extracted.

#### tor_bandwidth
![alt tor_bandwidth](https://cloud.githubusercontent.com/assets/22810624/23546800/85d9da72-0001-11e7-8577-a1697b14c68b.png)  
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
![alt tor_flags](https://cloud.githubusercontent.com/assets/22810624/23546797/835729b2-0001-11e7-9d25-2b3cae4ace8e.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_flags`

#### tor_traffic
![alt tor_traffic](https://i.imgur.com/YXLZHGa.png)  
`ln -s /usr/share/munin/plugins/tor_ /etc/munin/plugins/tor_traffic`



[1] 3.9 GETINFO - https://gitweb.torproject.org/torspec.git/blob/HEAD:/control-spec.txt
