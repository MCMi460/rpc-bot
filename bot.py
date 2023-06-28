# Created by Deltaion Lee (MCMi460) on Github

import discord
from discord.ext import commands
from PIL import Image
import re
import io
import json
import typing
import requests
import love

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = '.', intents = intents, case_insensitive = True)

# https://www.geeksforgeeks.org/check-if-an-url-is-valid-or-not-using-regular-expression/
regex = ('((http|https)://)(www.)?' +
        '[a-zA-Z0-9@:%._\\+~#?&//=]' +
        '{2,256}\\.[a-z]' +
        '{2,6}\\b([-a-zA-Z0-9@:%' +
        '._\\+~#?&//=]*)'
)
pattern = re.compile(regex)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.id != 1012066992817193001:
            print('Leaving %s: %s' % (guild.id, guild.name))
            await guild.leave()

    print('Logged in as %s (%s)' % (bot.user,bot.user.id))
    print('Present in %s servers.' % len(bot.guilds))
    print('------')
    await bot.change_presence(
        status = discord.Status.online,
        activity = discord.Activity(
            type = discord.ActivityType.listening,
            name = 'your game suggestions'
        )
    )

@bot.event
async def on_message(message):
    await bot.process_commands(message)

# From @AbstractUmbra
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx) -> None:
    synced = await ctx.bot.tree.sync()
    await ctx.send(f'Synced {len(synced)} commands globally')

@bot.tree.command()
@discord.app_commands.checks.cooldown(1, 60)
async def create(interaction:discord.Interaction, title_id:str, short:str, long:str, publisher:str, icon_url:str):
    '''
    Create a new game addition application.
    '''
    channel = bot.get_channel(1123524711742193694)

    try:
        title_id = title_id.upper()
        if not isHex(title_id):
            raise Exception('not real title ID!')
        short, long, publisher, icon_url = tuple(map(str, (short, long, publisher, icon_url)))
        if not re.search(pattern, icon_url):
            raise Exception('not a real URL!')
        startswith = (
            'https://media.discordapp.net/attachments/1123524711742193694/',
            'https://cdn.discordapp.com/attachments/1123524711742193694/',
            'https://github.com/'
        )
        fail = True
        for link in startswith:
            if icon_url.startswith(link):
                fail = False
        if fail:
            raise Exception('please use an image URL uploaded to %s. After uploading, right click (or press share on mobile) to copy the attachment link!' % channel.mention)

        await interaction.response.send_message(
            'Request created by %s.\n# `%s`.\n**Short**: %s\n**Long**: %s\n**Publisher**: %s\n**Icon URL**: <%s>' % (interaction.user.mention, title_id, short, long, publisher, icon_url),
            ephemeral = False
        )

        await interaction.channel.send('1. Passed all checks')

        ret = {
            'short': short,
            'long': long,
            'publisher': publisher,
            'imageID': title_id,
        }
        ret = io.BytesIO(bytes(json.dumps(ret), 'utf-8'))

        await interaction.channel.send('2. Formatted JSON file')

        image_data = requests.get(icon_url).content
        image = Image.open(io.BytesIO(image_data))
        image.resize((48, 48))

        image_data = io.BytesIO()
        image.save(image_data, format = 'PNG')
        image_data.seek(0)

        await interaction.channel.send('3. Formatted icon PNG')

        files = (
            discord.File(fp = image_data, filename = '%s.png' % title_id),
            discord.File(fp = ret, filename = '%s.txt' % title_id),
        )

        await interaction.channel.send('4. Created Discord files')

        message = await (await interaction.original_response()).fetch()

        thread = await channel.create_thread(name = title_id, message = message if interaction.channel.id == 1123524711742193694 else None)

        await interaction.channel.send('5. Created Discord thread (%s)' % thread.mention)

        upload = await thread.send(files = files)

        await interaction.channel.send('6. Uploaded files (%s)' % upload.jump_url)

    except Exception as e:
        try:
            await interaction.response.send_message(
                'Exception encountered!\n%s' % e,
                ephemeral = True
            )
        except:
            await interaction.channel.send('Exception encountered!\n%s' % e)

@create.error
async def create_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(str(error), ephemeral = True)

@bot.tree.command()
@discord.app_commands.checks.cooldown(1, 60)
async def get_title_id(interaction:discord.Interaction, friendcode:int):
    '''
    Gets the current title ID that a user is playing
    '''
    try:
        love.convertFriendCodeToPrincipalId(friendcode)
        headers = {
            'User-Agent': '3DS-RPC/0.31',
        }
        ret = requests.get('https://3dsrpc.com/api/u/%s' % friendcode, headers = headers).json()
        if ret['Exception']:
            raise Exception(ret['Exception'])
        await interaction.response.send_message(
            '`%s`: **%s**, Playing `%s`' % (ret['User']['friendCode'], ret['User']['username'], ret['User'].get('Presence', {}).get('game', {}).get('@id', 'Nothing!')),
            ephemeral = False
        )
    except Exception as e:
        try:
            await interaction.response.send_message(
                'Exception encountered!\n%s' % e,
                ephemeral = False
            )
        except:
            await interaction.channel.send('Exception encountered!\n%s' % e)

@get_title_id.error
async def get_title_id_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(str(error), ephemeral = True)

def isHex(string):
    for char in string:
        if not char.lower() in '0123456789abcdef':
            return False
    return True if string and len(string) == 16 else False

from private import token
bot.run(token)
