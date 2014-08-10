
from collections import Counter
import os
import json

from stem import CircStatus
from stem.control import Controller
import stem

from tor_ import TorPlugin, authenticate

DEFAULT_GEOIP_PATH = "/usr/share/GeoIP/GeoIP.dat"
CACHE_FNAME = 'munin_tor_country_stats.json'


def simplify(cn):
    """Simplify country name"""
    cn = cn.replace(' ', '_')
    cn = cn.replace("'", '_')
    cn = cn.split(',', 1)[0]
    return cn


class TorCountries(TorPlugin):
    def __init__(self, port):
        self.port = port

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

    @staticmethod
    def _gen_ipaddrs_from_circuits(controller):
        """Generate a sequence of ipaddrs for every built circuit"""
        # Currently unused
        for circ in controller.get_circuits():
            if circ.status != CircStatus.BUILT:
                continue

            for entry in circ.path:
                fingerprint, nickname = entry

                desc = controller.get_network_status(fingerprint, None)
                if desc:
                    ipaddr = desc.address
                    yield ipaddr

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

            yield simplify(country)

    def top_countries(self):
        """Build a list of top countries by number of circuits"""
        with Controller.from_port(port=self.port) as controller:
            try:
                authenticate(controller)
                c = Counter(self._gen_countries(controller))
                return sorted(c.most_common(self.max_countries))
            except stem.connection.AuthenticationFailure as e:
                print('Authencation failed ({})'.format(e))
                return []
