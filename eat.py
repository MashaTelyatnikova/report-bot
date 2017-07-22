from telepot.loop import OrderedWebhook
import telepot
from time import sleep
import json

from datetime import datetime
from enum import Enum
from sys import stdin 

class Rule:
	def matches(self, text):
		pass
		
class IsCommandRule(Rule):
	cmd = "/"
	def __init__(self, cmd):
		self.cmd += cmd
		
	def matches(self, text):
		return self.cmd == text
	
class IsIntegerRule(Rule):
	def matches(self, text):
		try:
			number = int(text)
			return True
		except ValueError:
			return False

class IsPositiveIntegerRule(Rule):
	def matches(self, text):
		try:
			number = int(text)
			return number > 0
		except ValueError:
			return False
			
class IsFloatRule(Rule):
	def matches(self, text):
		try:
			number = float(text)
			return True
		except ValueError:
			return False	

class IsAlwaysTrueRule(Rule):
	def matches(self, text):
		return True
			
class State(Enum):
	INIT = 0
	START = 1
	EAT = 2
	DRINK = 3
	HEALTH = 4
	HABITS = 5

class FoodItem():
	time = datetime.now()
	info = ""
		
def do_nothing():
		pass
		
class CommandInfo:
	next_state = State.INIT
	
	def __init__(self, next_state, command = lambda text, report, chat_id: do_nothing()):
		self.next_state = next_state
		self.command = command
	
class report:
	start: None
	end: None
	food = []
	water = 0.0
	habits = 0
	health = 0
	exercise = False
	
	def clear(self):
		self.start: None
		self.end: None
		self.food = []
		self.water = 0.0
		self.habits = 0
		self.health = 0
		self.exercise = False
		
	def to_string(self):
		if (self.start is None or self.end is None):
			return ""
			
		result = ""
		
		#food
		result += "1. \n"
		for item in self.food:
			result += item.time.isoformat(timespec='minutes') + " : " + item.info + "\n"

		result += "\n"
			
		#water
		result += "2. " + str(self.water) + " л\n"
		
		#exercise
		result += "3. " + ("+" if self.exercise else "-") + "\n"
		
		#time
		result += "4. " + self.start.isoformat(timespec='minutes') + " - " + self.end.isoformat(timespec='minutes') + "\n"
		
		#health
		result += "5. " + str(self.health) + "/10\n"
		
		#good_habits
		result += "6. " + str(self.habits) + "/5\n"
		
		return result
	
class Application:
	state = State.INIT
	
def handle_start(text, report, chat_id):
	report.start = datetime.now()
	#todo help

def handle_eat(text, report, chat_id):
	report.food.append(FoodItem())
	TelegramBot.sendMessage(chat_id = chat_id, text = "Введите описание того, что быо съедено")

def handle_food_item(text, report, chat_id):
	report.food[-1].info = text
	
def handle_stop(text, report, chat_id):
	report.end = datetime.now()
	TelegramBot.sendMessage(chat_id=chat_id, text=report.to_string())
	report.clear()
	
def handle_drink(text, report, chat_id):
	report.water += float(text)
	
def handle_exercise(text, report, chat_id):
	report.exercise = True
	
def handle_notexercise(text, report, chat_id):
	report.exercise = False
	
def handle_health(text, report, chat_id):
	report.health = int(text)
	
def handle_habits(text, report, chat_id):
	report.habits += int(text)

current_report = report()
transitions = {}

transitions[State.INIT] = [
	(IsCommandRule("start"), CommandInfo(State.START, lambda text, report, chat_id: handle_start(text, report, chat_id))),
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))), 
	(IsAlwaysTrueRule(), CommandInfo(State.INIT))
]

transitions[State.START] = [
	(IsCommandRule("eat"), CommandInfo(State.EAT, lambda text, report, chat_id: handle_eat(text, report, chat_id))),
	(IsCommandRule("drink"), CommandInfo(State.DRINK, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Введите количество выпитой воды в литрах"))),
	(IsCommandRule("health"), CommandInfo(State.HEALTH, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Введите своё самочувствие от 1 до 10"))),
	(IsCommandRule("hab"), CommandInfo(State.HABITS, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Введите выполненные привычки"))),
	(IsCommandRule("ex"), CommandInfo(State.START, lambda text, report, chat_id: handle_exercise(text, report, chat_id))),
	(IsCommandRule("notex"), CommandInfo(State.START, lambda text, report, chat_id: handle_notexercise(text, report, chat_id))),
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))), 
	(IsAlwaysTrueRule(), CommandInfo(State.START, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Неверная команда")))
]

transitions[State.EAT] = [
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))),
	(IsAlwaysTrueRule(), CommandInfo(State.START, lambda text, report, chat_id: handle_food_item(text, report, chat_id)))
]

transitions[State.DRINK] = [
	(IsFloatRule(), CommandInfo(State.START, lambda text, report, chat_id: handle_drink(text, report, chat_id))),
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))),
	(IsAlwaysTrueRule(), CommandInfo(State.DRINK, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Неверная команда")))
]

transitions[State.HEALTH] = [
	(IsPositiveIntegerRule(), CommandInfo(State.START, lambda text, report, chat_id: handle_health(text, report, chat_id))),
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))),
	(IsAlwaysTrueRule(), CommandInfo(State.HEALTH, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Неверная команда")))
]

transitions[State.HABITS] = [
	(IsIntegerRule(), CommandInfo(State.START, lambda text, report, chat_id: handle_habits(text, report, chat_id))),
	(IsCommandRule("stop"), CommandInfo(State.INIT, lambda text, report, chat_id: handle_stop(text, report, chat_id))),
	(IsAlwaysTrueRule(), CommandInfo(State.HABITS, lambda text, report, chat_id: TelegramBot.sendMessage(chat_id = chat_id, text = "Неверная команда")))
]


token = '394798553:AAG1Fv7iFuyOx3pQQP1AR3F-dQZ8XONbmto'

TelegramBot = telepot.Bot(token)
last_id = None

__CURRENT_STATE__ = State.INIT

def handle(msg):
	global __CURRENT_STATE__
	if __CURRENT_STATE__ is None:
		__CURRENT_STATE__ = State.INIT
		
	chat_id = msg['chat']['id']
	if ("text" in msg):
		data = msg["text"]
		for rule in transitions[__CURRENT_STATE__]:
			if (rule[0].matches(data)):
				__CURRENT_STATE__ = rule[1].next_state
				rule[1].command(data, current_report, chat_id)
				break
	
TelegramBot.message_loop(handle)

while True:
	sleep (1)