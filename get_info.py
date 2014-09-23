#!/usr/bin/python2
import stem
import stem.control
import argparse


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str,
                        help='query parameter for get_info request')
    parser.add_argument("-p", "--port", type=int,
                        help='set the port used for connecting to tor'
                        ' (default: 9051)', default=9051)
    parser.add_argument("-s", "--socket", type=str,
                        help='set the path to the socket used for connecting to tor (if connectmethod=socket)'
                        ' (default: /var/run/tor/control)', default='/var/run/tor/control')
    parser.add_argument("-m", "--connectmethod", type=str,
                        help='the method used to connect to tor (port or socket)'
                        ' (default: port)', default='port')
    args = parser.parse_args()

    get_info(args.query, args.port, args.socket, args.connectmethod)
