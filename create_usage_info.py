import json, os
from queryworks import Queryset

with open('drug.json') as fp:
	drugInfo = json.loads(fp.read())

with open('useAmount.json') as fp:
	useAmount = json.loads(fp.read())


ua = Queryset([('약품코드', str, ''), ('EDI코드', str, ''), ('사용량', float, 0)], '약품코드', useAmount)
di = Queryset([('보험코드', str, ''), ('제품명', str, ''), ('성분/함량', str, ''), ('약가', int, 0), ('판매사', str, '')], '보험코드', drugInfo)
ua.filter(lambda row: row['EDI코드']  in di.db)
print(len(ua.db))


edi_amount = ua.aggregate('EDI코드', '사용량', sum, '사용량합계')
di.join(edi_amount, [('사용량합계' ,str ,0)])
print(drugInfo)
di.to_excel('result.xlsx')
os.startfile('result.xlsx')





