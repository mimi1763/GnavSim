import sys
from sys import stdin, exit
from time import sleep, localtime
from weakref import WeakKeyDictionary
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server

# Multiplayer stuff -----------------
HOST = "localhost"
PORT = 112

class ClientChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		self.nickname = "anonymous"
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		self._server.DelPlayer(self)
	
	##################################
	### Network specific callbacks ###
	##################################
	
	def Network_message(self, data):
		self._server.SendToAll({"action": "message", "message": data['message'], "who": self.nickname})
	
	def Network_nickname(self, data):
		self.nickname = data['nickname']
		self._server.SendPlayers()

	def Network_command(self, data):
		"""
		Command types:
		0 : swap with player
		1 : draw drom deck
		2 : knock on table (when being handed the Narren card at start)
		"""
		cmd = data['command']
		if command == 'swap':
			return (0, data['player']) #tuple: (cmd type, data: player swapping with)
		elif command == 'draw':
			return 1 #cmd type
		elif command == 'knock':
			return 2 #cmd type
		else:
			return -1 #do nothing

class ChatServer(Server):
	channelClass = ClientChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.players = WeakKeyDictionary()
		print('Server launched')
	
	def Connected(self, channel, addr):
		self.AddPlayer(channel)
	
	def AddPlayer(self, player):
		print("New Player" + str(player.addr))
		self.players[player] = True
		self.SendPlayers()
		print("players", [p for p in self.players])
	
	def DelPlayer(self, player):
		print("Deleting Player" + str(player.addr))
		del self.players[player]
		self.SendPlayers()
	
	def SendPlayers(self):
		self.SendToAll({"action": "players", "players": [p.nickname for p in self.players]})
	
	def SendToAll(self, data):
		[p.Send(data) for p in self.players]
	
	def Launch(self):
		while True:
			self.Pump()
			sleep(0.0001)

# ----------------------------------------------------------------
if len(sys.argv) != 2:
	host = HOST
	port = PORT
else:
	host, port = sys.argv[1].split(":")
	port = int(port)
print ("Starting gnav server on %s and port %d..." % (host, port))
server = ChatServer(localaddr=(host, port))
server.Launch()