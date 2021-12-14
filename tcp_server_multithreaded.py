import socket, threading
import select
import time
from datetime import datetime

default_order = '0,Opera by Ivan Aivazovsky,1,Diffusion,0,50'
orderids = []
orders = []
data_lock = threading.Lock()
bot_lock = threading.Lock()

connections = []


def injest_orders(s):
    while(True):
        with data_lock:
            f = open('./serverfile.txt', 'r')
            t = f.read()
            f.close()
            f = open('./serverfile.txt', 'w')
            t1 = t.split('\n')
            for e in t1:
                eid = (e.split(','))[0]
                if(e != ''):
                    #if(not(eid in orderids)): #remove this check for production!
                    orders.append([0,e,''])
                    #orderids.append(eid) 
            f.write('')
            f.close()
            print(orders)

            out = ''
            for o in orders:
                for e in o:
                    out += str(e) + ','
                out += '\n'

            f = open('./currentorderlist.txt', 'w')
            t = f.write(out)
            f.close()

            #out = ""
            #for c in connections:
            #    out = str(c.fileno()) + " "
            #print(out)
        time.sleep(s)


class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.clientID = 'Nil'
        print ("New connection added: ", clientAddress)
    def run(self):
        try:
            print ("Connection from : ", clientAddress)
            start = time.time()
            on = True
            curr_order = ''
            state = 0 #has not recieved ID
            tlen = 0
            t = 0
            timeout_in_seconds = 300#60*60*2
            #self.csocket.setblocking(0)
            self.csocket.settimeout(timeout_in_seconds)
            print(self.csocket.gettimeout())
            dead = False
            msg = b''
            while on:
                #print("%s ping"%(self.clientID))
                #ready = select.select([self.csocket], [], [], timeout_in_seconds)
                try:
                    data = self.csocket.recv(2048)
                except socket.timeout:
                    dead = True

                #print(data)
                if(data == -1 or len(data) == 0):
                    dead = True

                if(dead):
                    print ("Client at ", clientAddress , " has gone silent...")
                    #add order to discord bot
                    dsc = self.clientID.split(',')
                    dsc = dsc[1]
                    botorder = '\nin 906761956894076968,post text,|Client %s has gone silent, @%s\n'%(self.clientID, dsc)
                    f = open('./botfile.txt', 'a')
                    f.write(botorder)
                    f.close()
                    with data_lock:
                        i = 0
                        while(i < len(orders)):
                            if(orders[i][0] == 1 and orders[i][2] == self.clientID):
                                print("%s FAILED %s"%(self.clientID, orders[i][1]))
                                orders[i][0] = 0
                                orders[i][2] = ''
                                break
                            i += 1
                        break
                #msg = data.decode()
                #print("%s pong"%(self.clientID))
                toDigest = len(data)
                c = 0
                while(c < toDigest):
                    msg = msg + data[c:c+1]
                    if(state < 4):
                        print(msg)
                    t += 1
                    if(state == 0): #get length of ID
                        tlen = int.from_bytes(msg, "little")
                        msg = b''
                        t = 0
                        state = 1
                    elif(state == 1 and t >= tlen):
                        #decode ID
                        self.clientID = msg.decode()
                        print("Client is %s"%(self.clientID))
                        msg = b''
                        t = 0
                        state = 2
                        tlen = 2
                        #send fresh order
                        out = default_order
                        curr_order = default_order
                        with data_lock:
                            i = 0
                            while(i < len(orders)):
                                if(orders[i][0] == 0):
                                    orders[i][0] = 1
                                    out = orders[i][1]
                                    orders[i][2] = self.clientID
                                    curr_order = orders[i][1]
                                    break
                                i += 1
                        print("sending %s order %s"%(self.clientID, out))
                        out = bytes(out, 'UTF-8')
                        outlen = len(out)
                        outlen = outlen.to_bytes(2, 'little')
                        self.csocket.send(outlen+out)
                    elif(state == 2 and t >= tlen): #waiting for response code
                        t = 0
                        code = int.from_bytes(msg, "little")
                        if(code == 404):
                            #some failure occured, mark order as incomplete
                            with data_lock:
                                i = 0
                                while(i < len(orders)):
                                    if(orders[i][0] == 1 and orders[i][2] == self.clientID):
                                        print("%s FAILED %s"%(self.clientID, orders[i][1]))
                                        orders[i][0] = 0
                                        orders[i][2] = ''
                                        break
                                    i += 1
                                on = False
                                break
                        elif(code == 222):
                            print("client %s is working"%(self.clientID))
                            msg = b''
                            state = 2
                            tlen = 2 #loop back
                        else:
                            #otherwise success code
                            msg = b''
                            state = 3
                            tlen = 8
                    elif(state == 3 and t >= tlen): #waiting for length of image
                        t = 0
                        tlen = int.from_bytes(msg, "little")
                        msg = b''
                        state = 4
                    elif(state == 4 and t >= tlen): #get image
                        t = 0
                        dt = (datetime.now()).strftime("%m_%d_%Y, %H:%M:%S")
                        img_targ = "./output/" + curr_order + "_" + dt + "_" + self.clientID + ".png"
                        f = open(img_targ, 'wb')
                        f.write(msg)
                        f.close()
                        #success, mark order as complete
                        with data_lock:
                            i = 0
                            while(i < len(orders)):
                                if(orders[i][0] == 1 and orders[i][2] == self.clientID):
                                    print("%s COMPLETED %s"%(self.clientID, orders[i][1]))
                                    orders[i][0] = 2
                                    orders[i].pop() #remove it from the orders queue
                                    break
                                i += 1
                        #add order to discord bot
                        botorder = '\nin 906761956894076968,post image,|%s\n'%(img_targ)
                        botorder = botorder + 'in 906761956894076968,post text,|%s'%(curr_order)
                        f = open('./botfile.txt', 'a')
                        f.write(botorder)
                        f.close()
                        msg = b''
                        tlen = 0
                        #start from beginning
                        state = 0
                    c += 1
            print ("Client at ", clientAddress , " disconnected...")
        except ConnectionResetError:
            print ("Client at ", clientAddress , " reset their connection...")
            with data_lock:
                i = 0
                while(i < len(orders)):
                    if(orders[i][0] == 1 and orders[i][2] == self.clientID):
                        print("%s FAILED %s"%(self.clientID, orders[i][1]))
                        orders[i][0] = 0
                        orders[i][2] = ''
                        break
                    i += 1



print("starting up data loop thread...")
x = threading.Thread(target=injest_orders, args=(32,))
x.start()

LOCALHOST = "192.168.1.246"
PORT = 13370
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for client request..")
while True:
    server.listen(1)
    clientsock, clientAddress = server.accept()
    connections.append(clientsock)
    newthread = ClientThread(clientAddress, clientsock)
    newthread.start()