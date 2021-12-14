# bot.py
import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

@tasks.loop(seconds = 10) # repeat after every 10 seconds
async def myLoop():
	print("looping!")


	the_elect = ['skreee#8782', 'Dunnerhomes#8233']
	elect_ids = ['<@186725927571423232>','<@187395801239126017>']


	channel = client.get_channel(905863726136180806)
	targ_channel = client.get_channel(906761956894076968)
	#check for orders
	f = open('./botfile.txt', 'r')
	orders = f.read()
	f.close()

	f = open('./botfile.txt', 'w')
	f.write('')
	f.close()

	print("digesting botfile orders...")

	orders = orders.split('\n')

	i = 0
	while(i < len(orders)):
		print("%d"%(i))
		print(orders[i])
		if(orders[i] != ''):
			o = orders[i].split(',')
			oc = orders[i].split('|')
			content = oc[1]
			#targ_channel = (o[0].split(' '))[1]
			#targ_channel = int(targ_channel)
			#targ_channel = client.get_channel(targ_channel)
			print("posting...")
			if(o[1] == 'post image'):
				print("posting img %s"%(content))
				await targ_channel.send(file=discord.File(content))
			elif(o[1] == 'post text'):
				print("posting text %s"%(content))
				if '@' in content:
					cnt = content.split('@')
					usr = cnt[2]
					usrid = 'None'
					c = 0
					while(c < len(the_elect)):
						if(the_elect[c] == usr):
							usrid = elect_ids[c]
						c += 1
					content = cnt[0] + cnt[1] + usrid
					print(content)
					print("\n\n")
					await targ_channel.send(content)
				else:
					await targ_channel.send(content)
				#oc = content.split(',')
				#await channel.fetch_message(content)
			else:
				print("something is wrong, input:%s"%(o[1]))

			#botorder = '\nin 906761956894076968,post image,%s\n'%(img_targ)
			#botorder = botorder + 'in 906761956894076968,post text,%s'%(curr_order)
			#await channel.send('hello and welcome to the art gallery')
			#await channel.send(file=discord.File('cheeseburgercat.jpg'))
		i += 1


	#get ID list
	f = open('./botorderids.txt', 'r')
	t = f.read()
	f.close()
	o_ids = t.split('\n')
	print("order ids:")
	print(o_ids)


	#commands channel: 905863726136180806
	async for message in channel.history(limit=10):
		if(str(message.author) in the_elect):
			print(message.content)
			print(message.id)
			print(message.reactions)
			if(message.content == "print current orders"):
				has_printed = False
				for react in message.reactions:
					if('🖨' == str(react)):
						has_printed = True
				if(not has_printed):
					f = open('./currentorderlist.txt', 'r')
					t = f.read()
					f.close()
					if(len(t) > 1900):
						t = t[0:1900]
					await channel.send(t)
					await message.add_reaction('🖨')
			for react in message.reactions:
				if('👍' == str(react)):
					print("thumbsup!")

					#check if this message was posted within the last 3 hours
					c_time = datetime.datetime.utcnow()
					m_time = message.edited_at
					if(m_time == None):
						m_time = message.created_at
					d_time = c_time - m_time
					minutes = d_time.total_seconds() / 60
					if(minutes > 180):
						await message.add_reaction('🕐')
						print("old")
						#if not, give it a clock1 emoji
						break
					else:
						print("fresh")
					print("checking")
					#do some basic checks to see if this message conforms to the order format
					goodorder = False
					mlist = (message.content).split(',')
					if(len(mlist) == 5):
						if(mlist[1].isnumeric() and mlist[3].isnumeric() and mlist[4].isnumeric()):
							if(int(mlist[1]) > 0 and int(mlist[3]) >= 0 and int(mlist[4]) > 0):
								if(int(mlist[4]) > int(mlist[3])):
									goodorder = True
								else:
									print("init step isn't less than total steps")
							else:
								print("numbers are out of range")
						else:
							print("numerics are not numeric")
					else:
						print("incorrect number of elements")
					if(not goodorder):
						await message.add_reaction('⁉')
						#if not, give it an interrobang emoji
						break
					#check if this message ID has already been registered
					if(str(message.id) in o_ids):
						print("message already recorded!")
						break
						#if yes, do nothing

					#else if it passes all checks, then record the order
					await message.add_reaction('💾')
					print('recording new order')

					o1 = (message.content).split(',')
					o2 = int(o1[1])

					f = open('./serverfile.txt', 'a')
					c = 0
					while(c < o2): #duplicate orders for larger 'batches'
						f.write((str(message.id) + ',' + message.content + '\n'))
						c += 1
					f.close()

					o_ids.append(str(message.id))
					f = open('./botorderids.txt', 'a')
					f.write((str(message.id) + '\n'))
					f.close()
					break

	#await channel.send('hello and welcome to the art gallery')
	#await channel.send(file=discord.File('cheeseburgercat.jpg'))

@client.event
async def on_ready():
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	print(
		f'{client.user} is connected to the following guild:\n'
		f'{guild.name}(id: {guild.id})\n'
	)


	myLoop.start()

client.run(TOKEN)
