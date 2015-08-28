import time

class Bcolours:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def mprint(body):
	print Bcolours.HEADER + "[" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + "] " + Bcolours.ENDC + body

def mprintln(body):
	mprint(body)
	print ""

def pprint(body, colour):
	print colour + body + Bcolours.ENDC
