# coding:utf8


'''
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.07.25.0
Description:
    解决MetadataLock
Help:
'''
import sys, os, json
import hashlib
import re
import time
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

    def case_d(self):
        line_list = []
        for line in self.out.strip().split('\n'):
            line_list.append(line.strip().split('\t'))
        return line_list

    def case_e(self):
        line_list = []
        a = []
        for line in self.out.strip().split('\n'):
            line_list.append(line.strip().split('\t'))
        key = line_list[0]
        for value in line_list[1:]:
            a.append(OrderedDict(zip(key, value)))
        return a


class Metadata_Lock():
    def __init__(self, url, port, user, password, database, bin):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.bin = bin

    def mysql_cmd(self, exe):
        cmd = """echo "{6}" | {0} -h{1} -P{2} -u{3} -p{4} {5} """.format(self.bin, self.url, self.port, self.user,
                                                                         self.password, self.database, exe)
        return cmd

    def get_mdl_info(self):
        """
        # 查看有metalock锁的线程
        # 查看未提交的事务运行时间，线程id，用户，sql语句等信息
        # 查看未提交的错误事务信息
        :return: 有序字典
        """
        result = OrderedDict()
        sql1 = "select id,State,command,info from information_schema.processlist where State='Waiting for table metadata lock';"
        sql2 = "select  timediff(sysdate(),trx_started) timediff,sysdate(),trx_started,id,USER,DB,COMMAND,STATE,trx_state,trx_query from information_schema.processlist,information_schema.innodb_trx where trx_mysql_thread_id=id;"

        sql_dict = {
            'processlist_MDL': sql1,
            'uncommited_TRX_SQL': sql2
        }
        for k, v in sql_dict.iteritems():
            cmd = self.mysql_cmd(v)
            result[k] = Do_Cmd(cmd).case_e()

        sql = """
        select info from information_schema.processlist where State='Waiting for table metadata lock' limit 1;
        """
        cmd = self.mysql_cmd(sql)
        return_data = Do_Cmd(cmd).case_e()
        if len(return_data) != 0:
            matchobj = re.match(r'.*(from|table|into|update)\s([0-9a-zA-Z]+);?\s?.*', return_data[0]['info'])
            table_name = matchobj.group(2)
            sql = """
            select t.processlist_id,t.processlist_time,e.sql_text,e.message_text 
            from performance_schema.threads t,performance_schema.events_statements_current e 
            where t.thread_id=e.thread_id and e.SQL_TEXT like '%{}%' and e.MESSAGE_TEXT is not null;
            """.format(table_name)
            cmd = self.mysql_cmd(sql)
            return_data = Do_Cmd(cmd).case_e()

        result['uncommited_wrong_trx'] = return_data
        return [result]

    def mdl_case_a(self):
        """第一种情况，则定位到长时间未提交的事务kill即可
        # 查询 information_schema.innodb_trx 看到有长时间未完成的事务， 使用 kill 命令终止该查询。
        """
        sql = """select concat('kill ',i.trx_mysql_thread_id,';') Methods_for_handling_MDL_failures from information_schema.innodb_trx i,
                      (select id, time
                          from information_schema.processlist
                      where
                          time = (
                                select max(time)
                                from
                                    information_schema.processlist
                                where
                                    state = 'Waiting for table metadata lock'
                                    and substring(info, 1, 5) in ('alter' , 'optim', 'repai', 'lock ', 'drop ', 'creat'))) p
                  where timestampdiff(second, i.trx_started, now()) > p.time
                  and i.trx_mysql_thread_id  not in (connection_id(),p.id);        
        """
        cmd = self.mysql_cmd(sql)
        return_data = Do_Cmd(cmd).case_e()
        return return_data

    def mdl_case_b(self):
        """
        第二种情况，是在第一种情况的基础上，还是有metadatalock锁，则手动继续kill掉长事务即可，注意生产环境中，有可能ddl操作需要保留
        :return:
        """
        sql = """
        select  concat('kill ',trx_mysql_thread_id,';') Methods_for_handling_MDL_failures from information_schema.processlist,information_schema.innodb_trx  where trx_mysql_thread_id=id and State!='Waiting for table metadata lock';
        """
        cmd = self.mysql_cmd(sql)
        return_data = Do_Cmd(cmd).case_e()
        return return_data

    def mdl_case_c(self, mdl_info):
        """
        ## 第三种情况没有发现长时间未提交的事务，但是会话中有metadatalock
        :return:
        """
        return_data = []
        for item in mdl_info[0]['uncommited_wrong_trx']:
            return_data.append({'cmd': 'kill {};'.format(item['processlist_id'])})
        return return_data

    def run_cmd(self, info, msg, result):
        for order in info:
            sql = self.mysql_cmd(order.values()[0])
            Do_Cmd(sql)
            result[0]['Operational_log'].append(
                {
                    'OperationalAudit': sql
                }
            )
        now = int(time.time())
        data['data'].append(
            {
                'timestamp': now,
                'trouble_desc': msg,
                'log': result
            }
        )
        time.sleep(5)

    def handle_mdl(self):
        result = []
        mdl_info = self.get_mdl_info()
        mdl_case_a_info = self.mdl_case_a()
        mdl_case_b_info = self.mdl_case_b()
        mdl_case_c_info = self.mdl_case_c(mdl_info)
        result.append(
            OrderedDict({
                'MetaDataLock_log': mdl_info,
                # 'mdl_case_a_info': mdl_case_a_info,
                # 'mdl_case_b_info': mdl_case_b_info,
                # 'mdl_case_c_info': mdl_case_c_info,
                'Operational_log': []
            })
        )
        if len(mdl_info[0]["processlist_MDL"]) != 0:
            # 如果存在mdl锁的会话则进一步判断
            if len(mdl_case_a_info) != 0:
                self.run_cmd(mdl_case_a_info, '存在长时间未提交的事务导致MDL锁', result)
                self.handle_mdl()

            elif len(mdl_case_b_info) != 0:
                self.run_cmd(mdl_case_b_info, 'DDL操作引起MDL锁', result)
                self.handle_mdl()

            elif len(mdl_case_c_info) != 0:
                self.run_cmd(mdl_case_c_info, '存在未提交的错误事务', result)
                self.handle_mdl()

        else:
            result[0]['Operational_log'].append(
                {
                    'OperationalAudit': 'No mdl lock.'
                }
            )
            now = int(time.time())
            data['data'].append(
                {
                    'timestamp': now,
                    'trouble_desc': '故障恢复',
                    'log': result
                }
            )


def startup(url, port, user, password, database, bin):
    """
    :return: data
    """
    api = Metadata_Lock(url, port, user, password, database, bin)
    api.handle_mdl()
    return data


if __name__ == '__main__':
    url, port, user, password, database, bin = "localhost", 3306, 'root', 'uplooking', 'mysql', 'mysql'
    data = startup(url, port, user, password, database, bin)
    print json.dumps(data)
