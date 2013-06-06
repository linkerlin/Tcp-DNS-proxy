#! /usr/bin/python
# -*- coding: utf-8 -*-
# cody by linker.lin@me.com

import socket
import Queue
import time
from threading import *

from bg_worker import bgworker
from connection import Connection

def _lockname(classname):
    return '_%s__%s' % (classname, 'lock')

class LockProxy(object):
    def __init__(self, obj):
        self.__obj = obj
        self.__lock = RLock()
        # RLock because object methods may call own methods
    def __getattr__(self, name):
        def wrapped(*a, **k):
            with self.__lock:
                getattr(self.__obj, name)(*a, **k)
        return wrapped



TIMEOUT = 3
# a connection pool
class ConnectionPool(object):
    def __init__(self, ttl=1):
        self.conn_pool = {}


    def getConnection(self, ip, port, socket_type=socket.SOCK_STREAM, socket_family=socket.AF_INET, timeout=TIMEOUT):
        #print "conn_pool",self.conn_pool
        conn_key = (socket_family, socket_type, ip, port, timeout)
        q = None
        conn = None
        # make sure the queue of conn_key is existed
        if conn_key not in self.conn_pool:
            q = Queue.Queue()
            self.conn_pool[conn_key] = q
        else:
            q = self.conn_pool[conn_key]
            #print q.qsize()
        while conn is None:
            if q.empty():
                def f():
                    if q.qsize() < 1:
                        q.put(Connection(conn_key))

                bgworker.post(lambda: f())
                time.sleep(0.1)
            else:
                conn = q.get_nowait()
        return conn

    def releaseConnection(self, conn):
        if conn is None:
            return
        if conn.isTimeout():
            conn.close()
            return
            # reuse connection
        q = None
        conn_key = conn.getKey()
        if conn_key in self.conn_pool:
            q = self.conn_pool[conn_key]
            q.put(conn)


main_conn_pool = LockProxy(ConnectionPool(100))
if __name__ == "__main__":
    for i in range(100):
        c = main_conn_pool.getConnection('8.8.8.8', 53)
        main_conn_pool.releaseConnection(c)
        c = main_conn_pool.getConnection('8.8.8.8', 53)
        main_conn_pool.releaseConnection(c)
