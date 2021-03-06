# -*- coding: utf-8 -*- 
import MySQLdb
import sys
import subprocess
import time
import subprocess
import os
import datetime
import random
from fabric.api import env,run,put,get,local 
reload(sys)
sys.setdefaultencoding('gbk')
os.getenv("ORACLE_HOME")
os.getenv("LD_LIBRARY_PATH")
os.getenv("NLS_LANG")
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import cx_Oracle
import getopt

AWR_DIR='/home/mysql/admin/bin/newbin'
#写入数据的配置，包括收集服务器的标记
ywpt_db_conf='/home/mysql/admin/bin/newbin/ywpt_db.conf'
#读取表结构的配置
tmp_ywpt_db_conf='/home/mysql/admin/bin/newbin/tmp_ywpt_db.conf'
#存储写入数据库的配置
monitor_db={}
tmp_monitor_db={}
is_completed='N'

def main():
    global h_ip,h_id

    try:
        opts, args = getopt.getopt(sys.argv[1:], "Hh:i:d:", ["help","host_ip=","dbid="])
        if len(sys.argv)==1: 
           usage()
           sys.exit(2)
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    for name,value in opts:
        if name in ("-H","--help"):
           usage()
           sys.exit()
        if name in ("-h","--help"):
           usage()
           sys.exit()
        if name in ("-i","--host_ip"):
           h_ip=value
           print "IP:"+h_ip
        if name in ("-d","--dbid"):
           h_id=value
           print "DBID:"+h_id
    connect_ssh(h_ip,h_id)        

def read_conf(conf_file,type):
    file_hand=open(conf_file)
    for line in file_hand:
        line=line.strip()
        (name,value)=line.split(':')
        if type=='ywpt':
            monitor_db[name]=value
        if type=='tmp':
            tmp_monitor_db[name]=value
    file_hand.close()

read_conf(ywpt_db_conf,'ywpt')

mysqldb = MySQLdb.connect(host=monitor_db.get('ip'), user=monitor_db.get('user'),passwd=monitor_db.get('pass'),db=monitor_db.get('db'),port=int(monitor_db.get('port')) ,charset="utf8")
mysqlcur=mysqldb.cursor()

#取得机器密码
def get_server_pass(t_ip_addr):
    global ip_addr
    global username
    global password
    global hostname,host_id
    ip_addr=t_ip_addr
    mysqlcur.execute("set names utf8")
    t_sql="select user_account,user_passwd,host_name from b_host_config where ip_addr=%s limit 1 "
    #mysqlcur.execute(t_sql,ip_addr)
    mysqlcur.execute("select user_account,user_passwd,host_name from b_host_config where ip_addr=%s limit 1 ",(ip_addr,))
    data = mysqlcur.fetchone()
        #hostname 一定要设对，不然后续获得文件名会出错
    username,password,hostname=data

#取得数据库密码    
def get_mysql_pass(t_dbid):
    global my_username,my_password,my_port,my_ip_addr,my_host_id
    mysqlcur.execute("set names utf8")
    t_sql="SELECT a.slow_log_user,a.slow_log_pass,a.port,b.ip_addr,a.host_id FROM b_db_config a,b_host_config b WHERE a.host_id=b.host_id  and a.db_id=%s   limit 1 "
    mysqlcur.execute(t_sql,(t_dbid,))
    data = mysqlcur.fetchone()
    my_username,my_password,my_port,my_ip_addr,my_host_id=data

#取得SLOW LOG日志文件
def get_slow_log():
    rm='rm -rf ' 
    #print my_username,my_password,my_port,my_ip_addr,my_host_id;
    remotedb = MySQLdb.connect(host=my_ip_addr, user=my_username,passwd=my_password,port=int(my_port),charset="utf8")
    remotecur = remotedb.cursor()
    sql_show="show variables like 'slow_query_log';"
    sql_on="set global slow_query_log='on';"
    sql_off="set global slow_query_log='off';"
    sql_dir="show variables like 'slow_query_log_file';"
    remotecur.execute(sql_dir)
    data=remotecur.fetchone()
    SLOW_NAME,SLOW_DIR=data
    remotecur.execute(sql_off)
    local(rm  +'/tmp/'+ip_addr+'_'+my_port+'_slow.log')
    get(SLOW_DIR,'/tmp/'+ip_addr+'_'+my_port+'_slow.log')  
    run('> '+SLOW_DIR)
    remotecur.execute(sql_on)

#入库
def insert_data():
    rm='rm -rf '
    host=monitor_db.get('ip')
    user=monitor_db.get('user')
    passwd=monitor_db.get('pass')
    db=monitor_db.get('db')
    #print host,user,passwd,db
    local(AWR_DIR+'/pt-query-digest --user='+user+' --password='+passwd+' --review h='+host+',D='+db+',t=myawr_query_review --review-history h='+host+',D='+db+',t=myawr_query_review_history --no-report --limit=100% --filter=" \$event->{add_column} = length(\$event->{arg}) and \$event->{dbid}='+"'"+str(h_id)+"'"+' and \$event->{ipaddr}= \$event->{\'ip\'}'+'" '+'/tmp/'+ip_addr+'_'+my_port+'_slow.log')
    local(rm  +'/tmp/'+ip_addr+'_'+my_port+'_slow.log')
  


def connect_ssh(g_ip,g_id):
    host_ip=g_ip
    dbid=g_id
    #根据传入IP取得对应服务器访问的账号等信息
    get_server_pass(host_ip)
    get_mysql_pass(dbid)
    env.user=username
    env.host_string=ip_addr+':22'
    env.password = password
    get_slow_log()
    insert_data()

'''
if __name__=="__main__":
       h_ip=sys.argv[1]   #访问主机ip
       h_id=sys.argv[2]   #访问数据库ID

       connect_ssh(h_ip,h_id)
'''

def usage():
    print '''
---------------usage:------------------
python get_slowlog_new.py -i ip -d dbid
or
python get_slowlog_new.py --host_ip=ip --dbid=dbid
---------------------------------------
'''
         
if __name__=="__main__":
   main()
