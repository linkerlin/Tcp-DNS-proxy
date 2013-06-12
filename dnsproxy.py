#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys
import struct
import threading
import SocketServer
import optparse

import config
from dnsserver import DNSServer
from servers import Servers


reload(sys)
sys.setdefaultencoding("utf-8")

#---------------------------------------------------------------
# bytetodomain
# 03www06google02cn00 => www.google.cn
#--------------------------------------------------------------
def bytetodomain(s):
    domain = ''
    i = 0
    length = struct.unpack('!B', s[0:1])[0]

    while length != 0:
        i += 1
        domain += s[i:i + length]
        i += length
        length = struct.unpack('!B', s[i:i + 1])[0]
        if length != 0:
            domain += '.'

    return domain


class DNSProxy(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    SocketServer.ThreadingMixIn.daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address=("0.0.0.0", 53), VERBOSE=2):
        self.VERBOSE = VERBOSE
        print "listening at:", address
        SELF = self

        class ProxyHandle(SocketServer.BaseRequestHandler):
            # Ctrl-C will cleanly kill all spawned threads
            daemon_threads = True
            # much faster rebinding
            allow_reuse_address = True

            def handle(self):
                data = self.request[0]
                socket = self.request[1]
                addr = self.client_address
                DNSProxy.transfer(SELF, data, addr, socket)

        SocketServer.UDPServer.__init__(self, address, ProxyHandle)

    def loadConfig(self, DNSS):
        self.DNSS = DNSS
        self.servers = Servers()
        for s in DNSS:
            ip, port, type_of_server = s
            self.servers.addDNSServer(DNSServer(ip, port, type_of_server))


    def transfer(self, querydata, addr, server):
        if not querydata: return
        domain = bytetodomain(querydata[12:-4])
        qtype = struct.unpack('!h', querydata[-4:-2])[0]
        print 'domain:%s, qtype:%x, thread:%d' % \
              (domain, qtype, threading.activeCount())
        sys.stdout.flush()
        response = None
        for i in range(9):
            response, dnsserv = self.servers.query(querydata)
            if response:
                # udp dns packet no length
                server.sendto(response[2:], addr)
                if int(self.VERBOSE) > 0:
                    dnsserv.showInfo(querydata, 0)
                    dnsserv.showInfo(response[2:], 1)
                break
        if response is None:
            print "[ERROR] Tried 9 times and failed to resolve %s" % domain
        return


if __name__ == '__main__':
    print '>> Please wait program init....'
    print '>> Init finished!'
    print '>> Now you can set dns server to 127.0.0.1'

    parser = optparse.OptionParser()
    parser.add_option("-v", dest="verbose", default="0", help="Verbosity level, 0-2, default is 0")
    options, _ = parser.parse_args()

    proxy = DNSProxy(VERBOSE=options.verbose)
    proxy.loadConfig(config.DNSS)

    proxy.serve_forever()
    proxy.shutdown()