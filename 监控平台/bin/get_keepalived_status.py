#-*-coding:utf-8-*-
import MySQLdb
import sys
import subprocess
import time
import datetime
import random
import getopt
###### zhou fei 2014-07-28

from fabric.api import env,run,put,get,local
reload(sys)
sys.setdefaultencoding('gbk')


ywpt_db_conf='/home/mysql/admin/bin/newbin/ywpt_db.conf'
tmp_ywpt_db_conf='/home/mysql/admin/bin/newbin/tmp_ywpt_db.conf'

monitor_db={}
tmp_monitor_db={}
is_completed='N'
g_gmt_create_dt=datetime.datetime.now()
g_gmt_create=g_gmt_create_dt.strftime('%Y%m%d%H%M%S')
g_gmt_modify=g_gmt_create

def main():
    global G_DBID

    try:
        opts, args = getopt.getopt(sys.argv[1:], "Hh:d:", ["help", "dbid="])
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
        if name in ("-d","--dbid"):
           G_DBID=value
           print "DBID:"+G_DBID
         
    check_keepalived_status(G_DBID)

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

def get_server_pass(t_db_id):
    global g_username
    global g_password
    global g_hostname,g_host_id,g_ip_addr
    mysqlcur.execute("set names utf8")
    t_sql='SELECT user_account,user_passwd,host_name,ip_addr FROM b_host_config a,b_db_config  b  WHERE a.host_id=b.host_id   AND b.db_id=%s limit 1 '
    mysqlcur.execute(t_sql,(t_db_id,))
    data = mysqlcur.fetchone()
    g_username,g_password,g_hostname,g_ip_addr=data

def insert_data(table_name,varlist):
                get_table_column('sys',table_name)
                mysqlcur.execute("replace into "+table_name+" ("+table_column_mysql+" ) values ("+var_list+")",(varlist))
                mysqldb.commit()

def get_table_column(table_owner,table_name):
    global table_column
    global table_column_mysql
    global var_list
    global table_column_cnt
    read_conf(tmp_ywpt_db_conf,'tmp')
    mysqldbtmp =  MySQLdb.connect(host=tmp_monitor_db.get('ip'), user=tmp_monitor_db.get('user'),passwd=tmp_monitor_db.get('pass'),db=tmp_monitor_db.get('db'),port=int(tmp_monitor_db.get('port')), charset="utf8")
    tmpcur=mysqldbtmp.cursor()
    tmpcur.execute("set names utf8")
    tmpcur.execute("SELECT column_name FROM  COLUMNS WHERE table_name=%s ORDER BY ORDINAL_POSITION",(table_name,))
    data=tmpcur.fetchall()
    table_column=''
    table_column_mysql=''
    table_column_cnt=0
    var_list=''
    for x in data:
       table_column_cnt=table_column_cnt+1
       table_column=table_column+str(x[0])+','
       table_column_mysql=table_column_mysql+'`'+str(x[0])+'`'+','
       var_list=var_list+'%s'+','
    table_column=table_column.rstrip(',')
    table_column_mysql=table_column_mysql.rstrip(',')
    var_list=var_list.rstrip(',')

def check_keepalived_status(t_db_id):
    get_server_pass(t_db_id)
    env.user=g_username
    env.host_string=g_ip_addr+':22'
    env.password = g_password
    k_process=run('ps -ef|grep keepalived|grep -v grep|wc -l')
    if int(k_process) < 3:
       t_msg=g_ip_addr+':Keepalived is STOP!!!!!'
       is_completed='N'
       t_tmd5='keepalived is stop!!'
       t_id=monitor_db.get('hid')+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+str(random.randint(10000,90000))
       info=[t_id,t_db_id,t_msg,is_completed,t_tmd5,g_gmt_create,g_gmt_modify,'0','20']
       insert_data('b_error_msg',info)
'''
if __name__=="__main__":
          g_db_id=sys.argv[1]
          check_keepalived_status(g_db_id)
'''
def usage():
    print '''
---------------usage:------------------
python get_keepalived_status_new.py -d dbid
or
python get_keepalived_status_new.py --dbid=dbid
---------------------------------------
'''
         
if __name__=="__main__":
   main()
