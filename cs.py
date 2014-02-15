#!/usr/bin/env python2
import Queue
import socket
import threading
import time
from netaddr import IPNetwork
from struct import *

THREAD_COUNT = 100

socket.setdefaulttimeout(0.05)

def extractInfo(txt):
    txt=txt.replace('\377', '')
    if txt.find('Dota 2') > 0:
        print ' DotA Server IP appended '
        return 'dota', 'Dota 2'
    elif txt.find('Counter-Strike') > 0:
        if txt.find('m') == 0:
            serv_name=txt.split('\0') [1]
            serv_map=txt.split('\0') [2]
            serv_engine=txt.split('\0') [3]
            serv_game=txt.split('\0') [4]
            players = unpack('bb',txt.split('\0')[5][:2])
            #if txt.split('\0')[9][:1] == '\0':
            #    protected = True
            #else:
            #    protected = False
            print ' CS Server IP appended '
            return 'cs', serv_name+" -- "+serv_map+" ("+str(players[0])+"/"+str(players[1])+" players)"
    return '', ''

class ClientThread (threading.Thread):
    def run (self):
        global serverListCS, serverListDotA
        ip = None
        while True:
            if not ipPool.empty():
                try:
                    ip = ipPool.get_nowait()
                except Exception,e:
                    break
            else:
                break
            if ip != None:
                found = False
                serverLine = ''+ip+'\t:\t'
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                try:
                    sock.connect((ip, 27015))
                except Exception,e:
                    sock.close()
                    print e
                    break
                sock.send('\377\377\377\377TSource Engine Query\0')
                while 1:
                    try:
                        text=sock.recv(1024)
                        print ' Message Received from '+ip
                    except Exception,e:
                        break
                    if not text:
                        break
                    found = True
                    game, info = extractInfo(text)
                    if game != '':
                        serverLine += info
                        break
                    else:
                        found = False
                        break
                if found:
                    if game == 'dota':
                        serverListDotA.append(serverLine)
                    elif game == 'cs':
                        serverListCS.append(serverLine)
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()

# BITS Student subnet (Updated)
# Still a list in lieu of future changes
subnetList = ["172.17." + str(x) + ".0/24" for x in xrange(1,38)]

ipPool = Queue.Queue(0)
global serverListDotA, serverListCS
serverListDotA = []; serverListCS = []
fileName = "cs.txt"

def checkIPs():
    global serverListCS, serverListDotA
    serverListDotA = []
    serverListCS = []
    for subnet in subnetList:
        for ip in IPNetwork(subnet).iter_hosts():
            ipPool.put('%s' % ip)
    for x in xrange(THREAD_COUNT):
        ClientThread().start()
    while threading.activeCount() > 1:
        time.sleep(1)

while True:
    checkIPs()
    serverList = []
    serverList += ["","CS Servers List: (Auto updated every minute)",""]
    serverList += serverListCS
    serverList += ["","DotA Servers List: (Auto updated every minute)",""]
    serverList += serverListDotA
    serverList.append("")
    serverList.append("Last updated at: "+time.strftime('%I:%M %p, %b %d, %Y'))
    serverList.append("Anyone interested in the code can look here: https://github.com/hyades/cscheck")
    print time.strftime('%I:%M %p, %b %d, %Y'), '-- MARK --'
    f = open(fileName, "w")
    for s in serverList:
        f.write(s)
        f.write('\n')
    f.close()
    time.sleep(50)
