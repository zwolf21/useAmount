from queryworks import Queryset
import xlrd, re, json, sys, os
from dependencies.progress import put_progress




if __name__ == '__main__':
	ret = {}
	for arg in sys.argv:
		fn, ext = os.path.splitext(arg)
		_dir = os.path.dirname(arg)
		if ext in ['.xls', 'xlsx']:
			os.chdir(_dir)
			amountInfo = Queryset([('약품코드', str, ''), ('EDI코드', str, ''), ('사용량', float, 0)], pk='약품코드')
			amountInfo.from_excel(arg)
			ret = amountInfo.db
	js = json.dumps(ret, indent=4)
	with open('useAmount.json', 'wt') as fp:
		fp.write(js)