from time import sleep
from random import choice, randint
import re, sqlite3 as sqlite, json, hashlib, secrets

# a fairly insecure password hashing function
def hashPwd(pwd, salt=None):
    if not salt:
        salt = secrets.token_hex(12)
    return { "hash": hashlib.sha256((pwd + salt).encode("utf-8")).hexdigest(), "salt": salt }

conn = sqlite.connect("fightergame.db")

db = conn.cursor()
db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if not db.fetchone():
    db.execute("CREATE TABLE users (name TEXT PRIMARY KEY, weapons TEXT NOT NULL, powerups TEXT NOT NULL, foughtBefore TEXT NOT NULL, enemyIndex INTEGER NOT NULL, health INTEGER NOT NULL, enemyHealth INTEGER NOT NULL, money INTEGER NOT NULL, turn INTEGER NOT NULL, password TEXT NOT NULL, salt TEXT NOT NULL)")
#db.execute("DROP TABLE users")
conn.commit()

updateQuery = ""

shopCommandRe = r"^buy\s+(weapon|powerup)\s*(\s+[a-z ]+)?$"

weapons = { \
            "shoe": { "cost": 12, "description": "Throws a shoe at your opponent.", "type": "single", "minDamage": 10, "maxDamage": 20, "failRate": 15, "article": "a" },\
            "bagpipes": { "cost": 400, "description": "Useful for bursting people's eardrums - can also be utilised as a club.", "type": "single", "minDamage": 20, "maxDamage": 40, "failRate": 10, "article": "some" },\
            "truncheon": { "cost": 20, "description": "whack", "type": "single", "minDamage": 20, "maxDamage": 45, "failRate": 12, "article": "a" },\
            "splinter": { "cost": 0.99, "description": "ow! ouch ouch oo ow", "type": "single", "minDamage": 5, "maxDamage": 30, "failRate": 1, "article": "a" },\
            "stick": { "cost": 8, "description": "ug ug big stick", "type": "single", "minDamage": 15, "maxDamage": 42, "failRate": 15, "article": "a" },\
            "doorknob": { "cost": 4.50, "description": "can be slightly uncomfortable when prodded in one's stomach", "type": "single", "minDamage": 10, "maxDamage": 35, "failRate": 5, "article": "a" },\
            "virus": { "cost": 65, "description": "may thou hath the plague", "type": "multiple", "length": 5, "minDamage": 20, "maxDamage": 35, "failRate": 15, "article": "a" },\
            "butter knife": { "cost": 4.20, "description": "stabby stabby", "type": "single", "minDamage": 10, "maxDamage": 25, "failRate": 10, "article": "a" },\
            "rabid sheep": { "cost": 108, "description": "whilst rabies has been eradicated in the UK, some sheep can be very dangerous.", "type": "multiple", "length": 6, "minDamage": 20, "maxDamage": 50, "failRate": 5, "article": "a" },\
            "whistle": { "cost": 1.20, "description": "eeeeeeeeeeeee", "type": "single", "minDamage": 5, "maxDamage": 10, "failRate": 0, "article": "a" },\
            "gaggle of geese": { "cost": 100, "description": "HONK! Bite poeople's angkles with giant ducks. HONK!", "type": "single", "minDamage": 45, "maxDamage": 80, "failRate": 20, "article": "a" },\
            "combat briefcase": { "cost": 50, "description": "Perfect for giving people concussion (and protecting sensitive documents)", "type": "single", "minDamage": 35, "maxDamage": 90, "failRate": 12, "article": "a" },\
            "attack handbag": { "cost": 50, "description": "WHACK!!", "type": "single", "minDamage": 40, "maxDamage": 90, "failRate": 14, "article": "an" },\
            "brexit": { "cost": 100, "description": "BREXIT. MEANS. BREXIT!", "type": "single", "minDamage": 60, "maxDamage": 120, "failRate": 20, "article": "some" },\
          }

powerups = { \
            "zorb": { "description": "protects your little body from some attacks until it bursts", "cost": 99, "length": 6, "value": 0.55 },\
            "calpol": { "description": "drugs can be good for you - this increases your health by 35% as soon as you buy it", "cost": 4.99, "value": 1.35 },\
            "lucozade": { "description": "increases your attack power by 50% for 4 turns!!!!!!!!11!11111111!11!!! xD :D:D:D:D:D:D:D", "cost": 1.99, "value": 1.5, "length": 4 },\
           }

# some enemies, such as sajid javid, have weapons repeated - this is so that some weapons ahve a lower chance of being used
enemies = [{ "name": "A RANDOM POLICEMAN", "health": 100, "weapons": ["truncheon", "whistle"], "refightCost": 4.99, "collect": { "weapons": ["truncheon", "butter knife"], "money": lambda: randint(1000, 1500)/100 }},\
           { "name": "THE DOOR", "health": 150, "weapons": ["splinter", "doorknob"], "refightCost": 7.50, "collect": { "weapons": ["stick"], "money": lambda: randint(1500, 1750)/100 }},\
           { "name": "SAJID JAVID", "health": 250, "weapons": ["virus", "shoe", "butter knife", "shoe", "butter knife"], "refightCost": 10.20, "collect": { "weapons": ["virus", "rabid sheep"], "money": lambda: randint(2000, 2800)/100 }},\
           { "name": "MATT HANCOCK", "health": 400, "weapons": ["rabid sheep", "virus", "butter knife", "shoe", "butter knife"], "refightCost": 10.20, "collect": { "weapons": ["rabid sheep", "gaggle of geese"], "money": lambda: randint(2500, 3200)/100 }},\
           { "name": "GAVIN WILLIAMSON", "health": 600, "weapons": ["gaggle of geese", "truncheon", "butter knife", "combat briefcase"], "refightCost": 15, "collect": { "weapons": ["combat briefcase", "gaggle of geese"], "money": lambda: randint(3000, 4000)/100 }},\
           { "name": "THERESA MAY", "health": 1000, "weapons": ["attack handbag", "truncheon", "butter knife", "brexit"], "refightCost": 23, "collect": { "weapons": ["brexit", "attack handbag"], "money": lambda: randint(5000, 10000)/100 }},\
           { "name": "BORIS JOHNSON", "health": 2000, "weapons": [weapon for weapon in weapons], "refightCost": 1000, "collect": { "weapons": [weapon for weapon in weapons], "money": lambda: 250 }},\
          ]

playerFailMessages = ["Your {0} missed your target! Better luck next time.", "Your {0} failed! Unlucky.", "{1} dodged out of the way of your {0}! Maybe next time..."]
enemyFailMessages = ["{1} {0} missed you! You were lucky this time...", "{1} {0} failed! Lucky you!", "You dodged out of the way of {1} {0} - you're alive! (for now)"]
meetMessages = ["You see {} running towards you... get ready to fight!", "{} has seen you coming - can you beat them?", "You bump into {} - maybe they'll be feeling merciful..."]
meetAgainMessages = ["You stumble across {} again! Who will win this time?", "{} wants to fight you again... may the best warrior win!"]
attackTypes = { "single": "deals damage on a single turn", "multiple": "deals damage on multiple turns" }

article = lambda noun: "an" if noun[0] in "aeiou" else "a"
possesive = lambda noun: "your" if noun == "you" else (noun + "'" + "s" if noun[-1] != "s" else "")

# the player class can be initialised with a settings dictionary; this is intended for saving the game.
class Player:
   
    def __init__(self, settings={}):
        self.weapons = ["shoe", "bagpipes"] if "weapons" not in settings else settings["weapons"]
        self.powerups = {} if "powerups" not in settings else settings["powerups"]
        self.money = 20 if "money" not in settings else settings["money"]
        self.commands = { "money": self.printMoney, "weapons": self.printweapons, "help": self.help, "shop": self.shop, "password": self.setPwd }
        self.name = input("Please enter your name: ") if "name" not in settings else settings["name"]
        self.health = -1 if "health" not in settings else settings["health"]
        self.enemyHealth = -1 if "enemyHealth" not in settings else settings["enemyHealth"]
        self.enemyIndex = 0 if "enemyIndex" not in settings else settings["enemyIndex"]
        self.foughtBefore = set() if "foughtBefore" not in settings else settings["foughtBefore"]
        self.turn = 0 if "turn" not in settings else settings["turn"]
        #print(self.enemyIndex)
        #print(settings)
        newPlayer = settings["new"]
       
        self.finished = False
        self.restart = False
       
        if newPlayer:
            self.help()
            sleep(0.5)
            input("Press enter to continue.\n")
        sleep(0.4)
        firstFight = True
        while True:
            while self.enemyIndex < len(enemies) - 1:
                self.enemy = enemies[self.enemyIndex]
                self.health = self.health if (firstFight and not newPlayer) else (self.enemy["health"] if self.enemy["name"] != "A RANDOM POLICEMAN" else 115)
                self.enemyHealth = self.enemyHealth if (firstFight and not newPlayer) else self.enemy["health"]
                if newPlayer and firstFight:
                    db.execute("INSERT INTO users VALUES (:name, :weapons, :powerups, :foughtBefore, :enemyIndex, :health, :enemyHealth, :money, :turn, '', '')", {"name": self.name, "weapons": json.dumps(list(self.weapons)), "powerups": json.dumps({}), "foughtBefore": json.dumps([]), "enemyIndex": 0, "health": self.health, "enemyHealth": self.enemyHealth, "money": self.money, "turn": self.turn })
                    conn.commit()
                firstFight = False
                print(choice(meetAgainMessages if self.enemyIndex in self.foughtBefore else meetMessages).format(self.enemy["name"]),"\n")
                sleep(0.2)
                self.foughtBefore.add(self.enemyIndex)
                self.save()
                won = self.fight()
                if won == "switch":
                    self.finished = False
                    print("Exiting...\n")
                    sleep(0.8)
                    return
                if won == "restart":
                    self.restart = True
                    print("Restarting...\n")
                    sleep(0.8)
                    return
                if won:
                    self.enemyIndex += 1
                    if "weapons" in self.enemy["collect"]:
                        collectWeapon = choice(self.enemy["collect"]["weapons"])
                        if collectWeapon not in self.weapons:
                            self.weapons.append(collectWeapon)
                            print(f"You collected {weapons[collectWeapon]['article']} {collectWeapon}!")
                    if "money" in self.enemy["collect"]:
                        collectMoney = self.enemy["collect"]["money"]()
                        self.money += collectMoney
                        self.money = round(self.money * 100) / 100
                        print(f"You collected £{collectMoney}! You now have £{self.money}.")
                else:
                    if self.money < self.enemy["refightCost"]:
                        print(f"You don't have enough money to fight {self.enemy['name']} again. Get some rest, then you'll have to fight your last 3 opponents again.\n")
                    else:
                        pay = self.yesNoInput(f"Would you like to pay £{self.enemy['refightCost']} to fight {self.enemy['name']} again?\nyes/no\n")
                    if not pay:
                        print(f"You chose not to refight {self.enemy['name']} again. Get some rest, then you'll have to fight your last 3 opponents again.\n")
                        self.enemyIndex = max(0, self.enemyIndex - 3)
                    else:
                        self.money -= self.enemy['refightCost']
                        self.money = round(self.money * 100) / 100
                        print(f"You now have £{self.money}. Get ready to fight again!\n")
                self.save()
                sleep(0.5)
            print(f"""Ok, {self.name}, now it's time for THE FINAL BOSS!
    That's right, it's the moment you've been waiting for - the moment where you get to assassinate Boris Johnson.
    Before fighting him, I'd recommend going into the shop to stock up on supplies.
    Ready, steady, FIGHT!""")
            self.enemyIndex = -1
            self.enemy = enemies[-1]
            self.health = 2000
            won = self.fight()
            if won:
               print("You won! Yay!")
               self.finished = True
               return
            else:
                print("""YOU LOST TO BORIS JOHNSON :C
You got thrown out of 10 Downing Street and left to die in a pothole somewhere - but now you're ready for revenge; luckily, your belongings weren't confiscated...
Back to the beginning you go!""")
    def save(self):
        db.execute("UPDATE users SET weapons = :weapons, powerups = :powerups, foughtBefore = :foughtBefore, enemyIndex = :enemyIndex, health = :health, enemyHealth = :enemyHealth, money = :money, turn = :turn WHERE name = :name", {"name": self.name, "weapons": json.dumps(list(self.weapons)), "powerups": json.dumps(self.powerups), "foughtBefore": json.dumps(list(self.foughtBefore)), "enemyIndex": self.enemyIndex, "health": self.health, "enemyHealth": self.enemyHealth, "money": self.money, "turn": self.turn })
        conn.commit()
        #print("saved", self.enemyIndex)
    def setPwd(self):
        pwd = None
        while not pwd:
            password = input("Enter a password: ")
            password2 = input("Confirm your password: ")
            if password == password2:
                pwd = password
            else:
                print("Passwords do not match.")
        db.execute("UPDATE users SET password = :hash, salt = :salt WHERE name = :name", { "name": self.name, **hashPwd(pwd) })
        conn.commit()
        print("Password saved!\n")
    def help(self):
        print(f"""
Welcome to Super Ultra Street Fighter 3: Scottish Supremacy, {self.name}!
The aim of the game is to get into 10 Downing Street to assassinate the prime minister Boris Johnson to get Nicola Sturgeon in power.
But first you need to get through the people protecting Boris - you will fight them one by one. But beware, if you are defeated, you will go back 3 fights (but you'll keep any weapons and money you gained) - unless you can pay to fight again.
You start of with two weapons - shoe and bagpipes - and gain more powerful ones along the way. To see all your weapons and their info, type 'weapons' at any point.
You start with £20, which you can use to refight enemies and buy new weapons and powerups in the shop - use the 'shop' command. You can earn money by defeating opponents.
Your game is automatically saved, so you can come back to the game and continue where you left off on the same computer. You can secure your account with a password using the 'password' command if you like.
Available commands are: {", ".join([k for k in self.commands])}
Good luck, {self.name}.
To display this message again, type 'help' at any point.
""")
    def shop(self):
        print(f"""Welcome to the shop, {self.name}!
View available weapons and their prices using 'buy weapon', and powerups with 'buy powerup'.
To buy a weapon or powerup, use 'buy weapon|powerup {{weapon or powerup}}'.
To exit the shop, type 'exit'.""")
        while True:
            cmd = self.shopInput()
            self.save()
            if cmd == "exit":
                print("Exiting shop...")
                sleep(0.2)
                break
            if cmd == "switch":
                return "switch"
            if cmd == "restart":
                return "restart"
    def shopInput(self):
        # there isn't much reason to be using regexes here but it looks cool (and I was going to do more with them... but I had better things to do)'
        while response := input("\n").lower() or True:
            if response == "switch":
                sure = self.yesNoInput("Are you sure you want to switch accounts?\nyes/no ")
                if sure:
                    return "switch"
            if response == "restart":
                sure = self.yesNoInput("Are you sure you want to restart the game? This action is irreversible.\nyes/no ")
                if sure:
                    return "restart"
            if response in self.commands:
                self.commands[response]()
                continue
            if response == "exit":
                 return "exit"
            availableWeapons = list(filter(lambda w: w not in self.weapons and "cost" in weapons[w] and weapons[w]["cost"] <= self.money, [w for w in weapons]))
            availablePowerups = list(filter(lambda p: p not in self.powerups and powerups[p]["cost"] <= self.money, [p for p in powerups]))
            if re.match("^sql ", response):
                try:
                    db.execute(response[3:])
                except Exception as e:
                    print(e)
                finally:
                    conn.commit()
            elif re.match(shopCommandRe, response, flags=re.I):
                if re.match(r"^buy weapon$", response, flags=re.I):
                    if not len(availableWeapons):
                        print("There aren't any weapons for sale that you can afford or that you don't already own.")
                    else:
                        tooExpensive = len(weapons) - (len(self.weapons) + len(availableWeapons))
                        print("  - " + "\n  - ".join([f"{w} - {weapons[w]['description']} - {attackTypes[weapons[w]['type']]}; deals between {weapons[w]['minDamage']} and {weapons[w]['maxDamage']} damage, {weapons[w]['failRate']}% chance of failure - £{'{:.2f}'.format(weapons[w]['cost'])}" for w in availableWeapons]) + (f"\n\nThere {'are' if tooExpensive > 1 else 'is'} {tooExpensive} other weapon{'s' if tooExpensive > 1 else ''} that you can't currently afford to buy.\n" if tooExpensive > 0 else '\n'))
                elif re.match(r"^buy powerup$", response, flags=re.I):
                    if not len(availablePowerups):
                        print("There aren't any powerups for sale that you can afford or that aren't' already in use.")
                    else:
                        tooExpensive = len(powerups) - (len(self.powerups) + len(availablePowerups))
                        print("  - " + "\n  - ".join([f"{p} - {powerups[p]['description']} - £{'{:.2f}'.format(powerups[p]['cost'])}" for p in availablePowerups]) + (f"\n\nThere {'are' if tooExpensive > 1 else 'is'} {tooExpensive} other powerup{'s' if tooExpensive > 1 else ''} that you can't currently afford to buy.\n" if tooExpensive > 0 else '\n'))
                elif re.match(r"^buy weapon [a-z\s]+$", response, flags=re.I):
                    weapon = response[11:]
                    if weapon in availableWeapons:
                        self.weapons.append(weapon)
                        self.money -= weapons[weapon]["cost"]
                        self.money = round(self.money * 100) / 100
                        self.printMoney()
                    elif weapon in self.weapons:
                        print("You already own that weapon.\n")
                    elif weapon in weapons:
                        print("You can't afford that weapon.\n")
                    else:
                        print("That weapon doesn't exist.\n")
                elif re.match(r"^buy powerup [a-z\s]+$", response, flags=re.I):
                    powerup = response[12:]
                    if powerup in availablePowerups:
                        self.money -= powerups[powerup]["cost"]
                        self.money = round(self.money * 100) / 100
                        print(f"You now have £{self.money}.")
                        if powerup == "calpol":
                            self.health *= powerups[powerup]["value"]
                            self.health = round(self.health)
                            print(f"You're now on {self.health} health.\n")
                        else:
                            self.powerups[powerup] = powerups[powerup]["length"]
                    elif powerup in self.powerups:
                        print("That powerup is already in use.")
                    elif powerup in powerups:
                        print("You can't afford that powerup.\n")
                    else:
                        print("That powerup doesn't exist.\n")
            else:
                print("That's not a valid command.")
            self.save()
    def printMoney(self):
        print(f"You have £{self.money}")
    def printweapons(self):
        print("Your weapons:\n  -", "\n  - ".join([f"{weapon}: {weapons[weapon]['description']} - {attackTypes[weapons[weapon]['type']]}; deals between {weapons[weapon]['minDamage']} and {weapons[weapon]['maxDamage']} damage, {weapons[weapon]['failRate']}% chance of failure" for weapon in self.weapons]), "\n")
    def fight(self):
        myRepeatedAttacks = {}
        eRepeatedAttacks = {}
        while True:
            if self.turn == 0:
                weapon = self.weaponInput(f"Enter a weapon to use on {self.enemy['name']}:\n")
                if weapon == "switch":
                    return "switch"
                if weapon == "restart":
                    return "restart"
                attackIncrease = 1
                if "lucozade" in self.powerups:
                    if self.powerups["lucozade"] <= 0:
                        del self.powerups["lucozade"]
                    else:
                        attackIncrease = powerups["lucozade"]["value"]
                        self.powerups["lucozade"] -= 1
                weaponInfo = weapons[weapon]
                failed = randint(0, 100) <= weaponInfo["failRate"]
                for w in eRepeatedAttacks:
                    print(f"You dealt {eRepeatedAttacks[w][0] * attackIncrease} damage to {self.enemy['name']} with {weapons[w]['article']} {w}!")
                    self.enemyHealth -= round(eRepeatedAttacks[w][0] * attackIncrease)
                    eRepeatedAttacks[w][1] -= 1
                if failed:
                    print(choice(playerFailMessages).format(weapon, self.enemy["name"]), "\n")
                else:
                    damage = randint(weaponInfo["minDamage"], weaponInfo["maxDamage"])
                    self.enemyHealth -= round(damage * attackIncrease)
                    if self.enemyHealth <= 0:
                        print(f"You defeated {self.enemy['name']} with {weaponInfo['article']} {weapon}!\n")
                        return True
                    else:
                        print(f"You dealt {damage} damage to {self.enemy['name']} with {weaponInfo['article']} {weapon}! They are now on {self.enemyHealth} health.\n")
                        if weaponInfo["type"] == "multiple":
                            eRepeatedAttacks[weapon] = [damage, weaponInfo["length"]]
            elif self.turn == 1:
                attackDecrease = 1
                if "zorb" in self.powerups:
                    if self.powerups["zorb"] <= 0:
                        del self.powerups["zorb"]
                    else:
                        attackDecrease = powerups["zorb"]["value"]
                        self.powerups["zorb"] -= 1
                weapon = choice(self.enemy["weapons"])
                weaponInfo = weapons[weapon]
                failed = randint(0, 100) <= weaponInfo["failRate"]
                for w in myRepeatedAttacks:
                    print(f"{self.enemy['name']} dealt {myRepeatedAttacks[w][0] * attackDecrease} damage to you with {weapons[w]['article']} {w}!")
                    myRepeatedAttacks[w][1] -= 1
                self.health -= sum([round(myRepeatedAttacks[a][0] * attackDecrease) for a in myRepeatedAttacks])

                if failed:
                    print(choice(enemyFailMessages).format(weapon, possesive(self.enemy["name"])), "\n")
                else:
                    damage = round(randint(weaponInfo["minDamage"], weaponInfo["maxDamage"]) * attackDecrease)
                    self.health -= damage
                    if self.health <= 0:
                        print(f"You were defeated by {self.enemy['name']} with {weaponInfo['article']} {weapon}.")
                        return False
                    else:
                        print(f"{self.enemy['name']} dealt {damage} damage to you with {weaponInfo['article']} {weapon}! You are now on {self.health} health.\n")
                        if weaponInfo["type"] == "multiple":
                            myRepeatedAttacks[weapon] = [damage, weaponInfo["length"]]
            self.turn = (self.turn + 1) % 2
            self.save()
            sleep(0.5)
   
    def weaponInput(self, prompt):
        response = None
        while response := input(prompt).lower().strip() or True:
            if re.match("^sql ", response):
                try:
                    db.execute(response[3:])
                except Exception as e:
                    print(e)
                finally:
                    conn.commit()
            if response == "switch":
                sure = self.yesNoInput("Are you sure you want to switch accounts?\nyes/no ")
                if sure:
                    return "switch"
            if response == "restart":
                sure = self.yesNoInput("Are you sure you want to restart the game? This action is irreversible.\nyes/no ")
                if sure:
                    return "restart"
            if response in self.commands:
                cmdOutput = self.commands[response]()
                if cmdOutput == "switch":
                    return "switch"
                if cmdOutput == "restart":
                    return "restart"
                continue
            if response in self.weapons:
                break
            elif response in weapons:
                print("You don't own that weapon.\n")
            else:
                print("That weapon doesn't exist.")
        return response
    def yesNoInput(self, prompt):
        response = None
        while (response := input(prompt).lower()) not in ("yes", "y", "no", "n"):
            print("That's not a valid option.")
        return response in "yes"
       
print("Welcome to Super Ultra Street Fighter 3: Scottish Supremacy! Let's get started.")

savedName = None

while True:
    name = name if savedName else input("Please enter your name: ")
    savedName = None
    db.execute("SELECT * FROM users WHERE name = :name", { 'name': name })
    usr = db.fetchone()
    conn.commit()
    player = None
    if usr:
        if usr[9]:
            while True:
                pwd = input("Enter your password (press enter to use a different account): ")
                if not pwd:
                    continue
                if hashPwd(pwd, salt=usr[10])["hash"] != usr[9]:
                    print("Incorrect password.")
                else:
                    break
        print(f"Welcome back, {name}! You'll continue where you left off. If you've never played before, then someone else has already used your name - please use the 'switch' command to switch accounts.")
        player = Player(settings={"new": False, "name": usr[0], "weapons": json.loads(usr[1]), "powerups": json.loads(usr[2]), "foughtBefore": set(json.loads(usr[3])), "enemyIndex": usr[4], "health": usr[5], "enemyHealth": usr[6], "money": usr[7], "turn": usr[8] })
    else:
        player = Player(settings={"name":name, "new": True})
    if player.restart:
        savedName = name
        db.execute("DELETE FROM users WHERE name = :name", { "name": name })
        conn.commit()
        continue
    if player.finished:
        break