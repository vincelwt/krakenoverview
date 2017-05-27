import krakenex, json, os, time
from termcolor import cprint, colored
from tabulate import tabulate

k = krakenex.API()
k.load_key('krakenvince.key')

liveValues = []
compound = []

# Updates liveValues array with current prices of all currencies
def updateLivevalues():
	global liveValues

	assets = k.query_public('Ticker', {'pair': 'ETHEUR,XBTEUR,LTCEUR,XMREUR,XRPEUR,DASHEUR,ETCEUR,ZECEUR,GNOEUR,REPEUR'})['result']

	liveValues = []

	for attr, value in assets.iteritems():
		liveValues.append([attr.replace('ZEUR', '').replace('EUR', ''), float(value['a'][0]) ])


# Returns an array with the currency price a week ago & a day ago
def getOldvalues(pair):
	pair = pair.replace('XBT', 'BTC').replace('ASH', 'DASH')

	timeAgo = int(time.time()-3600*24*7)

	spread = k.query_public('OHLC', {'pair': pair, 'interval': '1440', 'since': str(timeAgo)})

	for attr, value in spread['result'].iteritems():
		if not 'EUR' in attr: continue

		weekAgo = value[0]
		weekAgoAverage = ( float(weekAgo[1]) + float(weekAgo[2]) + float(weekAgo[3]) + float(weekAgo[4]) ) / 4

		dayAgo = value[5]
		dayAgoAverage = ( float(dayAgo[1]) + float(dayAgo[2]) + float(dayAgo[3]) + float(dayAgo[4]) ) / 4

	return [weekAgoAverage, dayAgoAverage]

	

# Update total outcome of all made trades
def printTrades(): 

	global compound

	recentTrades = k.query_private('ClosedOrders', {})

	compound = []

	for attr, value in recentTrades['result']['closed'].iteritems():

		type = value['descr']['type']

		asset = value['descr']['pair'][:3]
		source = value['descr']['pair'][-3:]


		price = float( value['price'] )
		vol = float( value['vol_exec'] )
		cost = float( value['cost'] )

		#print source, price

		if type == 'sell':
			vol = -vol
			cost = -cost

		touched = False
		touched2 = False

		for e in compound:
			if e[0] == asset:
				e[1] += vol
				e[2] += cost

				touched = True

		if not touched:
			compound.append([asset, vol, cost])
		
		#print '%15s  %13s  %12s' % (colored(type+asset, 'grey', 'on_yellow'), str(vol), colored(cost, 'white', 'on_magenta'))
		#print value

	#print '--------Total ---------'

	#for e in compound:
	#	print '%6s  %13s  %12s' % (colored(e[0], 'grey', 'on_yellow'), str(e[1]), colored(e[2], 'white', 'on_magenta'))



def printBalance():

	print colored('Updating data...', 'green')

	table = [['Balance', 'Quantity', 'Euro amount', 'Net results', 'Last 24h', 'Last week']]

	currencies = k.query_private('Balance')['result']

	balance = k.query_private('TradeBalance', {'asset': 'ZEUR'})['result']
	
	totalChange = 0
	totalWeekChange = 0
	totalDayChange = 0

	# For each currency in Kraken "wallet"
	for attr, pair in currencies.iteritems():

		value = 0
		change = 0
		weekChange = 0
		dayChange = 0

		pair = float(pair)

		valueStr = ''
		for values in liveValues:
			if values[0] == attr:
				value = pair*values[1]
				valueStr = str( int(value) )+' EUR'	


		if (attr != 'ZEUR'): # No need to calc changes for EUR fiat
			oldData = getOldvalues(attr[-3:]+'EUR')
			weekChange = value-(pair*oldData[0])
			dayChange = value-(pair*oldData[1])

			for e in compound:
				if e[0] in attr:
					change = float("%.2f" % float(value-e[2]))

		totalChange += change
		totalDayChange += dayChange
		totalWeekChange += weekChange

		changeStr = ''
		if change > 0:
			changeStr = colored(str("%.2f" % change)+' EUR', 'white', 'on_cyan')
		elif change < 0:
			changeStr = colored(str("%.2f" % change)+' EUR', 'white', 'on_red')

		weekChangeStr = ''
		if weekChange > 0:
			weekChangeStr = colored(str("%.2f" % weekChange)+' EUR', 'white', 'on_cyan')
		elif weekChange < 0:
			weekChangeStr = colored(str("%.2f" % weekChange)+' EUR', 'white', 'on_red')

		dayChangeStr = ''
		if dayChange > 0:
			dayChangeStr = colored(str("%.2f" % dayChange)+' EUR', 'white', 'on_cyan')
		elif dayChange < 0:
			dayChangeStr = colored(str("%.2f" % dayChange)+' EUR', 'white', 'on_red')


		toPrint = [colored(attr, 'grey', 'on_yellow'), str(pair), colored(valueStr, 'white', 'on_magenta'), changeStr, dayChangeStr, weekChangeStr]

		table.append(toPrint)


	totalChangeStr = ''
	if totalChange > 0:
		totalChangeStr = colored(str("%.2f" % totalChange)+' EUR', 'white', 'on_cyan')
	elif totalChange < 0:
		totalChangeStr = colored(str("%.2f" % totalChange)+' EUR', 'white', 'on_red')

	totalDayChangeStr = ''
	if totalDayChange > 0:
		totalDayChangeStr = colored(str("%.2f" % totalDayChange)+' EUR', 'white', 'on_cyan')
	elif totalDayChange < 0:
		totalDayChangeStr = colored(str("%.2f" % totalDayChange)+' EUR', 'white', 'on_red')

	totalWeekChangeStr = ''
	if totalWeekChange > 0:
		totalWeekChangeStr = colored(str("%.2f" % totalWeekChange)+' EUR', 'white', 'on_cyan')
	elif totalWeekChange < 0:
		totalWeekChangeStr = colored(str("%.2f" % totalWeekChange)+' EUR', 'white', 'on_red')

	table.append([colored('Total', 'white', 'on_blue'), 'x', colored( str(int(float( balance['eb'] )))+' EUR', 'white', 'on_green'), totalChangeStr, totalDayChangeStr, totalWeekChangeStr])


	os.system('clear')

	print tabulate(table, tablefmt="grid")

while 1:
	try:
		updateLivevalues()
		printTrades()
		printBalance()
	except:
		cprint('Error getting balance.', 'red')

	time.sleep(60)