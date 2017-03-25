import time

from requests import get

__all__ = ['get_public_ip']

def timeit(func):
	def timed(*args, **kwargs):
		ts = time.time()
		result = func(*args, **kwargs)
		te = time.time()
		print('%r (%r, %r) %2.2f sec' % (func.__name__, args, kwargs, te-ts))
		return result
	return timed


def ip42pl():
	return get('http://ip.42.pl/raw').text
	

def jsonip():
	return get('http://jsonip.com').json()['ip']
	

def httpbin():
	return get('http://httpbin.org/ip').json()['origin']
	

def ipify():
	return get('https://api.ipify.org/?format=json').json()['ip']
	


IP_SEVERS = [httpbin, ip42pl, jsonip, ipify]


def get_public_ip():
	for f in IP_SEVERS:
		try:
			ret =  f()
		except Exception as e:
			pass
		else:
			return ret
