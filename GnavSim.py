#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
import random
import time
import PodSixNet.Channel
import PodSixNet.Server
from PodSixNet.Connection import ConnectionListener, connection

PLAYERS = ["Kristoffer", "Matias", "Johannes"] #, "Miriam", "Mikkel", "Emil", "Oivind", "Ask"
MAX_ROUNDS = 1
SWAP_THRESHOLDNUMBER = 4
SWAP_FUZZINESS = 0.0 #Simulates human error. 0.1 = 10% chance of making a mistake.

# Multiplayer stuff -----------------

class ClientChannel(PodSixNet.Channel.Channel):

	gameId = 0

	def Network(self, data):
		print (data)

	def Network_myaction(self, data):
		print ("myaction: ", data)

	def Network_place(self, data):
		#player number (0 or 1)
		num = data["num"]

		#id of game given by server at start
		self.gameId = data["gameId"]

		#tells server to print something
		self._server.PrintMessage

class MyServer(PodSixNet.Server.Server):

	channelClass = ClientChannel
	games = []
	queue = []
	currentIndex = 0
	channels = []

	def __init__(self):
		self.games = []
		self.currentIndex = 0

	def Connected(self, channel, addr):
		print ("new connection: ", channel)

		if self.queue == None:
			self.currentIndex += 1
			channel.gameId = self.currentIndex
			self.queue = Game(channel, self.currentIndex)
		else:
			channel.gameId = self.currentIndex
			self.queue.player1 = channel
			self.queue.player0.Send({"action": "startGame", "player":0, "gameId": self.queue.gameId})
			self.queue.player1.Send({"action": "startGame", "player":1, "gameId": self.queue.gameId})
			self.games.append(self.queue)
			self.queue = None

	def PrintMessage(self, data, gameId, num):
		game = [a for a in self.games if a.gameId == gameId ]
		if len(game) == 1:
			game[0].PrintMessage(data, num)

class GnavGame(ConnectionListener):

	num = 0
	turn = False
	gameId = 0
	running = False
	address = 'localhost:111'

	def __init__(self):
		self.connectToServer()
		self.running = False

		while not self.running:
		    self.Pump()
		    connection.Pump()
		    time.sleep(0.01)

		#determine attributes from player #
		if self.num == 0:
			self.turn = True
		else:
			self.turn = False

	def connectToServer(self):
		self.address = input("Address of Server: ")
		try:
			if not self.address:
				host, port = "localhost", 111
			else:
				host,port = self.address.split(":")
				self.Connect((host, int(port)))
		except:
			print ("Didn't work! Error Connecting to Server")
			print ("Usage:", "host:port")
			print ("e.g.", "localhost:111")
			exit()
		print ("Wohoo! Boxes client started!")

	def update(self):
		time.sleep(0.01)		
		connection.Pump()
		self.Pump()

	def Network_startgame(self, data):
		self.running = True
		self.num = data["player"]
		self.gameid = data["gameId"]

class Game():

	turn = 0
	player0 = 0
	player1 = 0
	gameId = 0

	def __init__(self, player0, currentIndex):
		self.turn = 0
		self.player0 = player0
		self.player1 = None
		self.gameId = currentIndex

	def PrintMessage(self, data, gameId, num):
		print (data)
		data["hasBeenOnServer"] = True
		data["message"] = "Hello!"
		self.player0.Send(data)
		self.player1.Send(data)

def StartOrMPGame():
	choice = Human('', 666).inputYesNo("Is this going to be the multiplayer server")
	if choice:
		myServer = MyServer()
		while True:
			myServer.Pump()
			time.sleep(0.0001)
	else:
		gg = GnavGame()
		while True:
			gg.update()

# End multiplayer stuff -------------

class Player(object):

	pid = 0
	name = ""
	score = 5
	heldCard = None
	wins = 0
	losses = 0

	TXT_WANT_TO_SWAP = "Jeg vil gjerne bytte med deg."
	TXT_ACCEPT_SWAP = "Jada, her er kortet mitt."
	TXT_KNOCK = " banker tre ganger på bordet. <BANK, BANK, BANK>"
	TXT_PASSES = " sier 'Jeg står.'"
	TXT_NO_WAY_FOOL = " and thinks ''Aldri i livet, %s har jo narren!''"

	def __init__(self, name, pid):
		self.name = name
		self.pid = pid

	def setHeldCard(self, card, silent = False):
		self.heldCard = card
		#if not silent: print ("INFO: " + self.name + " now has: " + self.heldCard.name)

	def drawFromDeck(self, deck):
		self.discard(deck)
		self.setHeldCard(deck.draw())

	def discard(self, deck):
		if not (self.heldCard == None):
			deck.discard(self.heldCard)
		self.heldCard = None
	
	def requestSwap(self, toPlayer):
		print (self.sayTo(toPlayer, 0) + quote(self.TXT_WANT_TO_SWAP))

	def answerSwap(self, fromPlayer):
		val = self.heldCard.value
		if not (val > 16):
			print (self.sayTo(fromPlayer, 1) + quote(self.TXT_ACCEPT_SWAP))
		else:
			reply = Card.statements[val] if val < 21 else Card.statements[val].upper() 
			print (self.sayTo(fromPlayer, 1) + quote(reply))
		return val

	def swapWithPlayer(self, fromPlayer):
		print ("INFO: %s swaps cards with %s." % (self.name, fromPlayer.name))
		card = self.heldCard
		self.setHeldCard(fromPlayer.heldCard)
		fromPlayer.setHeldCard(card)

	def processAnswer(self, returnedCardValue):
		if (returnedCardValue > 16):
			if (returnedCardValue > 16 and returnedCardValue < 21): #huset, hesten, katten & dragonen
				return 1 #Loses 1 score and must ask next player.
			elif (returnedCardValue == 21): #gjoken
				return 2 #All other players than the one with Gjoken loses 1 score and turn is over.
		else:
			return 0 #Nothing happens.

	def addToScore(self, value):
		self.score += value
		verb = ("added" if value > 0 else "subtracted")
		prepos = ("to" if value > 0 else "from")
		print ("%s %s %d %s score." % (self.name, verb, abs(value), prepos))

	def sayTo(self, toPlayer, typ):
		verb = ' asks ' if typ == 0 else ' answers '
		return self.name + verb + toPlayer.name + ": "

	def sayPass(self):
		return self.name + self.TXT_PASSES

	def sayNoFool(self, player):
		return self.TXT_NO_WAY_FOOL % (player.name)

	def knockOnTable(self):
		print (self.name + self.TXT_KNOCK)
		return True

	def testForSwap(self, toPlayer = None):
		value = self.heldCard.value
		swap = SWAP_THRESHOLDNUMBER + 4
		chance = random.uniform(0.0, 1.0)
		if (chance < SWAP_FUZZINESS):
			swap -= 1
		elif (chance > 1 - SWAP_FUZZINESS):
			swap += 1

		if (value > swap):
			return False #Player doesn't want to swap and will say pass.
		else:
			return True #Player wants to swap.

class Card(object):
	
	types = {
		'Gjøken': 21,
		'Dragonen': 20,
		'Katten': 19,
		'Hesten': 18,
		'Huset': 17,
		'(12)': 16,
		'(11)': 15,
		'(10)': 14,
		'(9)': 13,
		'(8)': 12,
		'(7)': 11,
		'(6)': 10,
		'(5)': 9,
		'(4)': 8,
		'(3)': 7,
		'(2)': 6,
		'(1)': 5,
		'Narren': 4,
		'Potten': 3,
		'Uglen': 2,
		'(0)': 1
	}

	statements = {
		21: 'Stå for gjøk!',
		20: 'Hogg av!',
		19: 'Kiss!',
		18: 'Hest forbi!',
		17: 'Hus forbi!'
	}

	name = ""
	value = 0

	def __init__(self, name, value):
		self.name = name
		self.value = value

	def __repr__(self):
		return '%s: %d' % (self.name, self.value)

class Deck(object):

	cards = []
	discardPile = []

	def __init__(self):
		for key, val in Card.types.items():
			card = Card(key, val)
			self.cards.append(card)
			self.cards.append(card)
		#self.printCards()
		self.shuffleDeck()

	def shuffleDeck(self):
		print ("*** INFO: The deck is shuffled.")
		random.shuffle(self.cards)

	def draw(self):
		card = None
		if self.isDeckEmpty():
			self.useDiscardPile()
		return self.cards.pop()

	def useDiscardPile(self):
		print ("**** INFO: The discard deck is used.")
		self.cards = self.discardPile
		self.shuffleDeck()
		self.discardPile = []

	def isDeckEmpty(self):
		return len(self.cards) == 0

	def discard(self, card):
		self.discardPile.append(card)
		print ("A %s card was discarded." % (card.name))

	def testLengthSum(self):
		if (len(self.cards) + len(self.discardPile) == 42):
			#print ("All good, sum of piles piles is 42.")
			1 == 1
		else:
			print ("Warning! Sum of piles is not 42.")
			self.printCards()
			self.printCards(True)

	def printCards(self, discarded = False):
		cardsLine = "Discarded: " if discarded else "Cards: "
		cardList = self.discardPile if discarded else self.cards
		for card in cardList:
			cardsLine += card.name + ", "
		cardsLine = cardsLine[:-2]
		print (cardsLine)

class Human(Player):

	human = True

	def __init__(self, name, pid):
		Player.__init__(self, name, pid)

	def setHeldCard(self, card, silent = False):
		self.printGotCard(card.name)
		super(Human, self).setHeldCard(card, silent)

	def knockOnTable(self):
		result = self.inputYesNo("Knock on the table")
		if (result):
			print (self.name + self.TXT_KNOCK)
		return result

	def drawFromDeck(self, deck):
		super(Human, self).drawFromDeck(deck)

	def requestSwap(self, toPlayer):
		#result = self.inputYesNo("Do you want to swap cards with %s" % (toPlayer.name))
		#if (result):
		print (self.sayTo(toPlayer, 0) + quote(self.TXT_WANT_TO_SWAP))
		#return result

	def swapWithPlayer(self, fromPlayer):
		super(Human, self).swapWithPlayer(fromPlayer)

	def printGotCard(self, cardName = ""):
		card = self.heldCard.name if cardName == "" else cardName
		print ("Player %s, you got the card %s." % (self.name, card))

	def inputYesNo(self, question):
		choice = input("%s (y/n)? " % (question))
		return choice.upper() == 'Y'

	def testForSwap(self, toPlayer):
		text = "Do you want to "
		if (toPlayer == "deck"):
			text += "draw from the deck"
		else:
			text += "swap cards with %s" % (toPlayer.name)
		return self.inputYesNo(text)

# ------------- End of classes ---------------		

def playGame():
	players = []

	humanName = enterHumanPlayer()
	human = Human(humanName, len(PLAYERS) + 1)

	for index, name in enumerate(PLAYERS):
		players.append(Player(name, index))

	players.append(human)
	random.shuffle(players)
	deck = Deck()
	round = 1

	while not round > MAX_ROUNDS:
		print ("Round: %d ===> Card pile length: %d -----------------------" % (round, len(deck.cards)))

		#Draw cards for each player
		for player in players:
			player.drawFromDeck(deck)
			if player.heldCard.value == 4: #If player receives Narren
				if player.knockOnTable():
					player.addToScore(1)

		#Play round
		for nbr, player in enumerate(players, 0):
			wantsToSwap = False
			sayPass = player.sayPass()
			if not nbr == len(players) - 1:
				if players[nbr + 1].heldCard.value == 4: #If the other player has Narren...
					if not player.testForSwap(players[nbr + 1]): #Do small chance check if player has forgotten someone knocked 3 times.
						sayPass += player.sayNoFool(players[nbr + 1])
					else:
						wantsToSwap = True
				else:
					if player.testForSwap(players[nbr + 1]): #Only ask to swap if card is 4 or less.
						wantsToSwap = True

				if wantsToSwap:
					if not (askPlayers(nbr, player, players, deck)): #Check if Staa for gjok! is called.
						break
				else:
					print (sayPass)
			else:
				if player.testForSwap("deck"): #Only swap if card is 4 or less.
					print (player.name + " draws from the deck.")
					player.drawFromDeck(deck) #Draw from deck if noone else to swap with.
				else:
					print (sayPass)

		print ("End of round " + str(round) + " ======================================")
		#End of round

		#Calculate scores and stats
		sortedPlayers = sorted(players, key=lambda p: p.heldCard.value, reverse=True)
		winner = sortedPlayers[0]
		winner.wins += 1
		loser = sortedPlayers[len(sortedPlayers)-1]
		loser.losses += 1
		print ("Winner of this round is " + winner.name + " with the card " + winner.heldCard.name)
		winner.addToScore(1)
		print ("Loser of this round is " + loser.name + " with the card " + loser.heldCard.name)
		loser.addToScore(-1)
		#Search for Narren among players
		for player in players:
			if (player.heldCard.value == 4):
				print ("Unfortunately, " + player.name + "'s card at end of round is Narren.")
				player.addToScore(-1)

		#All players toss their cards in the discard pile
		for player in players:
			player.discard(deck)

		deck.testLengthSum()

		mostWins = sorted(players, key=lambda p: p.wins, reverse=True)
		mostLosses = sorted(players, key=lambda p: p.losses, reverse=True)
		highestScore = sorted(players, key=lambda p: p.score, reverse=True)

		scoreLine = "-------> Scores: "

		for player in players:
			thisPly = player.name
			if (player.pid == highestScore[0].pid):
				thisPly = "**" + thisPly.upper() + "**"
			scoreLine += thisPly + ": " + str(player.score) + ", "
		print ("")
		print (scoreLine[:-2])
		print ("GAME STATS: Most wins -> " + mostWins[0].name + ": " + str(mostWins[0].wins) + ", most losses -> " + mostLosses[0].name + ": " + str(mostLosses[0].losses))

		round += 1
		print ("")
		Human("dummy", 666).inputYesNo("Press any key to continue, okay")
		print ("")

	proclaimWinner(highestScore[0])

def askPlayers(nbr, player, players, deck):
	nextAdd = 1
	hasSwapped = False

	while not hasSwapped and (nbr + nextAdd) < len(players):
		print ("%s is now about to ask the next player, %s, if he wants to swap..." % (player.name, players[nbr + nextAdd].name))
		player.requestSwap(players[nbr + nextAdd])
		returnedCardValue = players[nbr + nextAdd].answerSwap(player)
		if returnedCardValue == 4:
			print (":-) Everybody starts laughing and says 'Men " + players[nbr + nextAdd].name + " har jo narren!'")
		result = player.processAnswer(returnedCardValue)
		if (result == 1): #Dragonen, katten, hesten or huset
			player.addToScore(-1)
			nextAdd += 1
		elif (result == 2): #Gjøken
			for ply in players:
				if not (ply.pid == players[nbr + nextAdd].pid):
					ply.addToScore(-1) #All other players loses 1 score.
			return False
		else: #The two players Swap cards
			player.swapWithPlayer(players[nbr + nextAdd])
			hasSwapped = True
		if not hasSwapped: #If player still hasn't swapped after being last in round
			print (player.name + " draws from the deck.")
			player.drawFromDeck(deck)
	return True

def proclaimWinner(player):
	print ("")
	text = "<<<<<<<<<<<<<<<<<< The winner of %d rounds of GNAV is... >>>>>>>>>>>>>>>>>>" % (MAX_ROUNDS)
	print (text)
	print ("<<" + int(len(text) - 4) * " " + ">>")
	spaces = int((len(text) - 2) / 2) - int(len(player.name) / 2)
	print ("<<" + (" " * spaces) + player.name + (" " * (spaces - 2)) + ">>")
	print ("<<" + int(len(text) - 4) * " " + ">>")
	print ("<" * int(len(text) / 2) + ">" * int(len(text) / 2))

def enterHumanPlayer():
	print ("<<< Welcome to Gnav The Card Game >>>")
	print (sys.version)
	return input("Please enter your name: ")

def quote(text):
	return "'" + text + "'"

StartOrMPGame()
playGame()