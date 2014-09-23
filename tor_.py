#!/usr/bin/python2

from __future__ import print_function
import os
import sys

try:
    import stem
    from stem.control import Controller
except ImportError:
    print('no (tor-munin requires the stem library from https://stem.torproject.org.)')
    sys.exit()

import circuits_by_country

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
    try:
        connect_method = os.environ['connectmethod']
    except KeyError:
        connect_method = 'port'

    if connect_method == 'port':
        try:
            port = os.environ['port']
        except KeyError:
            port = 9051

        return Controller.from_port(port=port)
    elif connect_method == 'socket':
        try:
            socket = os.environ['socket']
        except KeyError:
            socket = '/var/run/tor/control'

        return Controller.from_socket_file(path=socket)
    else:
        raise ValueError("env.connectmethod contains in invalid value. Please specify either 'port' or 'socket'.")


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
        options = ['connections', 'traffic']
        tc = circuits_by_country.TorCountries()
        if tc.available:
            options.append('countries')

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
                    print("No response from Tor Daemon in TorConnection.fetch()", file=sys.stderr)
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
                controller.authenticate()

                response = controller.get_info('dormant', None)
                if response is None:
                    print("Error while reading dormant state from Tor Deamon", file=sys.stderr)
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
                 'type': 'COUNTER',
                 'info': 'bytes read/written'}
        labels = {'read': {'label': 'read', 'min': 0, 'type': 'COUNTER'},
                  'written': {'label': 'written', 'min': 0, 'type': 'COUNTER'}}

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
                print("Error while reading traffic/read from Tor Deamon", file=sys.stderr)
                sys.exit(-1)

            print('read.value {}'.format(response))

            response = controller.get_info('traffic/written', None)
            if response is None:
                print("Error while reading traffic/write from Tor Deamon", file=sys.stderr)
                sys.exit(-1)
            print('written.value {}'.format(response))


def main():
    param = None
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
        provider = None
        if __file__.endswith('_connections'):
            provider = TorConnections()
        elif __file__.endswith('_dormant'):
            provider = TorDormant()
        elif __file__.endswith('_traffic'):
            provider = TorTraffic()
        elif __file__.endswith('_countries'):
            provider = circuits_by_country.TorCountries()
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
