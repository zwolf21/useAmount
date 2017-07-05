import requests
from urllib.parse import quote, urljoin
import os, re
import json
from bs4 import BeautifulSoup
from recordlib import RecordParser, read_excel, read_csv
from concurrent.futures import ThreadPoolExecutor
# curl "http://www.kimsonline.co.kr/drugcenter/search/detailsearchlist?Page=1^&prodtype=E" 
# -H 
# -H 
# -H 
# -H "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36" 
# -H "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8" 
# -H "Referer": "http://www.kimsonline.co.kr/DrugCenter/Search/detailsearch" 
# -H 
# -H  
# -H "Cache-Control": "max-age=0" --compressed

MAX_WORKER = 2

search_root = 'http://kims.co.kr/drugcenter/search/totalSearch/%EA%B0%80%EB%B0%94%ED%8E%98%EB%8B%8C%EC%BA%A1%EC%8A%90%20300mg'

class Kims:
	host = 'http://kims.co.kr/'
	search_list_api = 'http://kims.co.kr/Function/GetTotalSearch'
	search_detail_api = 'http://kims.co.kr/Function/GetUserControl'
	search_detail_url = 'http://www.kimsonline.co.kr/drugcenter/search/druginfo/'
	get_all_url = 'http://kims.co.kr/drugcenter/search/detailsearchlist'



	api_headers = {
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8" ,
		"Accept-Encoding": "gzip, deflate" ,
		"Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4" ,
		"Upgrade-Insecure-Requests": "1" ,
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
		"Content-Type": "application/json; charset=UTF-8",
		"Cookie": "cc_dbc=1; ASP.NET_SessionId=3js14nepgbjuiegsqhkr0sgg; s_lastvisit=1499247477038; .AUTHCOOKIE=4FABD7D2866D7940A9656155FF0FA3CEDC325A2D6368DBF662018305DEE1E0717A6D5CAB74283231F50D8B8556ABEE348421649E1065D56A89DB4428DB1EBEAC597AE7E0BA965A702E12C6C4DC28ACEE4D3BC488; Member=IPH9wCpf20+WPq/xBUImBWaK5lt1rU6KxGt9eEjW7EUCTasD6gq53gETLJh43+qs5mviJ0ndgkNmBdzMYuDSO44MYPeDs/yEuHNnbVFyMjUFSe/F/ZXsFr1mQOjoE38WIbGQ0XG8AaSjAQ+8tyYAZjxbesVk8Rzg/+qCtbpKUFpbDE1w1RcPijYnUH39KG9fiFI7P3NDGMiHFCwh5N67MA==; s_cc=true; s_nr=1499248030407-Repeat; us_sm_aut=6-111; s_sq=%5B%5BB%5D%5D" ,
		"Referer":"http://www.kimsonline.co.kr/DrugCenter/Search/detailsearch",
		"Cache-Control": "max-age=0",
		"Connection": "keep-alive",
		"Host": "www.kimsonline.co.kr"
	} 

	def search(self, keyword):
		payload = {
			"parameters":[
				{"Key":"TotalSearchKeyword","Value":keyword},
				{"Key":"MarketStatus","Value":"AS"},
				{"Key":"PageNo","Value":"1"},
				{"Key":"RowCount","Value":"200"}
		]}

		r = requests.post(self.search_list_api, data = json.dumps(payload), headers = self.api_headers)
		rsp = r.json()
		soup = BeautifulSoup(rsp['d'], 'html.parser')
		return [{row.name: row.text  for row in items if row.name} for items in soup('item')]

	def detail(self, kimscode):
		payload = {"control": 'briefmono', "KIMSCODE": kimscode}
		r = requests.get(urljoin(self.search_detail_url, kimscode), headers=self.api_headers)
		soup = BeautifulSoup(r.text, 'html.parser')

		table = soup.find('table', class_='ViewInfoTable')

		col_name_map = {
			'구분': 'kind', '제조사': 'manufacture', '판매사': 'celler', '포장정보': 'pkg_info', '보험정보': 'insurance_info', 'ATC 코드': 'atc_code',
			'복지부 분류': 'official_sort', 'KIMS 분류': 'kims_sort', '성분 및 함량': 'components', '생산발매현황': 'man_cell_status', '주성분코드 도움말': 'component_code'
		}

		row = {'drug_id': kimscode}

		for tr in table('tr'):
			if tr.th and tr.td:
				key = tr.th.text.strip()
				val = tr.td.text.strip()
				trans_key = col_name_map.get(key, key)
				

				if trans_key == 'atc_code':
					a = tr.td.find('a')
					if a:
						val = a.text

				row[trans_key] = val
		
		return row
	
	

	def get_all(self, category="E", market_status='AS', page=1, set_detail=False):
		'''	present_code = {'Y':'급여', 'N': '비급여'}
			prodtype_code = {'E': '전문', 'O': '일반', 'Q': '의약외품'}
			market_status_code = {'AS': '유통/생산 중', 'AE': '유통/생산 미확인', 'AD': '유통/생산 중단'}
		'''

		params = {"Page": page, "prodtype": category, "MktStatus": market_status}
		r = requests.get(self.get_all_url, params=params , headers=self.api_headers)
		soup = BeautifulSoup(r.text, 'html.parser')
		table = soup.find('div', {'class': 'search_result_list'})

		tab_as = soup.find(id='tabAS')
		tab_ae = soup.find(id='tabAE')
		tab_ad = soup.find(id='tabAD')

		as_count = tab_as.text
		ret = []
		for row in table('li'):
			img = row.find('img', {'src': re.compile(r'^/Data/DrugPictures_Small/.+$')})
			img_src = img['src'] if img else ''

			subject = row.find(class_='subject_kr')

			if not subject:
				return ret

			href = subject.a['href'] if subject.a else ''
			name = subject.a.text if subject.a else ''
			pow_yesno = '불가' if row.find('span', {'class': re.compile('.*icon_crs')}) else '가능'
	
			cmpnt = row.find(class_='subject_eng')
			component = cmpnt.text if cmpnt else ''
			
			info_area = row.find(class_='info_area')
			price = info_area.find(class_='price')
			edi = info_area.find(class_='type')
			company = info_area.find(class_='company')
			present_val = info_area.find('span', {'class': re.compile('.+[YNX]')})['class'][1][-1]
			
			present_code = {'Y':'급여', 'N': '비급여'}
			prodtype_code = {'E': '전문', 'O': '일반', 'Q': '의약외품'}
			market_status_code = {'AS': '유통/생산 중', 'AE': '유통/생산 미확인', 'AD': '유통/생산 중단'}


			ret.append({
				'market_status': market_status,
				'prod_type': prodtype_code.get(category),
				'img_src': urljoin(self.host, img_src) if img_src else '',
				'href': urljoin(self.host, href),
				'name': name,
				'component_summary': component,
				'company': company.text if company else '',
				'edi': edi.text if edi else '',
				'price': price.text.replace(',', '').replace('원', '') if price else '',
				'drug_id': os.path.basename(href),
				'powder_yesno': pow_yesno,
				'present_yesno': present_code.get(present_val, '산정불가')
			})

		if set_detail:
			recs_list = RecordParser(ret)
			id_list = recs_list.select(['drug_id'], inplace=False).to2darry(headers=False)
			id_list = [e[0] for e in id_list]

			with ThreadPoolExecutor(min(MAX_WORKER, len(ret))) as executor:
				details = executor.map(self.detail, id_list)

			recs_detail = RecordParser(list(details))
			recs_list.vlookup(recs_detail, 'drug_id', 'drug_id', 
				[
					('manufacture', ''), ('celler', ''), ('pkg_info', ''),
				 	('official_sort', ''), ('components', ''), ('component_code', '')
				]
			)
			print('Detail: ', len(recs_detail))
			return recs_list.records

		return ret

	def save_drug_list(self, page_start, page_end, categorys, market_status, excel=None, csv=None, append=False, set_detail=False):
		'''	present_code = {'Y':'급여', 'N': '비급여'}
			categorys = {'E': '전문', 'O': '일반', 'Q': '의약외품'}
			market_status = {'AS': '유통/생산 중', 'AE': '유통/생산 미확인', 'AD': '유통/생산 중단'}
		'''
		if append:
			recs = read_excel(excel) if excel else read_csv(csv, encoding='cp949')
		else:
			recs = RecordParser()

		for ctg in categorys:
			for mks in market_status:
				for npage in range(page_start, page_end):
					try:
						record = RecordParser(self.get_all(category=ctg, market_status=mks, page=npage, set_detail=set_detail))
					except Exception as e:
						print("Except on", ctg, mks, npage, e)
						break
					if not record:
						break
					recs+= record
					print('{}-{}-{}'.format(ctg, mks, npage))


		recs.distinct(['drug_id'])
		if excel:
			recs.to_excel(excel)
		elif csv:
			recs.to_csv(csv)



k = Kims()

k.save_drug_list(
	page_start=70, page_end=85,
	categorys = [
		'E', 
		'O', 
		'Q'
	],
	market_status = [
		'AS', 
		'AE', 
		'AD'
	],
	csv='kims_drug_detail_db.csv',
	append=True,
	set_detail=True
)

# ret = k.get_all(set_detail=0)


# recs = read_excel('kim_drugs_db.xlsx')
# print(len(recs))
# recs.distinct(['drug_id'])
# print(len(recs))
# keys = "DADBLDS0LG2 DBCTLTP02TD DBCTLTP0HHU DBIPLDS0LL1 DDBTLSRC51Z DIVCLKT0LIP DUNNLUN0HTS DUNNLUN0HUS DUNNLUN0HVR DUNNLUN0HWR E3MPLAE02DB E3MPLCOBN6I E3MPSPT00AY E3MPSPT02YJ E3MPSPT0H5I E3MPSTB00AO E3MPSTB093T E3MPSTDBZQX EABASIJ0AIN EABASIJ0AJN EABASIJ0AKN EABASIJ0ALN EABASIJ0AMN EABASIJ0ANN EABASIJ0AON EABASIJ0APN EABASIJ0C2I EABASIJ0C3I EABASIJ0C4I EABASIJ0C5I EABASIJ0C6I EABASIJ0C7I EABASIJ0C8I EABASIJ0C9I EABBSCH00WP EABBSCH0DOC EABBSCH0DPC EABBSCH0GVD EABBSCS08BI EABBSIJ00L7 EABBSIJ012C EABBSIJ01DI EABBSIJ01W6 EABBSIJ02AV EABBSIJ03Q1 EABBSIJ0DFB EABBSIJ0DGC EABBSIJ0DHB"
# codes =keys.split()
# ret = k.detail('EDWPSTB0N88')

# for code in codes:
# 	ret = k.detail(code)
# 	print(ret)