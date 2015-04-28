__author__ = 'secastro'

import sys
import dns.reversename
import ipaddr
from twisted.names import client, error
from twisted.internet import reactor
from twisted.internet import defer, task
import argparse
import json


class ReverseLookupService:
    resolver = None
    ip_info = {}

    def __init__(self):
        self.name = 'LookUp'
        self.resolver = client.Resolver('/etc/resolv.conf')
        self.num_workers = 4
        self.lookup_list = []

    def _receive_dns_response(self, records, addr):
        """
        Receives TXT records and parses them
        """
        answers, authority, additional = records
        if answers:
            for x in answers:
                try:
                    self.ip_info[addr] = dict(name=str(x.payload.name))
                except ValueError:
                    self.ip_info[addr] = dict(name=addr)
        else:
            self.ip_info[addr] = dict(name="None")

    def _handle_dns_error(self, failure, addr):
        """
        Print a friendly error message if the domainname could not be
        resolved.
        """
        failure.trap(error.DNSNameError)
        self.ip_info[addr] = dict(name="None")

    def _send_dns_query(self, entry):
        [qname, addr] = entry
        d = self.resolver.lookupPointer(qname)
        d.addCallback(self._receive_dns_response, addr)
        d.addErrback(self._handle_dns_error, addr)
        return d
    
    def _do_parallel_dns(self):
        coop = task.Cooperator()
        work = (self._send_dns_query(name) for name in self.lookup_list)
        return defer.DeferredList([coop.coiterate(work) for i in xrange(self.num_workers)])

    def lookup_many(self, addr_list):
        self.lookup_list = []
        for addr in addr_list:
            try:
                a = ipaddr.IPv4Address(addr)
                if a.is_private:
                    self.ip_info[addr] = dict(name="Private")
                else:
                    self.lookup_list.append([dns.reversename.from_address(addr).to_text(), addr])
            except ipaddr.AddressValueError:
                self.ip_info[addr] = dict(name="Invalid")

        finished = self._do_parallel_dns()

        finished.addCallback(lambda ignored: reactor.stop())

        reactor.run()

        return self.ip_info

    def lookup_one(self, addr):
        return self.lookup_many([addr])
