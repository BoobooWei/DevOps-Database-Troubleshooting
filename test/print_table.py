# coding:utf8



import json
import sys
reload(sys)
sys.setdefaultencoding('utf8')


class Print_Table():
    def __init__(self, data):
        self.data = data
        self.maxlen = 0
        for line in self.data:
            for col in line:
                if len(col) > self.maxlen:
                    self.maxlen = len(col)

    def report_format_left(self):
        report = []
        for line in self.data:
            line_format = []
            for col in line:
                col_format = col + (self.maxlen - len(col)) * ' ' + '\t'
                line_format.append(col_format)
            report.append(line_format)
        return report

    def report_print(self):
        report = []
        data_left = self.report_format_left()
        length = len(data_left[0])
        for i in data_left:
            report.append('-' * (length + 1) * self.maxlen + '\n')
            report.extend(i)
            report.append('\n')
        report.append('-' * (length + 1) * self.maxlen)
        return report



data = [["TABLE_TYPE","Engine","Count"],["BASE TABLE","MyISAM","10"],["BASE TABLE","CSV","2"]]
api = Print_Table(data)
for line in  api.report_print():
    sys.stdout.write(line)
