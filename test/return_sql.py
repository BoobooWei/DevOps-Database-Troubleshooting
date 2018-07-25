# coding:utf8

import sys, os, json
import hashlib
import re
from collections import OrderedDict
from subprocess import *

reload(sys)
sys.setdefaultencoding('utf8')

'''
table_schema	data_length_MB	index_length_MB
uplooking	281.77	0.00
otter	44.88	0.63
vingoo_manage_sys	10.03	2.34
vingoo_manage_sys_old	9.08	2.30
zabbix	3.94	3.06
mysql	3.45	0.21
information_schema	0.16	0.00
sys	0.02	0.00
performance_schema	0.00	0.00
'''

# case_d()=[[],[],[]]

result = [
    ['table_schema', 'data_length_MB', 'index_length_MB'],
    ['uplooking', '281.77', '0.00'],
    ['otter', '44.88', '0.63'],
    ['vingoo_manage_sys', '10.03', '2.34']
]

#case_e
a = []
key = result[0]
for value in result[1:]:
     a.append(OrderedDict(zip(key,value)))
print a

data = {
    'version': 'MySQL版本 : {0}'.format(1),
    'uptime': 'QPS平均负载 : {0:.2f}'.format(2),
    'questions': '查询统计 : {0}'.format(3),
    'threads': '已连接的会话数 : {0}'.format(4)
}
result= [data]
print result