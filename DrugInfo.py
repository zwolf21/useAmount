import hashlib, re
from datetime import datetime
from urllib.parse import quote, urljoin
from concurrent.futures import ThreadPoolExecutor

from requests import get, Session
from bs4 import BeautifulSoup
import xlrd

try:
	from .DrugInfoConfig import *
	from .dependencies.HtmlParser import ParseWebPage
except:
	from DrugInfoConfig import *
	from dependencies.HtmlParser import ParseWebPage

__all__ = ['DrugInfoScraper']




def hexMD5(value):
	h = hashlib.md5()
	h.update(value.encode())
	return h.hexdigest()


class DrugInfoScraper:
	host = 'https://www.druginfo.co.kr'
	img_path = '/drugimg/'
	login_url = 'https://www.druginfo.co.kr/login/login.aspx'
	search_url = 'https://www.druginfo.co.kr/search2/search.aspx?q='
	detail_url = 'https://www.druginfo.co.kr/detail/product.aspx?pid='
	MAX_WORKER = 10

	def __init__(self, userId=None, passWord=None, pubicIp=None, headers=None):
		self.session = None
		self.header = headers or HEADERS
		self.userId = userId or USER_ID
		self.passWord = passWord or PASSWORD
		self.pubicIp = pubicIp or PUBLIC_IP
		h = hashlib.md5()
		h.update(self.passWord.encode())
		hidden_value = h.hexdigest()
		timestamp = datetime.now().strftime("%Y%m%d%H")
	
	def _get_login_data(self):
		if self.userId and self.passWord and self.pubicIp:
			timestamp = datetime.now().strftime("%Y%m%d%H")		
			return {
				'id': self.userId,
				't_passwd': self.passWord,
				'passwd': hexMD5(timestamp+hexMD5(self.passWord)+self.pubicIp),
				'timestamp': timestamp,
			}	

	def login(self):
		login_data = self._get_login_data()
		if not login_data:
			return False
		session = Session()
		session.post(self.login_url, login_data, headers = self.header)
		self.session = session
		return True

	def logout(self):
		if self.session:
			self.session.close()

	def search(self, keyword, set_detail=False):
		keyword = quote(keyword, encoding='cp949')
		if self.session:
			r = self.session.get(self.search_url+ keyword, headers=self.header)
		else:
			# r = get(self.search_url, params={'q':keyword})
			r = get(self.search_url+ keyword, headers= self.header)
		prs = ParseWebPage(r.text)
		results = prs.ext_tables('제품명', '임부','보험코드',only_data=True)
		
		id_list = []

		for result in results:
			try:
				drugId, img = result.get('').split(',')
			except:
				drugId, img = '',''
			else:
				id_list.append(drugId)

			finally:
				result['img'] = urljoin(self.host+self.img_path, img)
				result['id'] = drugId
				result['약가'] = self._norm_price(result['약가'])

		if set_detail:
			with ThreadPoolExecutor(min(self.MAX_WORKER, len(id_list))) as executor:
				details = executor.map(self.get_detail, id_list)
			for detail in details:
				if not detail:
					continue
				for result in results:
					if result['id'] == detail['id']:
						break
				else:
					break
				pkg_str = detail.get('포장·유통단위')
				result['pkg_str'] = detail['pkg_str']
				result['pkg_amount'] = detail['pkg_amount']
				result['narcotic_class'] = detail['narcotic_class']
		return results


	def get_detail(self, drugId):
		if not self.login():
			return

		detail = {'id': drugId}
		detail_html = self.session.get(self.detail_url+drugId).text
		detail_prs = ParseWebPage(detail_html)
		for elm in detail_prs.ext_tables('항목', '내용'):
			if elm['항목'] in ['포장·유통단위','주성분코드']:
				detail[elm['항목']] = elm['내용']
		pkg_str = detail.get('포장·유통단위') or ''
		detail['pkg_str'] = pkg_str or ''
		detail['pkg_amount'] = self._pkg_num_from(pkg_str)
		detail['narcotic_class'] = self._get_narcotic_class(detail_html)
		return detail
		
	def _norm_price(self, price_str):
		regx = re.compile('[^\d]')
		try:
			return int(regx.sub('', price_str))
		except:
			return 0

	def _pkg_num_from(self, pkg_str):
		regx = re.compile('(\d+)정|(\d+)caps?|(\d+)T|(\d+)개|(\d+)바이알|(\d+)캡슐|(\d+)C|(\d+)CAPS|(\d+)|(\d+)EA|(\d+)TAB|(\d+)tab|(\d+)캅셀|(\d+)펜|(\d+)V|(\d+)P|(\d+)포')
		try:
			ret = list(filter(None, regx.findall(pkg_str)[-1]))[0]
			return ret
		except IndexError:
			return '1'

	def _get_narcotic_class(self, html):
		soup = BeautifulSoup(html, 'html.parser')
		mdt = soup('td',{'class':"medi_t2"})
		if mdt:
			for m in mdt:
				if '향정의약품' in m.text:
					return '향정'
				elif '마약' in m.text:
					return '마약'
				else:
					continue
			return '일반'



