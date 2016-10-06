#!/usr/bin/env python3

import os
import os.path
import sys
import subprocess
import http.server
import socketserver
import csv

from systemd import journal
from random_words import RandomWords
from random_words import RandomNicknames

PORT = 8000
ETCD_TOKEN_FILE = "etcd_discovery_token"

ipidx = 0
IPLIST = "iplist.csv"
ips = []

journal.send('ETCD_TOKEN_FILE')

work_dir = sys.argv[1]
server_ip = sys.argv[2]
port = int(sys.argv[3])

journal.send(work_dir, FIELD2=server_ip, FIELD3=port)

try:
    with open(work_dir + "/" + ETCD_TOKEN_FILE, "r") as f:
        etcd_discovery_token = f.read()
except FileNotFoundError:
    with open(work_dir + "/" + ETCD_TOKEN_FILE, "w") as f:
        print("Creating new etcd discovery token")

        etcd_discovery_token = subprocess.check_output(["wget", "-qO-", "https://discovery.etcd.io/new?size=3"]).decode("utf-8")
        f.write(etcd_discovery_token)

print("etcd discovery token: %s" % etcd_discovery_token)
journal.send("etcd discovery token: %s" % etcd_discovery_token)


try:
    with open(work_dir + "/" + IPLIST, "r") as iplistfile:
        ips_file = csv.DictReader(iplistfile)

        iplistfile.seek(0)
        for index, row in enumerate(ips_file, start=0):
            ip = {}
            ip["address"] = str(row["ipaddress"])
            print("Static IP discovered: %s" % ip["address"])
            ips.append(ip)
except FileNotFoundError:
        print("unable to open %s" % work_dir + "/" + IPLIST)   

class PxeHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):

        global ipidx

        print("Access from %s" % self.client_address[0])

        try:
            template = open(work_dir + self.path).read()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

        # increment the counter only when the clients request the cloud-config.yml file
        if self.path.endswith(".yml"):

            ip = ips[ipidx]
            ipidx += 1
            client_ip = ip["address"]
             
            private_ip = client_ip.split(".")
        else:
            client_ip = self.client_address[0]
            private_ip = self.client_address[0].split(".")
            
        private_ip2 = "10.12.69." + private_ip[3]
        private_ip3 = "10.13.69." + private_ip[3]
        private_ip4 = "10.14.69." + private_ip[3]
        private_ip5 = "10.15.69." + private_ip[3]

        rw = RandomWords()
        word = rw.random_word()
        rn = RandomNicknames()
        nick = rn.random_nick(gender='f')
        
        #name = nick + "-" + word.title()
        name = nick + "-" + word
        
        print (name)
        print (private_ip2)
        
        # substite for Fleet instance names so it doesn't break parsing
        instance = "%i"
        
        options = {
                "server_ip": server_ip,
                "client_ip": self.client_address[0],
                "public_ip": client_ip,
                "private_ip": private_ip2,
                "private_ip2": private_ip3,
                "private_ip3": private_ip4,
                "private_ip4": private_ip5,
                "client_ip_dash": self.client_address[0].replace(".", "-"),
                "etcd_discovery_token": etcd_discovery_token,
                "instance": instance,
        }
            
        self.wfile.write(bytes(template % options, "utf-8"))

Handler = http.server.SimpleHTTPRequestHandler

httpd = socketserver.TCPServer((server_ip, port), PxeHandler)

print("serving at %s:%s" % (server_ip, port))
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass

httpd.server_close()
