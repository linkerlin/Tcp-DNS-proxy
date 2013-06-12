#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'linkerlin'
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

from dnsserver import DNSServer
from random import sample


class Servers(object):
    def __init__(self):
        self.dnsservers = {}

    def addDNSServer(self, dns_server):
        assert isinstance(dns_server, DNSServer)
        self.dnsservers[dns_server.address()] = dns_server

    def query(self, query_data):
        # random select a server
        key = sample(self.dnsservers, 1)[0]
        print key
        server = self.dnsservers[key]
        return server.query(query_data)




if __name__ == "__main__":
    ss = Servers()
    s = DNSServer("8.8.8.8")
    ss.addDNSServer(s)
