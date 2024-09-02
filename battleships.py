from time import sleep
import random
import cmath

for i in range(1, 0):
	print('e')

helpMsg = "\na help message will be here soon\n"

letters = "abcdefghij"
numbers = "0123456789"

ShipTypes = { "carrier": 5, "battleship": 4, "cruiser": 3, "sub": 3, "destroyer": 2 }

allComplexes = frozenset([complex(x, y) for x in range(10) for y in range(10)])
identityComplexes = { 1j, -1j, 1+0j, -1+0j }

class BattleShipsPlayer:
	# autofill is for testing purposes only
	def __init__(self, name, **kwargs):
		self.name = name
		self.hitCoords, self.missedCoords, self.sunkCoords = set(), set(), set()
		self.shipCoords = {}
		self.opponent = None
		
		for shipType in ShipTypes:
			self.shipCoords[shipType] = set()
		
		autofill, computer = "autofill" in kwargs and kwargs["autofill"], "computer" in kwargs and kwargs["computer"]
		self.computer = computer
		
		if autofill and not computer:
			i = 0
			for shipType in ShipTypes:
				for j in range(ShipTypes[shipType]):
					self.shipCoords[shipType].add(complex(i, j))
				i += 1
		else:
			if computer:
				print(f"Generating ship positions for {self.name}...\n")
			for shipType in ShipTypes:
				shipLength = ShipTypes[shipType]
				valid = False
				while not valid:
					self.shipCoords[shipType] = set()
					startCoord = random.choice(tuple(allComplexes - self.allShipCoords())) if computer else self.coordInput(f"your {shipType}", pos="starting", disallowed=self.allShipCoords())
					sleep(0.3)
					try:
						endCoord = (startCoord + (random.choice(tuple(filter(lambda c: not ((d := startCoord + c).real > 9 or d.real < 0 or d.imag > 9 or d.imag < 0) or False, identityComplexes)))) * (shipLength - 1)) if computer else self.coordInput(f"your {shipType}", pos="ending", disallowed=self.allShipCoords())
					except Exception:
						continue
					
					sleep(0.3)
					
					gradient = (startCoord - endCoord) / (shipLength - 1)
					#print(gradient)
					
					# the following shoukd theoretically never be true but edge cases might exist
					if gradient.real % 1 != 0 and gradient.imag % 1 != 0 and not computer:
						print(f"Invalid ship length. This type of ship needs to be exactly {shipLength} squares long.\n")
						continue
					elif gradient not in identityComplexes and not computer:
						print("Ships can only be horizontal or vertical, not diagonal.\n")
						continue
					
					invalid = 0
					for i in range(0, ShipTypes[shipType]):
						coordTuple = startCoord - (gradient * i)
						if coordTuple in self.allShipCoords() and i not in (0, shipLength):
							invalid += 1
						self.shipCoords[shipType].add(coordTuple)
					if invalid == 0:
						valid = True
					elif not computer:
						print("Your ship cannot pass through another ship.\n")
			#print(self.shipCoords)
			#print(self.allShipCoords())
		
	def firedCoords(self):
		return self.missedCoords | self.hitCoords
		
	def allShipCoords(self):
		allShipCoords = set()
		for shipType in ShipTypes:
			allShipCoords |= self.shipCoords[shipType]
		return allShipCoords
		
	def coordInput(self, coordType, **kwargs):
		if not self.computer:
			while True:
				coord = input(f"{self.name}: please enter a {kwargs['pos'] + ' ' if 'pos' in kwargs else ''}coordinate for {coordType}. Coordinates go from A to J and 0 to 9. ").lower().strip()
				if coord == "help":
					print(helpMsg)
					continue
				elif len(coord) == 2 and coord[0] in letters and coord[1] in numbers:
					crd = complex(float(letters.index(coord[0])), float(coord[1]))
					if 'disallowed' in kwargs and crd in kwargs['disallowed']:
						print("You've already used that coordinate.\n")
					elif 'allowed' in kwargs and crd not in kwargs['allowed']:
						print("That isn't a valid coordinate.\n")
					else:
						print("\n")
						return crd
				else:
					print("That isn't a valid coordinate.\n")
		else:
			coord =  random.choice(tuple(allComplexes - self.firedCoords()))
			print(f"{self.name}: please enter a {kwargs['pos'] + ' ' if 'pos' in kwargs else ''}coordinate for {coordType}. Coordinates go from A to J and 0 to 9. {letters[int(coord.real)]}{int(coord.imag)}")
			return coord
			
				
	def printFired(self):
		board = "\n".join([" ".join(["   " + str(y)] + ["×" if complex(x, y) in self.hitCoords else ("•" if complex(x, y) in self.missedCoords else "-") for x in range (0, 10)]) for y in range(0, 10)])
		print(f"{self.name}'s fired coordinates:\n   ~ {' '.join(letters)}\n{board}\n")
		
	def printShips(self):
		board = "\n".join([" ".join(["   " + str(y)] + ["X" if complex(x, y) in self.allShipCoords() else "-" for x in range(0, 10)]) for y in range(0, 10)])
		print(f"{self.name}'s ship coordinates:\n   ~ {' '.join(letters)}\n{board}\n")
	
	def turn(self):#, coord0):
		if not isinstance(self.opponent, type(self)):
			raise TypeError
		else:
			if self.computer:
				sleep(1)
			coord = self.coordInput("firing", disallowed=self.firedCoords())
			if coord not in self.opponent.allShipCoords():
				print("You missed.\n")
				self.missedCoords.add(coord)
			else:
				hitShip = ""
				for shipType in ShipTypes:
					if coord in self.opponent.shipCoords[shipType]:
						hitShip = shipType
						break
				self.hitCoords.add(coord)
				self.opponent.sunkCoords.add(coord)
				print(f"You hit your opponent's {hitShip}!", f"You have {sum([ShipTypes[st] for st in ShipTypes]) - len(self.opponent.sunkCoords)} coordinates left to hit until you've won!\n" if not self.opponent.sunk() else "You've won!\n\n")

	def sunk (self):
		return len(self.sunkCoords) == sum([ShipTypes[st] for st in ShipTypes])

players = None
while (players := input("Enter the player settings: 1 for two human players, 2 for human vs computer, 3 for computers vs computer: ")) not in "123":
	print("That's not a valid answer.")

player1, player2 = BattleShipsPlayer("PLAYER 1", computer=(players == "3")), BattleShipsPlayer("PLAYER 2", computer=(players in "23"))

player1.opponent, player2.opponent = player2, player1

#player1.printShips()
#player2.printShips()

while True:
	try:
		player1.turn()
		if player2.sunk():
			print("Congratulations PLAYER 1; you won!")
			break
		player1.printFired()
		sleep(0.06)
		player2.turn()
		if player1.sunk():
			print("Congratulations PLAYER 2; you won!")
			break
		player2.printFired()
		sleep(0.06)
	except IndexError:
		print("error error eRrOr ErRoR ERROR ERROR")
		break
print("Here are both players' ship coordinates:")
player1.printShips()
player2.printShips()