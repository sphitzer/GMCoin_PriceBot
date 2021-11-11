import requests
from loguru import logger
import argparse
import asyncio

import discord
from discord.ext import commands

#command line parameters (temp until better solution)
parser = argparse.ArgumentParser(description='pricebot settings.  channel,guild,frequency args optional to provide regular updates to a single channel')
parser.add_argument('--token', dest='discord_token', required=True)
parser.add_argument('--guild', dest='discord_guild', required=False)
parser.add_argument('--channel', dest='discord_channel', required=False)
parser.add_argument('--frequency', dest='freq',  required=False,
                    help='frequency to check price in SECONDS')
parser.add_argument('--log', dest='log_level',  default='INFO',
                    help='frequency to check price in SECONDS')                    
args= parser.parse_args()

#Initialize logger
logger.add("./logs/log_{time}.log", format="{time} {level} {message}", level=args.log_level, rotation="20 MB")
logger.info("GOOD MORNING COIN DISCORD BOT")
logger.info("BE SURE TO HAVE A WONDERFUL GOOD MORNING!!!")

#dexlab API URLs
dexlab_last_price_url = "https://api.dexlab.space/v1/prices/diB1G66nRhvnu41evoXM76TrmBfJTBw9NfFyTK3VuDr/last"
dexlab_24h_vol_url = "https://api.dexlab.space/v1/volumes/diB1G66nRhvnu41evoXM76TrmBfJTBw9NfFyTK3VuDr"

#to store the current version of the price embed to send to the discord client
price_embed = None

#discord client connection 
## need to do some reading on async...
#client = discord.Client()
client = commands.Bot( command_prefix="!" )

@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == '!price':
        await message.channel.send(embed=price_embed)   

#only runs the channel update loop if all three of these values are provided as args
# discord_guild, discord_channel, frequency
#this is dumb, replace with a proper
async def periodic_channel_updates(freq,input_guild,input_channel):
    while True: 
        if(len(client.guilds) > 0):
            for guild in client.guilds:
                if guild.name == input_guild:
                    logger.debug(f'Belongs to guild: {guild}')
                    
                    for channel in guild.channels:
                        if channel.name == input_channel:
                            logger.debug(f'Belongs to channel: {channel}')

                            #pamp it
                            await channel.send(embed=price_embed)
                
        await asyncio.sleep(int(freq))


#refreshes price & volume info from dexlab once every 60 seconds
async def dexlab_data_refresh():
    #get data from dexlab
    price_data_raw = requests.get(dexlab_last_price_url)
    price_vol_raw = requests.get(dexlab_24h_vol_url)

    #extract current price 
    price_data_json = price_data_raw.json()
    current_price = float(price_data_json['data']['price'])

    #extract 24h vol 
    price_vol_json = price_vol_raw.json()
    volume_24h = float(price_vol_json['data']['summary']['totalVolume'])

    #extract vol data
    logger.info("Current price: " + str(round(current_price,6)))
    logger.info("24hr Volume: " + str(round(volume_24h,2)))

    temp_embed = discord.Embed(title="Price Check!",
                color=discord.Color.green())
    temp_embed.add_field(name="**Current Price**", value=f'${str(round(current_price,6))} USDC', inline=False)
    temp_embed.add_field(name="**24 Hour Volume**", value=f'${str(round(volume_24h,2))} USDC', inline=False)
    temp_embed.set_footer(text="All values currently via dexlabs")

    #update the global price embed data
    global price_embed
    price_embed = temp_embed

    #sleep 30 seconds & do it all over again
    await asyncio.sleep(30)



#run discord client loop

#only runs the channel update loop if all three of these values are provided
if args.freq and args.discord_guild and args.discord_channel:
    client.loop.create_task(periodic_channel_updates(args.freq,args.discord_guild,args.discord_channel))

client.loop.create_task(dexlab_data_refresh())
client.run(args.discord_token)

