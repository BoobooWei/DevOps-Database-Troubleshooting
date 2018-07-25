# coding:utf8

"""
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.07.09.0
Description:
    提供MySQL数据库慢查询日志Top 10
    判断标准为：先按照出现次数最多，再按照耗时最长排序
Help:
"""

import sys, os, json
import hashlib
import re
from collections import OrderedDict
from subprocess import *

reload(sys)
sys.setdefaultencoding('utf8')

data = {
    'data': [],
    'code': 0,
    'msg': ''
}


class Do_Cmd():
    def __init__(self, cmd):
        output = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        self.out, self.err = output.communicate()
        returncode = output.poll()
        if returncode != 0:
            data['code'] = 1
            data['msg'] = self.err

    def case_a(self):
        return self.out.strip()

    def case_b(self):
        return self.out.strip().split('\n')

    def case_c(self):
        return self.out.strip().split()


class Get_mysql_slowlog():
    def __init__(self, exe, slow_query_log_file):
        self.exe = exe
        self.slow_query_log_file = slow_query_log_file

    def parse_slowlog(self, slowlog):
        """
        Count: 35207  Time=2.81s (98813s)  Lock=0.00s (2s)  Rows=3.0 (106359), 2users@4hosts
        出现次数(Count),
        执行最长时间(Time),
        累计总耗费时间(Time),
        等待锁的时间(Lock),
        发送给客户端的行总数(Rows),
        扫描的行总数(Rows),
        用户以及sql语句本身
        :param slowlog:
        :return:
        """
        matchobj = re.match(r'Count:(.*)Time=(.*)s \((.*)s\).*Lock=(.*)s.*\((.*)s\).*Rows=(.*).*\((.*)\),(.*)', slowlog)
        if not matchobj:
            return None
        count = matchobj.group(1).strip()
        time = matchobj.group(2).strip()
        time_all = matchobj.group(3).strip()
        lock_wait_time = matchobj.group(4).strip()
        lock_wait_time_all = matchobj.group(5).strip()
        send_rows = matchobj.group(6).strip()
        scan_rows = matchobj.group(7).strip()
        user = matchobj.group(8).strip()
        return (count, time, time_all, lock_wait_time, lock_wait_time_all, send_rows, scan_rows, user)

    def get_mysql_slowlog(self):
        r1 = re.compile('Count')
        r2 = re.compile('select')
        num = 0
        names = locals()
        b_list = ['count', 'time', 'time_all', 'lock_wait_time', 'lock_wait_time_all', 'send_rows', 'scan_rows', 'user', 'sql']
        slowlog_list = []
        cmd = '{0} -s c -t 10 {1}'.format(self.exe, self.slow_query_log_file)

        for a_str in Do_Cmd(cmd).case_b():
            if r1.match(a_str):
                num = num + 1
                (count, time, time_all, lock_wait_time, lock_wait_time_all, send_rows, scan_rows, user) = self.parse_slowlog(a_str)
                names['b_list%d' % num] = [count, time, time_all, lock_wait_time, lock_wait_time_all, send_rows, scan_rows, user]
            elif r2.search(a_str):
                names['b_list%d' % num].append(a_str)

        for j in range(1, num + 1):
            c_list = names['b_list%d' % j]
            slowlog_list.append(OrderedDict(zip(b_list, c_list)))
        data['data'].append(slowlog_list)
        return data

if __name__ == "__main__":
    ops = Get_mysql_slowlog(exe='/data/mysql/bin/mysqldumpslow', slow_query_log_file='/data/mysql/data/iZbp10n0r0zwuwczjebdzwZ-slow.log')
    print json.dumps(ops.get_mysql_slowlog())
