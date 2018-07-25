# -*-coding: utf8 -*-

"""
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.07.23.0
Description:
    提供MySQL数据库性能诊断报告
Help:
案例1——备份[所有的库all]/[指定某一个库]
'backup_db_collection': [
		{
	    	    'database':'all', #所有的库用'all',指定的单库用库名
		    'collection': ['all'] # 所有的表用['all']，多个集合用['t1','t2']
		}
	]
案例2——备份多个库
'backup_db_collection': [
		{
	    	    'database':'db1',
		    'collection': ['all']
		}，
		{
	    	    'database':'db2',
		    'collection': ['c1','c2']
		}
	]
```
"""

import sys
import re
import os
from subprocess import *

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


class Mongodump():
    def __init__(self, **kwargs):
        self.bin = kwargs['bin']
        self.user = kwargs['user']
        self.pwd = kwargs['pwd']
        self.authenticationDatabase = kwargs['authenticationDatabase']
        self.backup_db_collection = kwargs['backup_db_collection']
        self.backupdir = kwargs['backupdir']

    def backup_cmd(self, backup_db, backup_collection):
        if backup_db == 'all':
            db = ' '
        else:
            db = '-d {0}'.format(backup_db)

        if backup_collection == 'all':
            collection = ''
        else:
            collection = '-c {0}'.format(backup_collection)
        cmd = '{0} -u{1} -p{2} --authenticationDatabase={3} {4} {5} -o {6}'.format(self.bin, self.user, self.pwd,
                                                                                   self.authenticationDatabase, db,
                                                                                   collection, self.backupdir)
        data['data'].append(cmd)
        return cmd

    def do_backup(self):
        for item in self.backup_db_collection:
            backup_db = item['database']
            backup_c_list = item['collection']
            c_len = len(backup_c_list)
            for c in backup_c_list:
                info = Do_Cmd(self.backup_cmd(backup_db, c)).case_b()
                data['data'].append(info)


def start_mongodump():
    params = {
        'bin': '/alidata/mongodb/bin/mongodump',
        'user': 'backup',
        'pwd': 'uplooking',
        'authenticationDatabase': 'admin',
        'backup_db_collection': [
            {
                'database': 'all',
                'collection': ['all']
            }
        ],
        'backupdir': '/alidata/backup'
    }
    api = Mongodump(**params)
    api.do_backup()
    return data

if __name__ == '__main__':
    print start_mongodump()
