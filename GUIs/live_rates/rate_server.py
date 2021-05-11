import socket as soc
import threading
import time

class server:

	#length of each rate information. In the used protocol the length of the message is the no of valid numbers of the MHz measurement +1 times 2 (two channels A and B) + 1 character for the seperator.
	msg_length = 13
	
	#listening port and address for the server
	port = 2610 
	address = ""
	connections = 1
	
	#socket used for the serversocket
	serversocket = None
	listen_thread = None
	still_listening = True;
	
	#list of client sockets to send to
	clientsockets = []
	

	def __init__(self):
		#check if config file exists and load it, otherwise standard parameters are kept
		config = configparser.ConfigParser()
		config.read('rate_transmission.conf')
		if "connection" in config:
			self.port=config["connection"]["port"]
			self.address=config["connection"]["address"]
	
	#starts the server by opening a listening socket			
	def start(self):
		#Check if server is already running
		if self.serversocket is None:
			self.serversocket = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
			# create an INET, STREAMing socket
        
			# bind the socket to a host and port
			if self.address=="":
				self.serversocket.bind((soc.gethostname(), self.port))
			else:
				self.serversocket.bind((self.address, self.port))
				
			# make it a server socket that allows for a certain number of connections
			self.serversocket.listen(self.connections)
			
			print("Server started!")	
			
			#routine to start a client thread as soon as a connection is requested (in own thread)
			self.listen_thread = threading.Thread(target=listen, args=[self])
			self.still_listening=True
			self.listen_thread.start()
			if self.listen_thread != None:
				print("Server listens on Port {0} !".format(self.port))	
		else:
			print("Server already started")
			return
    
    #stops the server by closing the listening and all client sockets and destroying them
	def stop(self):
		#stop the thread that listens
		server_cache=self.serversocket
		self.serversocket=None
		self.still_listening=False
		server_cache.shutdown(soc.SHUT_RDWR)
		server_cache.close()
		for i in self.clientsockets:
			i.shutdown(soc.SHUT_RDWR)
			i.close()
			self.clientsockets.remove(i)
		print("Shutdown the server and closed all sockets!")
				
	def sendRate(self, rate):
		rate=str(rate)
		if len(rate) != self.msg_length :
			print("The rate which was supposed to be sent had the wrong length! The configured msg_length is {0} but the one given as a parameter '{1}' had length {2}".format(self.msg_length, rate, len(rate)))
			return
		rate=rate.encode('utf8');
		for i in self.clientsockets:
			sent = i.send(rate)
			if sent == 0:
				print("The Socket connection on one of the sockets is broken. Socket will be eliminated")
				i.shutdown(soc.SHUT_RDWR)
				i.close()
				self.clientsockets.remove(i)
				
def listen(self):
	while self.still_listening:
		# accept connections from outside. The OSError exception ist thrown, when the server is shutdown, becaus the accept routine can't handle well that the socket is closed by another thread.
		try:
			#get new clientsocket from the listening server socket
			(clientsocket, address) = self.serversocket.accept()
			
			# create a new thread for each client and put it in the list of clientsockets
			ct = clientsocket
			self.clientsockets.append(ct)
			print("Created new client socket for new client which connected to the rate server!")
		except OSError:
			if self.still_listening :
				print("There was an error in the accept() statement of the server while listening for incoming connections. How could that be?")
			else:
				print("Successfully ended the server-listening thread!")
				
		
