__author__ = 'maxiao'
# -*- coding:utf-8 -*-
 
import sys
import socket
import time
import struct

f = open("binary_ECG_test7_n.txt")
arr = []
try:
    for line in f:
        arr.append(line[:-1])
finally:
    f.close()
len_arr = len(arr)
print len_arr
 
 
BUF_SIZE = 1024
server_addr = ('127.0.0.1', 8899)
try:
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, msg :
    print "Creating Socket Failure. Error Code : " + str(msg[0]) + " Message : " + msg[1]
    sys.exit()
print "Socket Created!"
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try :
    server.bind(server_addr)
except socket.error, msg:
    print "Binding Failure. Error Code : " + str(msg[0]) + " Message : " + msg[1]
    sys.exit()
print "Socket Bind!"
server.listen(5)
print "Socket listening"
while True:
    try:
        client, client_addr = server.accept()
        print 'Connected by', client_addr
    except socket.error, msg:
        print "Binding Failure. Error Code : " + str(msg[0]) + " Message : " + msg[1]
        sys.exit()
    i = 0
    k = 0
    while True:
         print k
         k = k + 1
         print arr[i]

         b = arr[i].split()
         len_b = len(b)
         j = 1
         while j <= len_b:
            b_int = int(b[j-1])
            client.sendall(struct.pack("B", b_int))
            j = j + 1
            #time.sleep(1)

         if i < 24:
             i = i + 1
         else:
             i = 0
         time.sleep(1)
server.close()
print "Socket Closed!"