import re
from bs4 import BeautifulSoup

class ParseWebPage(object):
	"""docstring for ParsePage"""
	def __init__(self, content):
		self.soup = BeautifulSoup(content, 'html.parser')

	def show_html(self):
		print(self.soup.text)
		
	def ext_links(self, regPattern, **tagAttr):
		rex = re.compile(regPattern)
		for tag, attr in tagAttr.items():
			qry = '{}[{}]'.format(tag, attr)
			links = self.soup.select(qry)
			return [link for link in links if rex.search(link[attr])]

	def ext_tables(self, *column, only_data=True):
		spc = re.compile('\s+')
		ret = []
		for table in self.soup('table'):
			if table('table'):
				continue
			hdr, *recs = table('tr')
			hdr_val = [spc.sub(' ', hdr.text).strip() for hdr in hdr.select('td, th')]

			if set(column) <= set(hdr_val):
				if only_data:
					ret+=[dict(zip(hdr_val, [spc.sub(' ',rec.text).strip() for rec in rec('td')])) for rec in recs]
				else:
					ret+=[dict(zip(hdr_val, [rec for rec in rec('td')])) for rec in recs]
		return ret
