try:
	from .dependencies.ipservice import get_public_ip
except:
	from dependencies.ipservice import get_public_ip


__all__ = ['HEADERS', 'PUBLIC_IP', 'USER_ID', 'PASSWORD']

HEADERS = {
	'Content-Type':'application/x-www-form-urlencoded',
	'Host':'www.druginfo.co.kr',
	'Origin':'https://www.druginfo.co.kr',
	'Referer':'https://www.druginfo.co.kr/',
	'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
}

PUBLIC_IP = get_public_ip() 
USER_ID = 'anonymous04'
PASSWORD = 'admindg04!'