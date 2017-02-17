#!/usr/bin/python2

from __future__ import print_function
from collections import Counter
from stem import CircStatus
from stem.control import Controller
#from tor_ import TorPlugin, authenticate, gen_controller
import os
import sys
import stem
import stem.control
import argparse
import json


#try:
#    import stem
#    from stem.control import Controller
#except ImportError:
#    print('no (tor-munin requires the stem library from https://stem.torproject.org.)')
#    sys.exit()


DEFAULT_GEOIP_PATH = "/usr/share/GeoIP/GeoIP.dat"
CACHE_FNAME = 'munin_tor_country_stats.json'


def simplify(cn):
    """Simplify country name"""
    cn = cn.replace(' ', '_')
    cn = cn.replace("'", '_')
    cn = cn.split(',', 1)[0]
    return cn

def get_info(query, port=9051, socket='/var/run/tor/control', connect_method='port'):
    if connect_method == 'port':
        def gen_controller():
            return stem.control.Controller.from_port(port=port)
    elif connect_method == 'socket':
        def gen_controller():
            return stem.control.Controller.from_socket_file(path=socket)
    else:
        raise ValueError("env.connectmethod contains in invalid value. Please specify either 'port' or 'socket'.")

    with gen_controller() as controller:
        controller.authenticate()

        try:
            response = controller.get_info(query)
            print(response)
        except stem.InvalidArguments as e:
            print("{}".format(e))

'''
 Here be dragons
'''

#%# family=auto
#%# capabilities=autoconf suggest


class ConnectionError(Exception):
    """Error connecting to the controller"""


class AuthError(Exception):
    """Error authenticating to the controller"""


def authenticate(controller):
    try:
        controller.authenticate()
        return
    except stem.connection.MissingPassword:
        pass

    try:
        password = os.environ['torpassword']
    except KeyError:
        raise AuthError("Please configure the 'torpassword' "
                        "environment variable")

    try:
        controller.authenticate(password=password)
    except stem.connection.PasswordAuthFailed:
        print("Authentication failed (incorrect password)")


def gen_controller():
    connect_method = os.environ.get('connectmethod', 'port')

    if connect_method == 'port':
        return Controller.from_port(port=int(os.environ.get('port', 9051)))
    elif connect_method == 'socket':
        return Controller.from_socket_file(path=os.environ.get('socket', '/var/run/tor/control'))
    else:
        print("env.connectmethod contains an invalid value. Please specify either 'port' or 'socket'.", file=sys.stderr)
        sys.exit(-1)


#########################
# Base Class
#########################


class TorPlugin(object):
    def __init__(self):
        raise NotImplementedError

    def conf(self):
        raise NotImplementedError

    @staticmethod
    def conf_from_dict(graph, labels):
        # header
        for key, val in graph.iteritems():
            print('graph_{} {}'.format(key, val))
        # values
        for label, attributes in labels.iteritems():
            for key, val in attributes.iteritems():
                print('{}.{} {}'.format(label, key, val))

    @staticmethod
    def autoconf():
        try:
            with gen_controller() as controller:
                try:
                    authenticate(controller)
                    print('yes')
                except stem.connection.AuthenticationFailure as e:
                    print('no (Authentication failed: {})'.format(e))

        except stem.connection:
            print('no (Connection failed)')

    @staticmethod
    def suggest():
        options = ['connections', 'traffic', 'dormant', 'bandwidth', 'flags', 'countries']
        ##tc = circuits_by_country.TorCountries()
	#TorCountries is always available now, because it is included in the tor_.py file
        #tc = TorCountries()
        #if tc.available:
        #    options.append('countries')

        for option in options:
            print(option)

    def fetch(self):
        raise NotImplementedError


##########################
# Child Classes
##########################

class TorConnections(TorPlugin):
    def __init__(self):
        pass

    def conf(self):
        graph = {'title': 'Connections',
                 'args': '-l 0 --base 1000',
                 'vlabel': 'connections',
                 'category': 'Tor',
                 'info': 'OR connections by state'}
        labels = {'new': {'label': 'new', 'min': 0, 'max': 25000, 'type': 'GAUGE'},
                  'launched': {'label': 'launched', 'min': 0, 'max': 25000, 'type': 'GAUGE'},
                  'connected': {'label': 'connected', 'min': 0, 'max': 25000, 'type': 'GAUGE'},
                  'failed': {'label': 'failed', 'min': 0, 'max': 25000, 'type': 'GAUGE'},
                  'closed': {'label': 'closed', 'min': 0, 'max': 25000, 'type': 'GAUGE'}}

        TorPlugin.conf_from_dict(graph, labels)

    def fetch(self):
        with gen_controller() as controller:
            try:
                authenticate(controller)

                response = controller.get_info('orconn-status', None)
                if response is None:
                    print("No response from Tor daemon in TorConnection.fetch()", file=sys.stderr)
                    sys.exit(-1)
                else:
                    connections = response.split('\n')
                    states = dict((state, 0) for state in stem.ORStatus)
                    for connection in connections:
                        states[connection.rsplit(None, 1)[-1]] += 1
                    for state, count in states.iteritems():
                        print('{}.value {}'.format(state.lower(), count))
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))


class TorDormant(TorPlugin):
    def __init__(self):
        pass

    def conf(self):
        graph = {'title': 'Dormant',
                 'args': '-l 0 --base 1000',
                 'vlabel': 'dormant',
                 'category': 'Tor',
                 'info': 'Is Tor not building circuits because it is idle?'}
        labels = {'dormant': {'label': 'dormant', 'min': 0, 'max': 1, 'type': 'GAUGE'}}

        TorPlugin.conf_from_dict(graph, labels)

    def fetch(self):
        with gen_controller() as controller:
            try:
                #controller.authenticate()
                authenticate(controller)

                response = controller.get_info('dormant', None)
                if response is None:
                    print("Error while reading dormant state from Tor daemon", file=sys.stderr)
                    sys.exit(-1)
                print('dormant.value {}'.format(response))
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))


class TorTraffic(TorPlugin):
    def __init__(self):
        pass

    def conf(self):
        graph = {'title': 'Traffic',
                 'args': '-l 0 --base 1024',
                 'vlabel': 'data',
                 'category': 'Tor',
                 'info': 'bytes read/written'}
        labels = {'read': {'label': 'read', 'min': 0, 'type': 'DERIVE'},
                  'written': {'label': 'written', 'min': 0, 'type': 'DERIVE'}}

        TorPlugin.conf_from_dict(graph, labels)

    def fetch(self):
        with gen_controller() as controller:
            try:
                authenticate(controller)
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))
                return

            response = controller.get_info('traffic/read', None)
            if response is None:
                print("Error while reading traffic/read from Tor daemon", file=sys.stderr)
                sys.exit(-1)

            print('read.value {}'.format(response))

            response = controller.get_info('traffic/written', None)
            if response is None:
                print("Error while reading traffic/write from Tor daemon", file=sys.stderr)
                sys.exit(-1)
            print('written.value {}'.format(response))


class TorBandwidth(TorPlugin):
    def __init__(self):
        pass

    def conf(self):
        graph = {'title': 'Observed bandwidth',
                 'args': '-l 0 --base 1000',
                 'vlabel': 'bytes/s',
                 'category': 'Tor',
                 'info': 'estimated capacity based on usage in bytes/s'}
        labels = {'bandwidth': {'label': 'bandwidth', 'min': 0, 'type': 'GAUGE'}}

        TorPlugin.conf_from_dict(graph, labels)

    def fetch(self):
        with gen_controller() as controller:
            try:
                authenticate(controller)
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))
                return

            # Get fingerprint of our own relay to look up the descriptor for.
            # In Stem 1.3.0 and later, get_server_descriptor() will fetch the
            # relay's own descriptor if no argument is provided, so this will
            # no longer be needed.
            fingerprint = controller.get_info('fingerprint', None)
            if fingerprint is None:
                print("Error while reading fingerprint from Tor daemon", file=sys.stderr)
                sys.exit(-1)

            response = controller.get_server_descriptor(fingerprint, None)
            if response is None:
                print("Error while getting server descriptor from Tor daemon", file=sys.stderr)
                sys.exit(-1)
            print('bandwidth.value {}'.format(response.observed_bandwidth))


class TorFlags(TorPlugin):
    def __init__(self):
        pass

    def conf(self):
        graph = {'title': 'Relay flags',
                 'args': '-l 0 --base 1000',
                 'vlabel': 'flags',
                 'category': 'Tor',
                 'info': 'Flags active for relay'}
        labels = {flag: {'label': flag, 'min': 0, 'max': 1, 'type': 'GAUGE'} for flag in stem.Flag}

        TorPlugin.conf_from_dict(graph, labels)

    def fetch(self):
        with gen_controller() as controller:
            try:
                authenticate(controller)
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))
                return

            # Get fingerprint of our own relay to look up the status entry for.
            # In Stem 1.3.0 and later, get_network_status() will fetch the
            # relay's own status entry if no argument is provided, so this will
            # no longer be needed.
            fingerprint = controller.get_info('fingerprint', None)
            if fingerprint is None:
                print("Error while reading fingerprint from Tor daemon", file=sys.stderr)
                sys.exit(-1)

            response = controller.get_network_status(fingerprint, None)
            if response is None:
                print("Error while getting server descriptor from Tor daemon", file=sys.stderr)
                sys.exit(-1)
            for flag in stem.Flag:
                if flag in response.flags:
                    print('{}.value 1'.format(flag))
                else:
                    print('{}.value 0'.format(flag))

class TorCountries(TorPlugin):
    def __init__(self):
        # Configure plugin
        self.cache_dir_name = os.environ.get('torcachedir', None)
        if self.cache_dir_name is not None:
            self.cache_dir_name = os.path.join(self.cache_dir_name,
                                               CACHE_FNAME)

        max_countries = os.environ.get('tormaxcountries', 15)
        self.max_countries = int(max_countries)

        geoip_path = os.environ.get('torgeoippath', DEFAULT_GEOIP_PATH)
        try:
            import GeoIP
            self.geodb = GeoIP.open(geoip_path, GeoIP.GEOIP_MEMORY_CACHE)
            self.available = True
        except Exception:
            self.available = False

    def conf(self):
        """Configure plugin"""
        if not self.available:
            return

        graph = {'title': 'Countries',
                 'args': '-l 0 --base 1000',
                 'vlabel': 'countries',
                 'category': 'Tor',
                 'info': 'OR connections by state'}
        labels = {}

        countries_num = self.top_countries()

        for c, v in countries_num:
            labels[c] = {'label': c, 'min': 0, 'max': 25000, 'type': 'GAUGE'}

        TorPlugin.conf_from_dict(graph, labels)

        # If needed, create cache file at config time
        if self.cache_dir_name:
            with open(self.cache_dir_name, 'w') as f:
                json.dump(countries_num, f)

    def fetch(self):
        """Generate metrics"""

        # If possible, read cached data instead of doing the processing twice
        if not self.available:
            return

        try:
            with open(self.cache_dir_name) as f:
                countries_num = json.load(f)
        except:
            # Fallback if cache_dir_name is not set, unreadable or any other
            # error
            countries_num = self.top_countries()

        for c, v in countries_num:
            print("%s.value %d" % (c, v))

    # Unused
    #@staticmethod
    #def _gen_ipaddrs_from_circuits(controller):
    #    """Generate a sequence of ipaddrs for every built circuit"""
    #    # Currently unused
    #    for circ in controller.get_circuits():
    #        if circ.status != CircStatus.BUILT:
    #            continue
    #
    #        for entry in circ.path:
    #            fingerprint, nickname = entry
    #
    #            desc = controller.get_network_status(fingerprint, None)
    #            if desc:
    #                ipaddr = desc.address
    #                yield ipaddr

    @staticmethod
    def _gen_ipaddrs_from_statuses(controller):
        """Generate a sequence of ipaddrs for every network status"""
        for desc in controller.get_network_statuses():
            ipaddr = desc.address
            yield ipaddr

    def _gen_countries(self, controller):
        """Generate a sequence of countries for every built circuit"""
        for ipaddr in self._gen_ipaddrs_from_statuses(controller):
            country = self.geodb.country_name_by_addr(ipaddr)
            if country is None:
                yield 'Unknown'
                continue

            yield simplify(country)

    def top_countries(self):
        """Build a list of top countries by number of circuits"""
        with gen_controller() as controller:
            try:
                authenticate(controller)
                c = Counter(self._gen_countries(controller))
                return sorted(c.most_common(self.max_countries))
            except stem.connection.AuthenticationFailure as e:
                print('Authentication failed ({})'.format(e))
                return []

def main():
    if len(sys.argv) > 1:
        param = sys.argv[1].lower()
    else:
        param = 'fetch'

    if param == 'autoconf':
        TorPlugin.autoconf()
        sys.exit()
    elif param == 'suggest':
        TorPlugin.suggest()
        sys.exit()
    else:
        # detect data provider
        if __file__.endswith('_connections'):
            provider = TorConnections()
        elif __file__.endswith('_dormant'):
            provider = TorDormant()
        elif __file__.endswith('_traffic'):
            provider = TorTraffic()
        elif __file__.endswith('_countries'):
            #provider = circuits_by_country.TorCountries()
            provider = TorCountries()
        elif __file__.endswith('_bandwidth'):
            provider = TorBandwidth()
        elif __file__.endswith('_flags'):
            provider = TorFlags()
        else:
            print('Unknown plugin name, try "suggest" for a list of possible ones.')
            sys.exit()

        if param == 'config':
            provider.conf()
        elif param == 'fetch':
            provider.fetch()
        else:
            print('Unknown parameter "{}"'.format(param))

if __name__ == '__main__':
    main()

#if __name__ == "__main__":
#    parser = argparse.ArgumentParser()
#    parser.add_argument("query", type=str,
#                        help='query parameter for get_info request')
#    parser.add_argument("-p", "--port", type=int,
#                        help='set the port used for connecting to tor'
#                        ' (default: 9051)', default=9051)
#    parser.add_argument("-s", "--socket", type=str,
#                        help='set the path to the socket used for connecting to tor (if connectmethod=socket)'
#                        ' (default: /var/run/tor/control)', default='/var/run/tor/control')
#    parser.add_argument("-m", "--connectmethod", type=str,
#                        help='the method used to connect to tor (port or socket)'
#                        ' (default: port)', default='port')
#    args = parser.parse_args()
#
#    get_info(args.query, args.port, args.socket, args.connectmethod)
