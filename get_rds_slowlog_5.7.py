# -*- coding:utf8 -*-
"""
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.09.17.0
Description:
Help:
"""

import MySQLdb
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class mysqlhelper():
    def __init__(self, url, port, username, password, dbname, charset="utf8"):
        self.url = url
        self.port = port
        self.username = username
        self.password = password
        self.dbname = dbname
        self.charset = charset
        try:
            self.conn = MySQLdb.connect(self.url, self.username, self.password, self.dbname, self.port)
            self.conn.set_character_set(self.charset)
            self.cur = self.conn.cursor()
        except MySQLdb.Error as e:
            print("Mysql Error %d: %s" % (e.args[0], e.args[1]))

    def query(self, sql):
        try:
            n = self.cur.execute(sql)
            return n
        except MySQLdb.Error as e:
            print("Mysql Error:%s\nSQL:%s" % (e, sql))

    def queryRow(self, sql):
        """
        :param sql:string
        :return: result:tuple
        """
        self.query(sql)
        result = self.cur.fetchone()
        return result

    def queryAll_tuple(self, sql):
        """
        :param sql:string
        :return: result:tuple
        """
        self.query(sql)
        result = self.cur.fetchall()
        return result

    def queryAll_dict(self, sql):
        """
        :param sql:string
        :return: result:dict
        """
        self.query(sql)
        result = self.cur.fetchall()
        return dict(result)

    def queryAll_xls(self, sql):
        """
        定制慢查询输出

        :param sql:
        :return:
        <tr><td>1</td><td>select name,sleep(2) from db1.t1 where age>10
        LIMIT 0, 1000</td><td>1次</td><td>18.002秒</td></tr><tr><td>2</td><td>select id,name,sleep(2) from db1.t1 where id=1
        LIMIT 0, 1000</td><td>1次</td><td>2.001秒</td></tr><tr><td>3</td><td>select name,sleep(2) from db1.t1 where name = 'superman'
        LIMIT 0, 1000</td><td>1次</td><td>2.001秒</td></tr>
        """
        result = self.queryAll_tuple(sql)
        tbody = ''
        for i in range(len(result)):
            for j in range(0, len(result[i]), 3):
                tbody += "<tr><td>%s</td><td>%s</td><td>%s次</td><td>%s秒</td></tr>" \
                         % (str(i + 1), result[i][j], result[i][j + 2],
                            round(float(result[i][j + 1]), 3))
        return tbody

    def close(self):
        self.cur.close()
        self.conn.close()

class CloudCareMail():
    def __init__(self, InstanceId, count, tbody, client, start_time, end_time):
        self.from_user = "xxx@jiagouyun.com"
        self.to_users = ["xxx@jiagouyun.com", "xxx"]
        self.host = "smtp.jiagouyun.com"
        self.count = count
        self.tbody = tbody
        self.msg = MIMEMultipart('related')
        self.InstanceId = InstanceId
        self.client = client
        self.start_time = start_time
        self.end_time = end_time

    def get_subject(self,):
        subject = "{0}RDS慢查询(test)Top{1}_{2}_{3}".format(self.client, str(self.count), self.start_time, self.end_time)
        return subject

    def get_body(self):
        content = "<p>DBInstanceId:{0}</p>".format(self.InstanceId)
        content += "<table border=\"1\"><thead><tr><th>序号</th><th>SQL语句</th><th>执行次数</th><th>平均执行时间</th></tr></thead><tbody>%s</tbody></table><br>".format(self.tbody)
        content += "<p><br><img src=\"http://static.moseeker.com/upload/logo/eee9c06e-e733-11e5-aa69-00163e003ad7.png\" /></p><p>中国上海市浦东新区科苑路399号张江创新园7号楼<br></p><p>400-882-3320 |&nbsp;<a href=\"http://www.cloudcare.cn/\" target=\"_blank\">www.cloudcare.cn</a><br></p>"
        html_format = """<table width="800" border="0" cellspacing="0" cellpadding="4">%(content)s</table>"""
        c = html_format % {'content': content}
        msgtext = MIMEText(c, "html", "UTF-8")
        return msgtext

    def send_mail(self):
        msgtext = self.get_body()
        self.msg.attach(msgtext)
        self.msg['Subject'] = self.get_subject()
        self.msg['From'] = self.from_user
        if len(self.to_users) > 1:
            self.msg['To'] = ",".join(self.to_users)
        else:
            self.msg['To'] = self.to_users
        try:
            server = smtplib.SMTP_SSL()
            server.connect(self.host, "465")
            server.set_debuglevel(1)
            server.login(self.from_user, "xxx")
            server.sendmail(self.from_user, self.to_users, self.msg.as_string())
            server.quit()
            print "发送成功"
        except Exception as e:
            print str(e)



class GetRDSSlowQuery57():
    def __init__(self, **kwargs):
        self.url = kwargs['url']
        self.port = kwargs['port']
        self.user = kwargs['user']
        self.password = kwargs['password']
        self.database = kwargs['database']
        self.count = kwargs['count']
        self.cli = mysqlhelper(self.url, self.port, self.user, self.password, self.database)
        self.start_time = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        #self.start_time = '2018-09-17'
        self.end_time = (datetime.datetime.now() - datetime.timedelta(days=0)).strftime("%Y-%m-%d")
        #self.end_time = '2018-09-18'


    def get_rds_query_57(self):
        sql = """
              select sql_text,avg(query_time),count(*) count 
              from mysql.slow_log 
              where start_time >= '{0}' and start_time < '{1}' 
              and sql_text not regexp 'analysis_' 
              group by sql_text 
              order by count desc , query_time desc 
              limit {2}""".format(self.start_time, self.end_time, self.count)
        result = self.cli.queryAll_xls(sql)
        self.cli.close()
        return result


def startup():
    params = {
        'url': 'xxx',
        'port': 3306,
        'user': 'booboo',
        'password': 'xxx',
        'database': 'mysql',
        'count': 3
    }
    api = GetRDSSlowQuery57(**params)
    client = '千颂网络'
    InstanceId = 'boobootestrds'
    count = api.count
    tbody = api.get_rds_query_57()
    start_time = api.start_time
    end_time = api.end_time
    cm = CloudCareMail(InstanceId, count, tbody, client, start_time, end_time)
    cm.send_mail()


if __name__ == '__main__':
    startup()