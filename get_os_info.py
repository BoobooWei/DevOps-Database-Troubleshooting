# coding: utf8

"""
Created on:
@author: BoobooWei
Email: rgweiyaping@hotmail.com
Version: V.18.07.09.0
Description:
    获取Linux服务器的系统相关信息，（OS目前支持redhat centos ubuntu）
    依赖两个工具包 sysstat、net-tools
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

class Get_os_info():
    '''
    获取服务器的操作系统相关信息,（OS为Linux）
    '''
    def __init__(self):
        self.datalist = []
        # 安装必要的linux软件工具sar
        OS_info = Do_Cmd('cat /proc/version').case_b()[0]
        if "Red Hat" in OS_info:
            self.OS = "RedHat\CentOS"
            Do_Cmd('which sar')
            if data['code'] == 1: Do_Cmd('yum install -y sysstat net-tools')
        else:
            self.OS = "Ubuntu"
            Do_Cmd('which sar')
            if data['code'] == 1: Do_Cmd('apt-get install -y sysstat net-tools')



    def get_os_hardware_infos(self):
        '''
        硬件规格信息:cpu mem disk
        系统发行版本和内核信息:release kernel
        '''
        cmd=['cat /proc/version','lscpu','free','df -h']
        info = ['OS Version','cpu','mem','disk']
        result=[]
        for i in cmd:
            result.append(Do_Cmd(i).case_b())
        os_info_dict = OrderedDict(zip(info,result))
        return os_info_dict

    def get_os_old_resource_utilization(self):
        '''
        历史系统资源使用情况;需要额外安装sysstat软件
        sar -u 报告CPU的利用率
        sar -q 报告CPU运行队列和交换队列的平均长度
        sar -r 报告内存没有使用的内存页面和硬盘块
        sar -b 报告IOPS的使用情况
        sar -d 报告磁盘的使用情况
		sar -n 报告网络的使用情况
        '''
        cmd = ['sar -u','sar -q','sar -r','sar -b','sar -d','sar -n']
        info = ['cpu_usage_rate','cpu_average_load','mem_usage_rate','iops_usage_rate','disk_usage_rate','net_usage_rate']
        result = []
        for i in cmd:
            result.append(Do_Cmd(i).case_b())
        os_info_dict = OrderedDict(zip(info, result))
        return os_info_dict

    def get_os_current_resource_utilization(self):
        '''
        实时系统资源使用情况
        观察系统的进程状态、内存使用、虚拟内存使用、磁盘的IO、中断、上下文切换、CPU使用等
        vmstat 1 5
        监控系统磁盘的IO性能情况
        iostat -dkx 1 5
        统计当前所有的连接数情况
        netstat -nat| awk '{print $6}'| sort | uniq -c
        查出哪个ip地址连接最多
        netstat -na|grep ESTABLISHED|awk '{print $5}'|awk -F: '{print $1}'|sort|uniq -c
        查看占用CPU最大的5个进程
        ps -aux 2> /dev/null |sort -k3nr|head -n 5|awk 'BEGIN{print "%CPU\tPID\tCOMMAD"}{print $4,'\t',$2,'\t',$11}'
        查看占用内存最多的5个进程
        ps -aux 2> /dev/null | sort -k4nr |head -n 5 | awk 'BEGIN{print "%MEM\tPID\tCOMMAD"}{print $4,'\t',$2,'\t',$11}'
        '''
        cmd = ['vmstat 1 5',
               'iostat -dkx 1 5',
               "netstat -nat| awk '{print $6}'| sort | uniq -c",
               "netstat -na|grep ESTABLISHED|awk '{print $5}'|awk -F: '{print $1}'|sort|uniq -c",
               '''ps -aux |sort -k3nr|head -n 5''',
               "ps -aux | sort -k4nr |head -n 5"
        ]
        info = ['processlist_info','disk_info','connection_info','max_connected_ip','Top5_processes_consuming_CPU','Top5_processes_consuming_Mem']
        result = []
        for i in cmd:
            result.append(Do_Cmd(i).case_b())
        os_info_dict = OrderedDict(zip(info, result))
        return os_info_dict

    def get_os_info(self):
        data['data'].append(self.get_os_hardware_infos())
        data['data'].append(self.get_os_current_resource_utilization())
        data['data'].append(self.get_os_old_resource_utilization())
        return json.dumps(data)


if __name__ == '__main__':
    get = Get_os_info()
    print get.get_os_info()