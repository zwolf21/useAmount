# -*- coding:utf-8 -*-
from collections import OrderedDict
from csv import DictReader, DictWriter, reader
from io import BytesIO, StringIO
import os

import xlrd, xlsxwriter


class Queryset:
	
	def __init__(self, scheme=None, pk=None, query=None):
		self.scheme = scheme
		self.pk = pk
		self.db = {}
		if query and self.scheme:
			for pk ,row in query.items():
				record = {}
				for key, val in row.items():
					for key, constraint, default in self.scheme:
						record[key] = constraint(row.get(key) or default)
				self.db[pk] = record

		

	def _file_contents(self, fn, mode='rt'):
		with open(fn, mode) as fp:
			return fp.read()

	def from_excel(self, excel, target_sheet_index=0, header_row=0):

		'''excel: file name or conents'''

		if isinstance(excel, str):
			fn, ext = os.path.splitext(excel)
			if ext in ['.xls', '.xlsx']:
				with open(excel, 'rb') as fp:
					excel = fp.read()
			else:
				return

		wb = xlrd.open_workbook(file_contents=excel)
		ws = wb.sheet_by_index(target_sheet_index)
		fields = ws.row_values(header_row)

		if not self.scheme:
			self.scheme = list(zip(fields, [str]*len(fields), [""]*len(fields)))

		for r in range(1, ws.nrows):
			raw_data = dict(zip(fields, ws.row_values(r)))
			record = dict()
			
			for column, constraint, default in self.scheme:
				record[column] = constraint(raw_data.get(column) or default)

			if self.pk:
				pk = raw_data[self.pk]
				self.db[pk] = record
			else:
				self.db[r] = record


	def from_csv(self, csv, csv_fp=None):
		fp = csv_fp
		
		if isinstance(csv, str):
			fn, ext = os.path.splitext(csv)
			if ext == '.csv':
				fp = open(csv, 'rt')
			else:
				return 
		
		dict_reader = DictReader(fp)
		fields = list(next(dict_reader).keys())
		
		if not self.scheme:
			self.scheme = list(zip(fields, [str]*len(fields), [""]*len(fields)))
			
		for raw_data in dict_reader:
			record = dict()
			
			for column, constraint, default in self.scheme:
				record[column] = constraint(raw_data.get(column) or default)
			
			if self.pk:
				pk = raw_data[self.pk]
				self.db[pk] = record
			else:
				self.db[r] = record

		fp.close()


	def to_csv(self,  fn=None, fields=None):
		csv = StringIO()

		if not fields:
			fields = [e[0] for e in self.scheme]

		writer = DictWriter(csv, fieldnames=fields)
		writer.writeheader()

		for idx, row in self.db.items():
			writer.writerow(row)

		if fn:
			with open(fn, 'w', newline='') as fp:
				fp.write(csv.getvalue())
		else:
			return csv.getvalue()

	def to_excel(self, fn=None, fields=None):
		output = BytesIO()

		if not fields:
			fields = [e[0] for e in self.scheme]

		wb = xlsxwriter.Workbook(output, {'inmemory': True, 'remove_timezone': True})
		ws = wb.add_worksheet()

		ws.write_row(0, 0, fields)
		for r, (pk, row) in enumerate(self.db.items(), 1):	
			for c, col in enumerate(fields):
				ws.write(r, c, row[col])
				# print(row[col])

		wb.close()
		if fn:
			with open(fn, 'wb') as fp:
				fp.write(output.getvalue())
		else:
			return output.getvalue()


	def filter(self, where):
		self.db = {pk:row for pk, row in self.db.items() if where(row)}
		return self

	def aggregate(self, group, target, func, alias):
		grouped = {}
		typ = str
		for pk, row in self.db.items():
			grouped.setdefault(row[group], []).append(row[target])

		for g, vlist in grouped.items():
			grouped[g] = {alias :func(vlist)}
		else:
			typ = type(func(vlist))

		return self.__class__([(alias, typ, 0)], group, grouped)


	def add_column(self, column, value=None, func=None):
		for pk, row in self.db.items():
			row[column] = func(row) if func else value


	def join(self, queryset, schemes):
		self.scheme+= schemes
		for pk, row in self.db.items():
			updated = {}			
			for scheme in schemes:
				key, func, default = scheme
				updated[key] = queryset.db.get(pk, {key: default})[key]
			row.update(updated)









