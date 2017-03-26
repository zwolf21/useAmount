from DrugInfo import DrugInfoScraper
import xlrd, re, json, sys, os
from dependencies.progress import put_progress

def xlspget(xls, pat):
	retPat = []
	p = re.compile(pat)
	wb = xlrd.open_workbook(xls)
	for nsht in range(wb.nsheets):
		sht = wb.sheet_by_index(nsht)
		for r in range(sht.nrows):
			for c in sht.row(r):
				if p.findall(c.value):
					retPat+=p.findall(c.value)
	return retPat

def get_from_json(file):
	if os.path.isfile(file):
		with open(file) as fp:
			data = fp.read()
		return json.loads(data)
	else:
		return {}


if __name__ == '__main__':
	
	jsonEdis = get_from_json('drug.json')

	for arg in sys.argv:
		ret = {}
		fn, ext = os.path.splitext(arg)
		_dir = os.path.dirname(arg)
		if ext in ['.xls', 'xlsx']:
			os.chdir(_dir)
			edis = xlspget(arg, '\d{9}')
			edis = list(set(edis) - set(jsonEdis))
			npage = 100
			kw = ' '.join(edis[:50])

			d = DrugInfoScraper()
			for p in range(0, len(edis), npage):
				kw = ' '.join(edis[p:p+npage])
				for row in d.search(kw):
					ret[row['보험코드']] = row
				put_progress(len(edis), p+npage, 'Completed')
			jsonEdis.update(ret)
		else:
			continue

	js = json.dumps(jsonEdis, indent=4)
	with open('drug.json', 'wt') as fp:
		fp.write(js)