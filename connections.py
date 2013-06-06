#! /usr/bin/python
# -*- coding: utf-8 -*-
# cody by linker.lin@me.com

import socket
import Queue
import time

from bg_worker import bgworker
from connection import Connection


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
        while conn is None:
            if q.empty():
                def f():
                    q.put(Connection(conn_key))

                bgworker.post(lambda: f())
                time.sleep(0.1)
            else:
                conn = q.get_nowait()
        return conn

    def releaseConnection(self, conn):
        if conn is None:
            return
        conn.close()


main_conn_pool = ConnectionPool(100)
if __name__ == "__main__":
    for i in range(100):
        c = main_conn_pool.getConnection('8.8.8.8', 53)
        main_conn_pool.releaseConnection(c)
        c = main_conn_pool.getConnection('8.8.8.8', 53)
        main_conn_pool.releaseConnection(c)
