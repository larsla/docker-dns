from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server

import docker
import os


import socket
import fcntl
import struct


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


class DockerResolver(object):

    def __init__(self):

        self.base_url = 'unix://var/run/docker.sock'
        if 'DOCKER_HOST' in os.environ:
            self.base_url = os.environ['DOCKER_HOST']

        self.interface = 'eth0'
        if 'INTERFACE' in os.environ:
            self.interface = os.environ['INTERFACE']

        self.docker = docker.Client(base_url=self.base_url,
                                    version='1.6',
                                    timeout=10)

    def _dockerQuery(self, query):
        name = query.name.name

        parts = name.split('.')
        host = parts[0]

        address = False

        for container in self.docker.containers():
            data = self.docker.inspect_container(container['Id'])
            if data['Config']['Hostname'] == host:
                address = data['NetworkSettings']['IPAddress']

        if not address:
            return False

        answer = dns.RRHeader(
            name=name,
            payload=dns.Record_A(address=b'%s' % address, ttl=60))
        answers = [answer]
        authority = []
        additional = []
        return answers, authority, additional

    def _nsQuery(self, query):
        name = query.name.name
        answer = dns.RRHeader(
            type=query.type,
            name=name,
            payload=dns.Record_NS(get_ip_address(self.interface), ttl=60))

        answers = [answer]
        authority = []
        additional = []
        return answers, authority, additional

    def query(self, query, timeout=None):
        if query.type == dns.A:
            print "Got A query for %s" % query.name
            answer = self._dockerQuery(query)
            if answer:
                return defer.succeed(answer)
            else:
                return defer.fail(error.DomainError())
        elif query.type == dns.NS:
            print "Got NS query for %s" % query.name
            return defer.succeed(self._nsQuery(query))
        else:
            print "Got unknown query of type %s for %s" % (query.type, query.name)
            return defer.fail(error.AuthoritativeDomainError())


def main():
    """
    Run the server.
    """
    factory = server.DNSServerFactory(
        clients=[DockerResolver()]
    )

    protocol = dns.DNSDatagramProtocol(controller=factory)

    reactor.listenUDP(53, protocol)
    reactor.listenTCP(53, factory)

    reactor.run()


if __name__ == '__main__':
    raise SystemExit(main())
