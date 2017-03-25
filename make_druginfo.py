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

if __name__ == '__main__':
	ret = {}
	for arg in sys.argv:
		fn, ext = os.path.splitext(arg)
		_dir = os.path.dirname(arg)
		if ext in ['.xls', 'xlsx']:
			os.chdir(_dir)
			edis = xlspget(arg, '\d{9}')
			edis = list(set(edis))
			npage = 100
			kw = ' '.join(edis[:50])

			d = DrugInfoScraper()
			for p in range(0, len(edis), npage):
				kw = ' '.join(edis[p:p+npage])
				for row in d.search(kw):
					ret[row['보험코드']] = row
				put_progress(len(edis), p+npage, 'Completed')

	js = json.dumps(ret, indent=4)
	with open('drug.json', 'wt') as fp:
		fp.write(js)