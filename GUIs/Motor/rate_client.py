import socket as soc
from time import sleep
import threading
import configparser
import numpy as np

class rate_client:

    #length of each rate information. In the used protocol the length of the message is the no of valid numbers of the MHz measurement +1 times 2 (two channels A and B) + 1 character for the seperator.
    msg_length = 13

    #info about the server to connect to
    port = 2610
    address = "131.188.167.100"#"192.168.0.103"
    
    #client socket that is used to connect to the rate server
    socket = None
    
    #status of the client's listening functionality
    still_listening = False
    #thread which executes the listening function
    listen_thread = None
    
    #value of the last transmitted rates
    rateA = None
    rateB = None
    
    def __init__(self):
        # Find address, message length and port to connect to
        global_config = configparser.ConfigParser()
        global_config.read('../global.conf')
        if "controller" in global_config:
            self.address=global_config["controller"]["address"]
        else:
            print("Error in the 'global.config'-file. The file does not contain the section 'controller'. Please correct!")
            exit()
        if "rate_transmission" in global_config:            
            self.msg_length=int(global_config["rate_transmission"]["msg_length"])
        else:
            print("Error in the 'global.config'-file. The file does not contain the section 'rate_transmission'. Please correct!")
        self.port = np.loadtxt("/home/pi/Desktop/port.txt") 
        print("rate-client init completed. Configuation: addr {0} port {1} msg_length {2}".format(self.address, self.port, self.msg_length))

        
    #connects the rate client to the rate server
#NEED TO ADD ERROR HANDLING!
    def connect(self):
        #create a client socket to connect to the rate server
        if self.socket is None:
            self.socket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
            self.socket.settimeout(1)
            print("Connecing to {0} on port {1}".format(self.port, self.address))
            self.socket.connect((self.address, self.port))
            self.socket.settimeout(None)
            print("Client started!")    
            
            #routine to start a client thread as soon as a connection is requested (in own thread)
            self.listen_thread = threading.Thread(target=listen, args=[self])
            self.still_listening=True
            self.listen_thread.start()
            if self.listen_thread != None:
                print("Client connected to {1} on Port {0} and is listening!".format(self.port, self.address))  
        else:
            print("Error in the connect method of the rate client! There shouldn't be a socket but in fact there is! Did you connect once too often?")
        

    #returns the value of the last rate in channel A transmitted
    def getRateA(self):
        if self.rateA != None:
            if self.still_listening:
                return self.rateA
            else:
#               print("TEST")
                raise RuntimeError("Connection to server lost!")
        else:
            #print("No rate has yet been received")
            return -1
            

    #returns the value of the last rate in channel B transmitted
    def getRateB(self):
        if self.rateB != None:
            if self.still_listening:
                return self.rateB
            else:
                raise RuntimeError("Connection to server lost!")
        else:
            #print("No rate has yet been received")
            return -1

    #stops the client and closes all connections
    def stop(self):
        self.socket.shutdown(soc.SHUT_RDWR)
        self.socket.close()
        print("Shutdown the client and closed the socket!")
        self.socket = None;
    
#makes the client listen to incoming rates
def listen(self):
    while self.still_listening:
        chunks = []
        bytes_recd = 0
        while bytes_recd < self.msg_length:
            chunk = self.socket.recv(min(self.msg_length - bytes_recd, 2048))
            if chunk == b'':
                if self.socket != None:
                    print("Socket connection broken. Destroyed on purpose?")
                    self.still_listening = False
                    break
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        if self.still_listening == False:
            break
        org=str(b''.join(chunks))
        parts=org.split(";")
        self.rateA=float(parts[0].split("'")[1])
        self.rateB=float(parts[1].split("'")[0])
