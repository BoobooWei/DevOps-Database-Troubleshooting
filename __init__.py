# coding:utf8
"""
1. get_os_info.py:         获取Linux服务器的系统相关信息，（OS目前支持redhat centos ubuntu）
2. get_mysql_tuning.py:    提供MySQL数据库性能诊断报告
3. 根据报告做故障排查
3.1 慢查询日志分析：get_mysql_slowlog.py
3.2
"""

import json

a = {"Instances": {"Instance": [{"RegionId": "cn-hangzhou", "Instance_id": "i-bp1el2h2cnrbp2pxak76"},{"RegionId": "cn-hangzhou", "Instance_id": "i-bp180ru630hv9xaz3yte"},{"RegionId": "cn-hangzhou", "Instance_id": "i-bp1fcqc8bu4h7wru5jyo"}]}}
print json.dumps(a)