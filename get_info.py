#!/usr/bin/python2
import stem
import stem.control
import argparse

def get_info(query, port=9051):
	with stem.control.Controller.from_port(port=port) as controller:
		controller.authenticate()

		try:
			response = controller.get_info(query)
			print(response)
		except stem.InvalidArguments as e:
			print("{}".format(e))

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("query", type=str, help='query parameter for get_info request')
	parser.add_argument("-p", "--port", type=int, help='set the port used for connecting to tor (default: 9051)', default=9051)
	args = parser.parse_args()

	get_info(args.query, args.port)

	
		
