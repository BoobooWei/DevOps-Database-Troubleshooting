# coding:utf8


'''
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.07.13.0
Description:
    提供MySQL数据库性能诊断报告
Help:
检查结果：信息0、一般警告1、严重警告2、灾难3
'''
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


class Get_mysql_tunning():
    def __init__(self, url, port, user, password, database, bin):
        self.url = url
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.bin = bin
        self.Info = 0
        self.Deferred_Alarm = 1
        self.Serious_Warning = 2
        self.Disaster = 3
        #信息0、一般警告1、严重警告2、灾难3

    def mysql_cmd(self, exe):
        cmd = """echo "{6}" | {0} -h{1} -P{2} -u{3} -p{4} {5} """.format(self.bin, self.url, self.port, self.user,
                                                                         self.password, self.database, exe)
        return cmd

    def human(self, bytes):
        bytes = float(bytes)
        if bytes >= 1099511627776:
            terabytes = bytes / 1099511627776
            size = '%.0fT' % terabytes
        elif bytes >= 1073741824:
            gigabytes = bytes / 1073741824
            size = '%.0fG' % gigabytes
        elif bytes >= 1048576:
            megabytes = bytes / 1048576
            size = '%.0fM' % megabytes
        elif bytes >= 1024:
            kilobytes = bytes / 1024
            size = '%.0fK' % kilobytes
        else:
            size = '%.0fb' % bytes
        return size

    def return_data(self, **kwargs):
        """
        返回数据库检查项目
        :param Category: 检查项目
        :param Check_status：检查结果（信息0、一般警告1、严重警告2、灾难3）
        :param Issue: 检查结果简易描述
        :param Descreption: 检查结果详细描述
        :param Reference: 帮助链接
        :param Solution: 解决建议
        :param result: 检查项中涉及到的变量和状态值
        :return: 返回有序字典OrderedDict
        """
        a = OrderedDict()

        if 'Category' in kwargs:
            a['Category'] = kwargs['Category']
        else:
            a['Category'] = None

        if 'Check_status' in kwargs:
            a['Check_status'] = kwargs['Check_status']
        else:
            a['Check_status'] = None

        if 'Issue' in kwargs:
            a['Issue'] = kwargs['Issue']
        else:
            a['Issue'] = None

        if 'Description' in kwargs:
            a['Description'] = kwargs['Description']
        else:
            a['Description'] = None

        if 'Reference' in kwargs:
            a['Reference'] = kwargs['Reference']
        else:
            a['Reference'] = None

        if 'Solution' in kwargs:
            a['Solution'] = kwargs['Solution']
        else:
            a['Solution'] = None

        if 'result' in kwargs:
            a['result'] = kwargs['result']
        else:
            a['result'] = None

        return a

    def get_mysql_variables(self):
        """
        获取数据库中所有的变量值，后续check时会用到
        :return: 字典
        """
        self.myv = {}
        cmd = self.mysql_cmd("show global variables")
        for line in Do_Cmd(cmd).case_b():
            line_list = line.split('\t')
            if len(line_list) == 1:
                key = line_list[0]
                value = None
            else:
                key, value = line_list
            self.myv[key] = value
        return self.myv

    def get_mysql_status(self):
        """
        获取数据库当前所有的状态值，后续check时会用到
        :return: 字典
        """
        self.mys = {}
        cmd = self.mysql_cmd("show global status")
        for line in Do_Cmd(cmd).case_b():
            line_list = line.split('\t')
            if len(line_list) == 1:
                key = line_list[0]
                value = None
            else:
                key, value = line_list
            self.mys[key] = value
        return self.mys

    def status_report(self):
        """
        数据库基本信息
        :return: 返回有序字典OrderedDict
        """
        version = self.myv['version']
        uptime = self.mys['Uptime']
        questions = self.mys['Questions']
        threads = self.mys['Threads_connected']
        avg_qps = float(questions) / float(uptime)


        Category = '数据库基本信息'
        Check_status = self.Info
        result = [{
            'version' : 'MySQL版本 : {0}'.format(version),
            'uptime' : 'QPS平均负载 : {0:.2f}'.format(avg_qps),
            'questions' : '查询统计 : {0}'.format(questions),
            'threads' : '已连接的会话数 : {0}'.format(threads)
        }]

        return self.return_data(Category=Category, Check_status=Check_status, result=result)


    def database_data_report(self):
        """
        数据库库的数据量和索引量统计（以表格的形式）
        :return: 返回有序字典OrderedDict
        """
        sql = '''
        select table_schema,round(sum(data_length/1024/1024),2) as data_length_MB,
        round(sum(index_length/1024/1024),2) as index_length_MB 
        from information_schema.tables  
        group by table_schema order by data_length_MB desc,index_length_MB desc;
        '''
        result= Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = '数据库库的数据量和索引量统计'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)


    def table_data_report(self):
        """
        表的数据量和索引量，行数统计前十（以表格的形式）
        :return: string
        """
        sql = '''
        select table_schema,table_name, TABLE_ROWS,
        round(data_length/1024/1024,2) as data_length_MB,
        round(index_length/1024/1024,2) as index_length_MB 
        from information_schema.tables 
        order by data_length_MB desc,index_length_MB desc 
        limit 10;
        '''
        result = Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = '表的数据量和索引量Top10'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)


    def table_and_engine_report(self):
        """
        表数据量统计以及不同存储引擎表的数量统计（以表格的形式）
        :return: string
        """
        sql = '''
        SELECT table_type ,engine,COUNT(TABLE_NAME) AS num_tables
        FROM INFORMATION_SCHEMA.TABLES
        group by TABLE_TYPE,engine order by num_tables desc;
        '''
        result = Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = '表数据量统计以及不同存储引擎表的数量统计'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)


    # return data

    def summary_size_report(self):
        """
        数据和索引量统计和占比（以表格的形式）
        :return: string
        """
        sql = '''set sql_mode='';SELECT
                ROUND(((data_size + index_size) / gb),4) AS total_size_gb,
                ROUND((index_size / gb),4) AS index_size_gb,
                ROUND((data_size / gb),4) AS data_size_gb,
                ROUND((index_size / (data_size + index_size)),2) * 100 AS perc_index,
                ROUND((data_size / (data_size + index_size)),2) * 100 AS perc_data
                FROM (
                  SELECT
                  SUM(data_length) data_size,
                  SUM(index_length) index_size,
                  SUM(if(engine = 'innodb', data_length, 0)) AS innodb_data_size,
                  SUM(if(engine = 'innodb', index_length, 0)) AS innodb_index_size,
                  SUM(if(engine = 'myisam', data_length, 0)) AS myisam_data_size,
                  SUM(if(engine = 'myisam', index_length, 0)) AS myisam_index_size,
                  POW(1024, 3) gb
                  FROM information_schema.tables
                  WHERE table_type = 'BASE TABLE') a;
        '''
        result = Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = '数据和索引量统计和占比'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)

    # return data

    def innodb_engine_report(self):
        """
        innodb存储引擎情况（以表格的形式）
        :return: string
        """
        sql = '''set sql_mode='';SELECT
                 ROUND((SUM(innodb_index_size + innodb_data_size) / gb),4) AS innodb_total_size_gb,
                 ROUND((innodb_data_size / gb),4) AS innodb_data_size_gb,
                 ROUND((innodb_index_size / gb),4) AS innodb_index_size_gb,
                 ROUND(innodb_index_size / (innodb_data_size + innodb_index_size),2) * 100 AS innodb_perc_index,
                 ROUND(innodb_data_size / (innodb_data_size + innodb_index_size),2) * 100 AS innodb_perc_data,
                 ROUND(innodb_index_size / index_size,2) * 100 AS innodb_perc_total_index,
                 ROUND(innodb_data_size / data_size,2) * 100 AS innodb_perc_total_data
                 FROM (
                   SELECT
                   SUM(data_length) data_size,
                   SUM(index_length) index_size,
                   SUM(if(engine = 'innodb', data_length, 0)) AS innodb_data_size,
                   SUM(if(engine = 'innodb', index_length, 0)) AS innodb_index_size,
                   SUM(if(engine = 'myisam', data_length, 0)) AS myisam_data_size,
                   SUM(if(engine = 'myisam', index_length, 0)) AS myisam_index_size,
                   POW(1024, 3) gb
                   FROM information_schema.tables
                   WHERE table_type = 'BASE TABLE') a;
         '''
        result = Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = 'innodb存储引擎表数据量情况'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)

    # return data

    def myiasm_engine_report(self):
        """
        myisam存储引擎情况（以表格的形式）
        :return: string
        """
        sql = '''set sql_mode='';SELECT
                 ROUND((SUM(myisam_index_size + myisam_data_size) / gb),4) AS myisam_total_size_gb,
                 ROUND((myisam_data_size / gb),4) AS myisam_data_size_gb,
                 ROUND((myisam_index_size / gb),4) AS myisam_index_size_gb,
                 ROUND(myisam_index_size / (myisam_data_size + myisam_index_size),2) * 100 AS myisam_perc_index,
                 ROUND(myisam_data_size / (myisam_data_size + myisam_index_size),2) * 100 AS myisam_perc_data,
                 ROUND(myisam_index_size / index_size,2) * 100 AS myisam_perc_total_index,
                 ROUND(myisam_data_size / data_size,2) * 100 AS myisam_perc_total_data
                 FROM (
                   SELECT
                   SUM(data_length) data_size,
                   SUM(index_length) index_size,
                   SUM(if(engine = 'innodb', data_length, 0)) AS innodb_data_size,
                   SUM(if(engine = 'innodb', index_length, 0)) AS innodb_index_size,
                   SUM(if(engine = 'myisam', data_length, 0)) AS myisam_data_size,
                   SUM(if(engine = 'myisam', index_length, 0)) AS myisam_index_size,
                   POW(1024, 3) gb
                   FROM information_schema.tables
                   WHERE table_type = 'BASE TABLE') a;
         '''
        result = Do_Cmd(self.mysql_cmd(sql)).case_e()
        Category = 'myisam存储引擎表数据量情况'
        Check_status = self.Info
        return self.return_data(Category=Category, Check_status=Check_status, result=result)


    def check_dead_lock(self):
        """
        检查死锁情况
        :return: OrderedDict
        """
        Category = "检查死锁情况"
        sql = '''show engine innodb status;'''
        a_str = Do_Cmd(self.mysql_cmd(sql)).case_a()
        if 'LATEST DETECTED DEADLOCK' in a_str:
            Check_status = self.Serious_Warning
            Issue = '存在死锁'
            Description = "在出现死锁的情况下，不同的事务无法进行，因为每个事务持有另一个需要的锁。因为这两个事务都在等待资源可用，所以它们都不会释放它所持有的锁。"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/innodb-deadlocks.html"
            Solution = "您需要找到死锁的原因并从代码级别解决死锁。"
            n_start = a_str.index('LATEST')
            n_end = a_str.index('TRANSACTIONS')
            deadlock_info = a_str[n_start:n_end]
            result = OrderedDict()
            result['deadlock info'] = deadlock_info
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference, Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = '不存在死锁'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category)

    def check_innodb_lock(self):
        """
        检查innodb行锁等待
        获取到innodb事务锁冲突的原始id
        :return:OrderedDict
        """
        Category = "检查innodb行锁等待"
        sql = '''
        select id from information_schema.processlist,information_schema.innodb_trx  
        where trx_mysql_thread_id=id and trx_id in 
        (select blocking_trx_id from (select blocking_trx_id, count(blocking_trx_id) as countnum 
        from 
          (select a.trx_id,a.trx_state,b.requesting_trx_id,b.blocking_trx_id 
          from information_schema.innodb_lock_waits as  b 
          left join information_schema.innodb_trx as a 
          on a.trx_id=b.requesting_trx_id) as t1 
          group by blocking_trx_id 
          order by  countnum desc limit 1)c) ;
        '''
        sql_result = Do_Cmd(self.mysql_cmd(sql)).case_a()

        if len(sql_result) == 0:
            Check_status = self.Info
            Issue = '不存在innodb锁冲突'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category)
        else:
            Check_status = self.Disaster
            Issue = '存在innodb锁冲突'
            Description = "当前存在行锁等待"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/sys-innodb-lock-waits.html"
            Solution = "您需要杀掉innodb事务锁冲突的原始会话id"
            result = OrderedDict()
            result['blocking trx id'] = sql_result
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])



    def check_Metadata_lock(self):
        """
        检查MDL锁
        :return:OrderedDict
        """
        Category = "检查MDL锁"
        sql = '''
          select id,State,command,info from information_schema.processlist where State='Waiting for table metadata lock';
          '''
        sql_result = Do_Cmd(self.mysql_cmd(sql)).case_a()
        if len(sql_result) == 0:
            Check_status = self.Info
            Issue = '不存在锁冲突'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category)
        else:
            Check_status = self.Disaster
            Issue = '存在锁冲突'
            Description = "当前存在metadata锁等待"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/metadata-locking.html"
            Solution = "您需要联系数据库工程师进行处理"
            result = OrderedDict()
            result['matadata_info'] = sql_result
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])



    def check_ratio_aborterd_connections(self):
        """
        检查失败连接的比率
        :return: OrderedDict
        """
        Category = "检查失败连接的比率"

        Aborted_connects = int(self.mys['Aborted_connects'])
        Connections = int(self.mys['Connections'])
        Aborted_connects_ratio = round((float(Aborted_connects) / Connections), 2)

        result = OrderedDict()
        result['Total connections'] = Connections
        result['Total aborted connections'] = Aborted_connects
        result['Percentage , Aborted connections ratio'] = Aborted_connects_ratio

        if Aborted_connects_ratio > 0.1:
            Check_status = self.Deferred_Alarm
            Issue = "存在大量失败连接"
            Description = "存在超过10%的失败连接，这个警报发现了大量与数据库的中断连接。"
            Reference = "http://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#option_mysqld_wait_timeout"
            Solution = "造成这种情况的一个常见原因是，由于连接超时到达，应用程序或锁定的表之间的连接被不正确地关闭，导致随后的连接中断。这个警告建议审核您的代码，以便正确关闭连接，或者在一个临时环境中测试正在测试的查询，以监视锁定的表。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = "失败连接比率正常"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category)


    def check_ratio_max_connections(self):
        """
        检查最大连接数占比
        :return: OrderedDict
        """
        Category = "检查最大连接数占比"
        max_connections = int(self.myv['max_connections'])
        Threads_connected = int(self.mys['Threads_connected'])
        Max_used_connections = int(self.mys['Max_used_connections'])
        connections_ratio = round((float(Max_used_connections) / max_connections), 2)
        max_connect_R = round((Max_used_connections * 1.25), 2)

        result = OrderedDict()
        result['Current max_connections'] = max_connections
        result['Current Threads_connected'] = Threads_connected
        result['Historic Max_used_connections'] = Max_used_connections
        result['Percentagte, The number of used connections is'] = connections_ratio

        if connections_ratio > 0.85:
            Check_status = self.Serious_Warning
            Issue = "最大连接数配置有问题。(max_connections = {0})".format(max_connect_R)
            Description = "服务器连接配置需要进行优化"
            Reference = "http://dev.mysql.com/doc/refman/5.7/en/too-many-connections.html "
            Solution = "更改max_connections的值，以实现85%的最大利用率。请记住，增加连接数量将增加每个线程缓冲区使用的RAM的数量。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = '最大连接数配置正常'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])


    def check_slowlog(self):
        """
        检查慢查询
        :return:
        """
        Category = "检查慢查询"
        long_query_time = self.myv['long_query_time']
        slow_query_log = self.myv['slow_query_log']
        slow_query_log_file = self.myv['slow_query_log_file']
        min_examined_row_limit = self.myv['min_examined_row_limit']
        log_queries_not_using_indexes = self.myv['log_queries_not_using_indexes']
        slow_queries = int(self.mys['Slow_queries'])
        questions = int(self.mys['Questions'])
        slow_query_ratio = round((float(slow_queries) / questions), 2)

        result = OrderedDict()
        result['long_query_time'] = long_query_time
        result['slow_query_log'] = slow_query_log
        result['slow_query_log_file'] = slow_query_log_file
        result['min_examined_row_limit'] = min_examined_row_limit
        result['log_queries_not_using_indexes'] = log_queries_not_using_indexes
        result['slow_queries'] = slow_queries
        result['slow_query_ratio'] = slow_query_ratio

        if slow_query_log == 'ON':

            if slow_query_ratio > 0.1:
                Check_status = self.Deferred_Alarm
                Issue = '慢查询占比较高'
                Description = "慢查询较多需要优化"
                Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#statvar_Slow_queries "
                Solution = "根据您的工作角色(开发人员、DBA或两者的组合)，您可以优化单个SQL语句、整个应用程序、单个数据库服务器或多个网络数据库服务器的级别。有时您可以提前计划并提前计划性能，而其他时候您可能会在出现问题之后对配置或代码问题进行故障排除。优化CPU和内存使用情况还可以提高可伸缩性,允许数据库来处理更多的负载没有放缓down.https:/ /dev.mysql.com/doc/refman/5.7/en/optimization.html"
                return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category,
                                        Description=Description, Reference=Reference,
                                        Solution=Solution, result=[result])
            else:
                Check_status = self.Info
                Issue = '慢查询占比不高'
                return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])
        else:
            Check_status = self.Deferred_Alarm
            Issue = '没有开启慢查询'
            Description = "慢查询日志需要开启"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#statvar_Slow_queries "
            Solution = "通过在mysql配置文件中添加配置 slow_query_log = ON 来启用慢查询日志。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])



    def check_binlog(self):
        """
        检查binlog
        :return: OrderedDict
        """
        Category = "检查二进制日志"
        log_bin = self.myv['log_bin']
        binlog_format = self.myv['binlog_format']
        sync_binlog = self.myv['sync_binlog']
        expire_logs_days = self.myv['expire_logs_days']
        result = OrderedDict()
        result['log_bin'] = log_bin
        result['binlog_format'] = binlog_format
        result['sync_binlog'] = sync_binlog
        result['expire_logs_days'] = expire_logs_days

        if log_bin == 'ON':
            Issue_list = []
            Check_status = self.Info
            if binlog_format != 'ROW':
                Check_status = self.Serious_Warning
                Issue_list.append('二进制日志格式为ROW；')
            elif int(sync_binlog) != 1:
                Check_status = self.Deferred_Alarm
                Issue_list.append('sync binlog值不是 1；')
            elif int(expire_logs_days) == 0:
                Check_status = self.Deferred_Alarm
                Issue_list.append('二进制日志自动清理阈值expire_log_days应该大于0')
            Issue = ' '.join(Issue_list)
            Description = "二进制日志格式应该设为ROW ；二进制日志建议在每次写入时被同步到磁盘上； 二进制日志自动清理阈值expire_log_days应该大于0 "
            Reference = "http://dev.mysql.com/doc/refman/5.7/en/binary-log.html"
            Solution = "您需要修改配置文件，添加或修改二进制日志的相关参数。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Serious_Warning
            Issue_list = ['二进制日志没有开启；']
            if binlog_format != 'ROW':
                Check_status = self.Serious_Warning
                Issue_list.append('二进制日志格式为ROW；')
            elif int(sync_binlog) != 1:
                Check_status = self.Deferred_Alarm
                Issue_list.append('sync binlog值不是 1；')
            elif int(expire_logs_days) == 0:
                Check_status = self.Deferred_Alarm
                Issue_list.append('二进制日志自动清理阈值expire_log_days应该大于0')
            Issue = ' '.join(Issue_list)
            Description = "二进制日志需要开启；二进制日志格式应该设为ROW ；二进制日志建议在每次写入时被同步到磁盘上； 二进制日志自动清理阈值expire_log_days应该大于0 "
            Reference = "http://dev.mysql.com/doc/refman/5.7/en/binary-log.html"
            Solution = "您需要修改配置文件，添加或修改二进制日志的相关参数。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])


    def check_innodb(self):
        """
        检查innodb存储引擎的情况
        :return: OrderedDict
        """
        Category = '检查innodb存储引擎的情况'

        innodb_flush_log_at_trx_commit = self.myv['innodb_flush_log_at_trx_commit']
        innodb_doublewrite = self.myv['innodb_doublewrite']
        tx_isolation = self.myv['tx_isolation']
        innodb_lock_wait_timeout = self.myv['innodb_lock_wait_timeout']  #

        result = OrderedDict()
        result['innodb_flush_log_at_trx_commit'] = innodb_flush_log_at_trx_commit
        result['innodb_doublewrite'] = innodb_doublewrite
        result['tx_isolation'] = tx_isolation
        result['innodb_lock_wait_timeout'] = innodb_lock_wait_timeout

        if int(innodb_flush_log_at_trx_commit) == 1 and innodb_doublewrite == 'ON':
            Check_status = self.Info
            Issue = 'innodb配置良好'
        else:
            Check_status = self.Deferred_Alarm
            Issue = '请检查innodb的相关配置'
        return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])


    def check_table_scans(self):
        """
        检查临时表使用情况
        :return: OrderedDict
        """
        Category = '检查临时表使用情况'

        max_heap_table_size = self.myv['max_heap_table_size']
        tmp_table_size = self.myv['tmp_table_size']
        real_tmp_table_size = min(max_heap_table_size, tmp_table_size)

        Created_tmp_disk_tables = self.mys['Created_tmp_disk_tables']
        Created_tmp_files = self.mys['Created_tmp_files']
        Created_tmp_tables = self.mys['Created_tmp_tables']
        tmp_table_raito = '{0:.1}'.format(float(Created_tmp_disk_tables) / float(Created_tmp_tables))

        result = OrderedDict()
        result['real_tmp_table_size'] = real_tmp_table_size
        result['Created_tmp_disk_tables'] = Created_tmp_disk_tables
        result['Created_tmp_files'] = Created_tmp_files
        result['Created_tmp_tables'] = Created_tmp_tables
        result['tmp_table_raito'] = tmp_table_raito

        if tmp_table_raito <= 0.25:
            Check_status = self.Info
            Issue = '临时表使用情况良好'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])
        else:
            Check_status = self.Serious_Warning
            Issue = '临时表配置需要优化'
            Description = "比较理想的配置是：Created_tmp_disk_tables / Created_tmp_tables * 100% <= 25%。"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#statvar_Created_tmp_disk_tables"
            Solution = "在优化查询语句时，避免使用临时表，如果无法避免，请确保这些临时表在内存中。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])


    def check_open_table(self):
        """
        检查open table的情况
        :return:
        """
        Category = '检查open table的情况'
        table_open_cache = self.myv['table_open_cache']
        Open_tables = self.mys['Open_tables']
        Opened_tables = self.mys['Opened_tables']
        table_cache_hit_rate = float(Open_tables) / float(Opened_tables)
        table_cache_fill = float(Open_tables) / float(table_open_cache)

        result = OrderedDict()
        result['table_open_cache'] = table_open_cache
        result['Open_tables'] = Open_tables
        result['Opened_tables'] = Opened_tables
        result['table_cache_hit_rate'] = '{0:.1}'.format(table_cache_hit_rate)
        result['table_cache_fill'] = '{0:.1}'.format(table_cache_fill)

        if table_cache_fill < 0.95:
            Check_status = self.Info
            Issue = '表缓存配置正常'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])
        elif table_cache_hit_rate <= 0.85:
            Check_status = self.Serious_Warning
            Issue = '表缓存配置不正常'
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#table__open_cache"
            Description = "打开表的数量/打开过的表数量 应该大于等于0.95 ，打开表的数量/表缓存 应该小于等于 0.85"
            Solution = "您可能需要提高table_open_cache配置。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = '表缓存配置正常'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])

    def check_threads(self):
        """
        检查线程缓冲
        :return: OrderedDict
        """
        Category = '检查线程缓冲'
        thread_cache_size = self.myv['thread_cache_size']
        Threads_created1 = self.mys['Threads_created']
        Threads_created2 = self.mys['Threads_created']
        Threads_cached = self.mys['Threads_cached']
        Uptime = self.mys['Uptime']
        historic_threads_per_sec = round((float(Threads_created1) / int(Uptime)), 4)
        current_threads_per_sec = round((float(Threads_created2) - int(Threads_created1)), 4)
        result = OrderedDict()
        result['thread_cache_size'] = thread_cache_size
        result['Threads_created'] = Threads_created1
        result['Threads_cached'] = Threads_cached
        result['historic_threads_per_sec'] = historic_threads_per_sec
        result['current_threads_per_sec'] = current_threads_per_sec

        if (historic_threads_per_sec >= 2 or current_threads_per_sec >= 2) and Threads_cached <= 1:
            Check_status = self.Serious_Warning
            Issue = "线程缓存数thread_cache_size配置不合理"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#thread_cache_size"
            Description = "您应该提高thread_cache_size。"
            Solution = "您应该增加thread_cache_size。默认值基于以下公式，上限为100:[8 + (max_connections / 100)]。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = "线程缓存数thread_cache_size配置正常"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])

    def check_query_cache_type(self):
        """
        检查查询缓存是否关闭
        :return: OrderedDict
        """
        Category = '检查查询缓存是否关闭'
        query_cache_type = self.myv['query_cache_type']
        result = OrderedDict()
        result['query_cache_type'] = query_cache_type
        if query_cache_type == 'OFF':
            Check_status = self.Info
            Issue = '查询缓冲已关闭'
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])
        else:
            Check_status = self.Serious_Warning
            Issue = '查询缓冲仍然开启'
            Description = '关闭查询缓冲后不会缓存结果或从查询缓存中检索结果。'
            Reference = 'http://dev.mysql.com/doc/refman/5.7/en/server-system-variables.html#option_mysqld_query_cache_size'
            Solution = "您目前还没有释放查询缓存缓冲区，您应该将query_cache_size设置为0。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])

    def check_sort_buffer(self):
        """
        检查排序缓冲
        :return: OrderedDict
        """
        Category = '检查排序缓冲'
        sort_buffer_size = self.myv['sort_buffer_size']
        read_rnd_buffer_size = self.myv['read_rnd_buffer_size']
        Sort_merge_passes = self.mys['Sort_merge_passes']
        Sort_scan = self.mys['Sort_scan']
        Sort_range = self.mys['Sort_range']
        total_sorts = int(Sort_scan) + int(Sort_range)
        passes_per_sort = round((float(Sort_merge_passes) / int(total_sorts)), 4)

        result = OrderedDict()
        result['sort_buffer_size'] = self.human(sort_buffer_size)
        result['read_rnd_buffer_size'] = self.human(read_rnd_buffer_size)
        result['Sort_merge_passes'] = Sort_merge_passes
        result['Sort_scan'] = Sort_scan
        result['Sort_range'] = Sort_range
        result['total_sorts'] = total_sorts
        result['passes_per_sort'] = passes_per_sort

        if passes_per_sort >= 2:
            Check_status = self.Serious_Warning
            Issue = "排序缓存配置不合理"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#sort_buffer_size"
            Description = "排序缓冲区的分配比所需的值更大。"
            Solution = "您应该提高sort_buffer_size，还应该提高read_rnd_buffer_size。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = "排序缓存配置正常"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])


    def check_join_buffer_size(self):
        """
        检查join缓存使用情况
        :return:
        """
        Category = '检查join缓存使用情况'
        Select_full_join = self.mys['Select_full_join']
        Select_range_check = self.mys['Select_range_check']
        join_buffer_size = self.myv['join_buffer_size']
        join_buffer_size = int(join_buffer_size) + 4096

        result = OrderedDict()
        result['Select_full_join'] = Select_full_join
        result['Select_range_check'] = Select_range_check
        result['join_buffer_size'] = self.human(join_buffer_size)

        if Select_range_check == '0' and Select_full_join == '0':
            Check_status = self.Info
            Issue = "您的连接似乎正确地使用了索引。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])
        else:
            Check_status = self.Serious_Warning
            Issue = "您的连接似乎没有正确地使用索引。"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#sort_buffer_size"
            Description = "您已经有{0}个join，没有使用索引导致需要全表扫描。".format(Select_range_check)
            Solution = "您可以开启log-queries-not-using-indexes参数，然后在慢速查询日志中查找非索引join语句。如果您无法优化您的查询，您可能希望增加您的join_buffer_size，以容纳更大的连接。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])


    def check_open_files_limit(self):
        """
        检查打开的文件数情况
        :return:
        """
        Category = '检查打开的文件数情况'
        open_files_limit = self.myv['open_files_limit']
        Open_files = self.mys['Open_files']
        open_files_ratio = round((int(Open_files) / float(open_files_limit)), 4)
        result = OrderedDict()
        result['open_files_limit'] = open_files_limit
        result['Open_files'] = Open_files
        result['open_files_ratio'] = open_files_ratio

        if open_files_ratio >= 0.75:
            Check_status = self.Serious_Warning
            Issue = "open_files_limit参数设置需要优化"
            Reference = "https://dev.mysql.com/doc/refman/5.7/en/server-status-variables.html#open_files_limit"
            Description = "目前开启的文件数已经超过了最大文件数限制的75%。"
            Solution = "您需要调高open_files_limit参数值"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, Description=Description,
                                    Reference=Reference,
                                    Solution=Solution, result=[result])
        else:
            Check_status = self.Info
            Issue = "open_files_limit配置正常。"
            return self.return_data(Check_status=Check_status, Issue=Issue, Category=Category, result=[result])


    def get_mysql_tunning(self, check_item='all'):
        self.get_mysql_variables()
        self.get_mysql_status()
        if check_item == 'all':
            result = OrderedDict()
            result['status_report'] = self.status_report()
            result['summary_size_report'] = self.summary_size_report()
            result['database_data_report'] = self.database_data_report()
            result['table_data_report'] = self.table_data_report()
            result['table_and_engine_report'] = self.table_and_engine_report()
            result['innodb_engine_report'] = self.innodb_engine_report()
            result['myiasm_engine_report'] = self.myiasm_engine_report()
            result['check_dead_lock'] = self.check_dead_lock()
            result['check_innodb_lock'] = self.check_innodb_lock()
            result['check_metadata_lock'] = self.check_Metadata_lock()
            result['check_slowlog'] = self.check_slowlog()
            result['check_ratio_aborterd_connections'] = self.check_ratio_aborterd_connections()
            result['check_ratio_max_connections'] = self.check_ratio_max_connections()
            result['check_binlog'] = self.check_binlog()
            result['check_innodb'] = self.check_innodb()
            result['check_table_scans'] = self.check_table_scans()
            result['check_open_table'] = self.check_open_table()
            result['check_threads'] = self.check_threads()
            result['check_query_cache_type'] = self.check_query_cache_type()
            result['check_sort_buffer'] = self.check_sort_buffer()
            result['check_join_buffer_size'] = self.check_join_buffer_size()
            result['check_open_files_limit'] = self.check_open_files_limit()
            data['data'] = result
            return data
        else:
            result = OrderedDict()
            result[check_item] = getattr(self, check_item)()
            data['data'] = result
            return data


def startup(url, port, user, password, database, bin, check_item='all'):
    api = Get_mysql_tunning(url, port, user, password, database, bin)
    data = api.get_mysql_tunning(check_item)
    return data


if __name__ == '__main__':
    # 完整报告
    data = startup("localhost", 3306, 'root', 'uplooking', 'mysql', 'mysql')
    print json.dumps(data)

    # 指定检查项目
    #data = startup("localhost", 3306, 'root', 'uplooking', 'mysql', 'mysql','check_slowlog')
    #print json.dumps(data)

