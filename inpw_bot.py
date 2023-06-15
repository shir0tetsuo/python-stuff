import discord
from discord.ext import commands
import random
import json
import os
import time
from datetime import timedelta
import statistics
import re
from hashlib import sha256
# just a discord_token.py file with bot_token string
import discord_token
bot_token = discord_token.bot_token

shadow_folder = '.inpw'
'''This is the folder where all of the .json will be saved.'''

listing_length = 9

# Check if the Operating System is Windows(NT) or Linux(Posix) then make a path to a hidden folder with the chains in it.
if os.name == 'nt':
    main_path = os.path.realpath(__file__).split('\\')
    main_path.remove(main_path[-1])
    main_path = '\\'.join(main_path) + '\\'
    # The hidden folder with your chains.
    main_folder = '{}{}'.format(main_path, shadow_folder)
    '''The place where all chain .json are stored.'''
else:
    #main_path = os.getcwd() + '/'
    #main_folder = '{}{}'.format(main_path, shadow_folder)
    main_path = '/home/cpi/nas/python/'
    main_folder = '/home/cpi/nas/python/.inpw'

# MODIFY FOR YOUR PURPOSES.

bot_handler_users = [
    '303309686264954881',
    '383791592873525249'
]
'''Discord userIDs list.'''

# Shouldn't modify unless needed.
if not os.path.exists(main_folder):
    os.makedirs(main_folder)
os.chdir(main_folder)

print('Directory: {}'.format(main_path))
print('main_folder: {}'.format(main_folder))

# Path of this script on the operating system.
this_file = os.path.realpath(__file__)

# this_hash, this_modified_time can be used for other things
with open(this_file,"r") as monitoring_script:
    this_dump = monitoring_script.read().encode('utf-8')
    this_hash = sha256(this_dump).hexdigest()
this_modified_time = time.ctime(os.path.getmtime(this_file))

# This will appear in every Genesis Block and is required for pristine_genesis.
genesis_signature = 'Genesis __[shadowsword#0179]__ {} {}'.format(this_hash, this_modified_time) # or "Genesis"
'''Genesis Block Signature, this script's hash and modification time are included'''

#
# eof out-of-box lines
# 

# a generalized exception
class GenesisOnly(Exception):
    "Only Genesis Block found, Nothing to compare."
    pass

# Quick return of what is in the main folder. Starting here, can be modified to include server nodes etc...
def Get():
    '''Return a list of Chains class files with `Chains.Get()`.'''
    zones = [Floor(ch.replace('.json','')) for ch in next(os.walk('.'))[2] if re.compile(r'.*.json$').match(ch)]
    for idx, ch in list(enumerate(zones)):
        print('{}: {} Loaded'.format(idx, ch.name))
    return zones

def DetermineDifficulty(proof_of_work_hash):
    count = 0
    for char in proof_of_work_hash:
        if char == '0':
            count += 1
        else:
            break
    return count

def RandomHex():
    return hex(random.randint(0,65536))

def ptime(time_float : float):
    return time.ctime(time_float)

def subtract_time(more_recent : float, less_recent : float):
    return str(timedelta(seconds=(more_recent - less_recent)))

def objects_between_timestamps(objects : list, older_timestamp : float, newer_timestamp : float):
    '''Compare timestamp floats to object timestamp in list (`2628288` is roughly a month in seconds)'''
    for obj in objects:
        if older_timestamp <= obj.timestamp <= newer_timestamp:
            yield obj

#
#
# THE DISCORD SIDE OF THINGS
#
#

def command_help():
    '''The Discord-side help command execution, returns prepared string.'''
    help_lines = [
                    'A strange note-taking system.',
                    '**Floors** are hexadecimal values like `0x0`, `0xff`, `0xffffff`; There are a finite number of floors.',
                    'Floors contain **chunks,** they are small pieces of data that have a **symbol** :black_circle: which may indicate the type of information.',
                    'Chunks are similar to blocks in a block chain. The information can be verified for authenticity using the **timewarp** command, also revealing the floor integrity.',
                    'Chunk information can be associated with other chunks in the **chunk map** revealing nearby **chunks** on their **floor.**',
                    'Each floor has a file, each file containing the **chunk chain** for information on that floor, which can be compared and inspected retroactively.',
                    'Verifying data may hint at a loss of file integrity due to radiation or degredation of the TF Card the information is stored on (or careless manipulation).',
                    '`puts` inspects or appends to new chunk in floor ||puts 0x0 :black_circle: test||',
                    '`list` displays the chunks in list from floor ||list 0x0 [chunk-integer]||',
                    '`miss` reveals a mission brief format of the selected chunk ||miss 0x0 [chunk-integer]||',
                    '`rm1` removes only the last chunk in a floor ||rm1 0x0||',
                    '`rmall` removes the floor ||rmall 0x0||',
                    '`timewarp` reveals snapshot of the time of the chunk creation ||timewarp 0x0 1||',
                    '`--random` returns hex value between 0 and 65536',
                    '`--help` <- you are here',
                    'By default only the (creator) of the bot has permission to use the bot commands They are listed in the **Genesis Chunk** or index 0.'
                ]
    return '\n'.join(help_lines)

def isbase16(string):
    try:
        int(string, base=16)
    except ValueError:
        return False
    else:
        return True

def isint(string):
    try:
        int(string)
    except ValueError:
        return False
    else:
        return True
    
def timewarp_2(msg_content):
    args = msg_content.lower().split(' ')[1:]
    if not isbase16(args[0]):
        return
    if not isint(args[1]):
        return
    
    # Target decimal, hexadecimal
    arg_decimal = int(args[0], base=16)
    arg_hexadecimal = hex(arg_decimal)
    arg_selected_decimal = int(args[1])
    
    # Set the target floor variables
    FLR = Floor(hex_index=str(arg_hexadecimal))

    # Floor chunks of interest
    FLR_chunk_last = FLR.last_block
    FLR_chunk_genesis = FLR.genesis_block
    FLR_chunk_secondlast = FLR.second_last_block
    try:
        FLR_chunk_selected = FLR.chain[arg_selected_decimal]
    except IndexError:
        FLR_chunk_selected = FLR.last_block

    # Other floors listing lengths
    lowest = arg_decimal - (listing_length - 1)
    highest = arg_decimal + (listing_length)

    time_now = time.time()

    # 4$, $$
    time_recent = ptime(FLR_chunk_last.timestamp)
    time_since_recent = subtract_time(time_now, FLR_chunk_last.timestamp) # NOW(FUTURE)
    # X, $$
    time_selected = ptime(FLR_chunk_selected.timestamp)
    time_since_selected = subtract_time(time_now, FLR_chunk_selected.timestamp) # RETROSPECT
    # 0, $$
    time_genesis = ptime(FLR_chunk_genesis.timestamp)
    time_since_genesis = subtract_time(time_now, FLR_chunk_genesis.timestamp) # PAST

    # 0-X-4$
    time_between_selected_last = subtract_time(FLR_chunk_last.timestamp, FLR_chunk_selected.timestamp) # X, 4$
    time_between_selected_genesis = subtract_time(FLR_chunk_selected.timestamp, FLR_chunk_genesis.timestamp) # 0, X

    # 0-4$
    time_between_recent_genesis = subtract_time(FLR_chunk_last.timestamp, FLR_chunk_genesis.timestamp) # 0, 4$

    # 3-4$
    time_between_recent_secondlast = subtract_time(FLR_chunk_last.timestamp, FLR_chunk_secondlast.timestamp) # 3, 4$

    # Chunks, retroactive class objects, between a month ago and the selected chunk TS.
    historic_chunks = objects_between_timestamps(FLR.chain, (FLR_chunk_selected.timestamp-2628288), FLR_chunk_selected.timestamp) # history of the floor within past month
    historic = [
       '> {} `#{}` `@[{}]` {} '.format(hchunk.symbol, hchunk.index, ptime(hchunk.timestamp), hchunk.comment) for hchunk in historic_chunks
    ]
    # Ensure compliance
    while len('\n'.join(historic)) > 4070:
        historic.pop(0)

    field_chunk_map = []
    # CHUNK MAP goes here
    for floor_integer in reversed(range(lowest, highest, 1)):
        is_selected_floor = True if floor_integer == arg_decimal else False
        is_commented_floor = True if floor_integer in list(range((arg_decimal-2),(arg_decimal+3),1)) else False
        floor_working = Floor(hex_index = str(hex(floor_integer)))
        if is_commented_floor and not is_selected_floor and floor_working.last_block.index > 0:
            field_chunk_map.append('> {} `{}` `#{}` {}'.format(floor_working.last_block.symbol, floor_working.hex_index, floor_working.last_block.index, floor_working.last_block.comment))
        elif is_selected_floor:
            field_chunk_map.append('`->` __{} `{}` `#{}`__ {}'.format(floor_working.last_block.symbol, floor_working.hex_index, floor_working.last_block.index, floor_working.last_block.comment))
        else:
            field_chunk_map.append('> {} `{}` `#{}`'.format(floor_working.last_block.symbol, floor_working.hex_index, floor_working.last_block.index))
    
    field_timewarp_map = []
    # TIMEWARP CHUNK MAP goes here
    for floor_integer in reversed(range(lowest, highest, 1)):
        is_selected_floor = True if floor_integer == arg_decimal else False
        floor_working = Floor(hex_index = str(hex(floor_integer)))

        if not is_selected_floor:
            using_chunk_index = 0
            for chunk in floor_working.chain:
                if not chunk.timestamp > FLR_chunk_selected.timestamp:
                    using_chunk_index = chunk.index
        else:
            using_chunk_index = FLR_chunk_selected.index
        
        inspect_chunk = floor_working.chain[using_chunk_index]
        ic_floor = floor_working.hex_index
        ic_symbol = inspect_chunk.symbol
        ic_index = inspect_chunk.index
        ic_timesince = subtract_time(FLR_chunk_selected.timestamp, inspect_chunk.timestamp)
        ic = [ic_floor, ic_symbol, ic_index, ic_timesince]

        is_genesis = True if ic_index == 0 else False
        
        if not is_selected_floor:
            if is_genesis:
                field_timewarp_map.append('> `{}` {} `#{}`'.format(ic[0], ic[1], ic[2]))
            else:
                field_timewarp_map.append('> `{}` {} `#{}` :pound:`[{}]`'.format(ic[0], ic[1], ic[2], ic[3]))
        else:
            field_timewarp_map.append('`->` `{}` {} `#{}` :dollar:`[{}]`'.format(ic[0],ic[1],ic[2],ic[3]))


    # GLOBAL TIME MAP
    time_map = [
        '__{} `#{}`__ **GENESIS**'.format(FLR_chunk_genesis.symbol, FLR_chunk_genesis.index),
        '> `[{}]`'.format(time_genesis),
        '> `[{} ago]`'.format(time_since_genesis),
        '',
        '__{} `#{}`__ **SELECTED**'.format(FLR_chunk_selected.symbol, FLR_chunk_selected.index),
        '> __`[{}]`__'.format(time_selected),
        #'> ',
        '> `[{} ago]`'.format(time_since_selected),
        '{} `#{}` `[{}]`'.format( FLR_chunk_genesis.symbol, FLR_chunk_genesis.index, time_between_selected_genesis),
        ':yen: `{}`'.format(FLR_chunk_selected.compute_value()),
        '',
        '__{} `#{}`__ **LAST**'.format(FLR_chunk_last.symbol, FLR_chunk_last.index),
        '> `[{}]`'.format(time_recent),
        '> `[{} ago]`'.format(time_since_recent),
        '{} `#{}` `[{}]`'.format(FLR_chunk_genesis.symbol, FLR_chunk_genesis.index, time_between_recent_genesis),
        '{} `#{}` `[{}]`'.format(FLR_chunk_selected.symbol, FLR_chunk_selected.index, time_between_selected_last),
        '{} `#{}` `[{}]`'.format(FLR_chunk_secondlast.symbol, FLR_chunk_secondlast.index, time_between_recent_secondlast),
    ]

    stat_map = [
        '`Pristine Floor: {}`'.format('True' if FLR.pristine else 'False'),
        '`Pristine Genesis: {}`'.format('True' if FLR.pristine_genesis else 'False'),
        '`Pristine Difficulty: {}`'.format('True' if FLR.pristine_difficulty else 'False'),
        '`Hash_.: {}..., Nonce: {}`'.format(FLR_chunk_selected.compute_hash()[:8], FLR_chunk_selected.nonce),
        '`Hash_P: {}...`'.format(FLR_chunk_selected.previous_hash[:8]),
        '``` {} ```'.format(FLR_chunk_selected.comment),
        ':hourglass: **NOW**',
        '> `[{}]`'.format(ptime(time_now)),
    ]

    embed_title = 'Timewarp `{} ({}) #{}` '.format(arg_hexadecimal, arg_decimal, FLR_chunk_selected.index)
    embed_stats_title = '__`{}` {} `#{}`__'.format(arg_hexadecimal, FLR_chunk_selected.symbol, FLR_chunk_selected.index)
    embed_timemap_title = '`{}` {} `#{}` `=>` __{} `#{}`__ `=>` {} `#{}`'.format(FLR.hex_index, FLR_chunk_genesis.symbol, FLR_chunk_genesis.index, FLR_chunk_selected.symbol, FLR_chunk_selected.index, FLR_chunk_last.symbol, FLR_chunk_last.index)
    embed = discord.Embed(title=embed_title,description='Month in Retrospect:\n'+'\n'.join(historic))
    embed.add_field(name='Chunk Map',value='\n'.join(field_chunk_map),inline=False)
    embed.add_field(name='Timewarp Chunk Map',value='\n'.join(field_timewarp_map),inline=False)
    embed.add_field(name=embed_stats_title,value='\n'.join(stat_map),inline=True)
    embed.add_field(name=embed_timemap_title,value='\n'.join(time_map),inline=True)

    return embed

def Missionprint2(msg_content):
    args = msg_content.lower().split(' ')[1:]
    try:
        if not isbase16(args[0]):
            return
        if not isint(args[1]):
            return
    except IndexError:
        return
    
    arg_decimal = int(args[0], base=16)
    arg_hexadecimal = hex(arg_decimal)
    arg_selected_decimal = int(args[1])

    FLR = Floor(hex_index=str(arg_hexadecimal))
    try:
        FLR_chunk_selected = FLR.chain[arg_selected_decimal]
    except IndexError:
        FLR_chunk_selected = FLR.last_block

    FLR_chain_integer = FLR_chunk_selected.index

    embed = discord.Embed()
    return embed

def Missionprint(msg_content):
    args = msg_content.lower().split(' ')[1:]
    try:
        if not isbase16(args[0]):
            return
        if not isint(args[1]):
            return
    except IndexError:
        return
    
    arg_decimal = int(args[0], base=16)
    arg_hexadecimal = hex(arg_decimal)
    arg_selected_decimal = int(args[1])

    FLR = Floor(hex_index=str(arg_hexadecimal))
    try:
        FLR_chunk_selected = FLR.chain[arg_selected_decimal]
    except IndexError:
        FLR_chunk_selected = FLR.last_block

    output = []
    worth = 0
    all_worths = []

    if len(FLR.chain) > 1:
        for index, chunk in list(enumerate(FLR.chain[1:])):
            ic_floor = FLR.hex_index
            ic_symbol = chunk.symbol
            ic_index = chunk.index
            ic_value = chunk.compute_value()
            ic_comment = chunk.comment
            worth += ic_value
            all_worths.append(ic_value)
            if FLR_chunk_selected.index == ic_index:
                output.append('`->` `{}` {} `#{}` :yen: `{}`'.format(ic_floor, ic_symbol, ic_index, ic_value))
            else:
                output.append('> `{}` {} `#{}` :yen: `{}` '.format(ic_floor, ic_symbol, ic_index, ic_value))
        while len(output) > 7:
            output.pop(0)
        worths_mean = round(statistics.mean(all_worths))
        output.append('> `{}` :grey_question: `#{}` :yen: `~ {}`'.format(ic_floor, (FLR.last_block.index+1), worths_mean))
        #output.append()
    else:
        output = ['Only the GENESIS chunk was found.']
    
    selected_data = '> :yen: `{}`\n``` {} ```'.format(FLR_chunk_selected.compute_value(), FLR_chunk_selected.comment)

    while len('\n'.join(output)) > 2048:
        output.pop(0)

    stack_level = round(((worth-ic_value)/512)+1)

    embed_title = 'Summary `{}` {}'.format(FLR.hex_index, FLR_chunk_selected.symbol)
    embed_description = ':yen: `{}` `lvl {}`'.format(worth, stack_level)
    embed_field_name = '`#{}` `@[{}]`'.format(FLR_chunk_selected.index, ptime(FLR_chunk_selected.timestamp))
    embed = discord.Embed(title=embed_title,description=embed_description)
    embed.add_field(name=embed_field_name,value=selected_data,inline=True)
    embed.add_field(name='Latest',value='\n'.join(output),inline=True)
    return embed

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}! use --help to display help.')

    async def on_message(self, message):

        message_author = str(message.author.id)

        if len(message.content) == 0:
            return
        
        message_command = message.content.split(' ')[0].lower()
        message_args = message.content.lower().split(' ')[1:]

        if (message_author in bot_handler_users):

            # --HELP
            if message_command == '--help':
                return await message.channel.send(command_help())

            # GETRANDHEX
            if message_command == '--random':
                return await message.channel.send('`{}`'.format(RandomHex()))
            
            # MISSION2
            if message_command in ['m2','m']:
                embed = Missionprint2(message.content)
                if not embed:
                    return
                return await message.channel.send(embed=embed)

            # MISSION
            if message_command in ['miss','scope']:
                embed = Missionprint(message.content)
                if not embed:
                    return
                return await message.channel.send(embed=embed)
            
            # TIMEWARP
            if message_command in ['timewarp','tw','trail']:
                msg_reply = timewarp_2(message.content)

                if not msg_reply:
                    return

                if isinstance(msg_reply, str):
                    return await message.channel.send(msg_reply)
                else:
                    return await message.channel.send(embed=msg_reply)

            # RM
            if message_command == 'rmall':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try:
                    int(args[1], base=16)
                except ValueError:
                    return
                
                Floor(hex_index = args[1].lower()).delete()
                return await message.channel.send('Deleted {}'.format(args[1]))

            # PUTS
            if message_command in ['puts', 'ins']:
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    int(args[1], base=16)
                except ValueError:
                    return
                
                if not args[1].startswith('0x') and not args[1].startswith('-0x'):
                    return await message.channel.send('Floor `{}` missing hexadecimal header `0x`, command rejected.'.format(args[1]))

                chain = Floor(hex_index = args[1].lower())
                last_block = chain.last_block

                if len(args) == 2:
                    data = [
                        '__`{}`__ ({})'.format(chain.hex_index, chain.numerical),
                        '> __{} `#{}`__ "{}"'.format(last_block.symbol, last_block.index, last_block.comment),
                        '> `{}`'.format(last_block.compute_hash()),
                        '> `{}`'.format(time.ctime(last_block.timestamp))
                    ]
                    return await message.channel.send('\n'.join(data))
                
                if len(args) > 2:
                    symbol = args[2]
                    try:
                        # Make sure that it's not a number because we don't want just numbers.
                        int(symbol)
                    except ValueError:
                        trail_position = len(args[0]) + len(args[1]) + len(args[2]) + 3
                        comment = message.content[trail_position:]
                        if not comment:
                            comment = ""
                        Floor(hex_index = args[1].lower()).add(symbol, comment)
                        return await message.channel.send("Data added.")
                    else:
                        return await message.channel.send("Did you mean to use `tw`?")
                    
            # RM SMALL
            if message_command in ['rm','rm1']:
                if not isbase16(message_args[0]):
                    return
                F = Floor(hex_index = message_args[0])
                F.chain.pop(-1)
                F.save()
                return await message.channel.send('Done.')

            # LIST
            if message_command in ['list','li']:
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    point = int(args[1], base=16)
                except ValueError:
                    return await message.channel.send('Not base 16')
                
                # start, stop, step 1
                lowest = point - (listing_length - 1)
                highest = point + listing_length
                all_pt = []

                try:
                    index_argument = int(args[2])
                except Exception:
                    index_argument = -1
                
                if index_argument != -1:
                    for index_chunk in reversed(range(lowest, highest, 1)):
                        pt = Floor(hex_index = hex(index_chunk))
                        try:
                            chunk = pt.chain[index_argument]
                        except Exception:
                            chunk = pt.last_block
                        if index_chunk == point:
                            all_pt.append('')
                            all_pt.append('> <- {} `{}` `#{}` {}'.format(chunk.symbol, pt.hex_index, chunk.index, chunk.comment))
                            all_pt.append('> -> {} `{}` `#{}` {}'.format(pt.last_block.symbol, pt.hex_index, pt.last_block.index, pt.last_block.comment))
                            delta_point = str(timedelta(seconds=(pt.last_block.timestamp - chunk.timestamp)))
                            all_pt.append('> <--> `[{}]` ({} & {})'.format(delta_point, time.ctime(chunk.timestamp), time.ctime(pt.last_block.timestamp)))
                            all_pt.append('')
                        else:
                            all_pt.append('> {} `{}` `#{}`'.format(chunk.symbol, pt.hex_index, chunk.index))
                    
                    all_pt.append('`trail mode`')
                    return await message.channel.send('\n'.join(all_pt))

                else:
                    for index in reversed(range(lowest, highest, 1)):
                        pt = Floor(hex_index = hex(index))
                        if index == point:
                            all_pt.append('> -> {} `{}` `#{}` {}'.format(pt.last_block.symbol, pt.hex_index, pt.last_block.index, pt.last_block.comment))
                        else:
                            all_pt.append('> {} `{}` `#{}`'.format(pt.last_block.symbol, pt.hex_index, pt.last_block.index))
                    embed = discord.Embed(title='List').add_field(name="Chunk Map",value='\n'.join(all_pt))
                    return await message.channel.send(embed=embed)

            pass
        #print(f'Message from {message.author}: {message.content}')

def Load(filename):
    '''# Load JSON Rows from File.
    json object <= line <= filename'''
    loaded = []
    if os.path.exists(filename):
        with open(filename) as f:
            for line in f:
                loaded.append(json.loads(line.rstrip()))
    return loaded


class Floor:
    def __init__(self, hex_index):
        self.hex_index = hex_index
        self.numerical = int(self.hex_index, base=16)

        self.file = '{}.json'.format(self.hex_index)

        chain_raw = [row for row in Load(self.file)]
        self.chain = []

        for data in chain_raw:
            block = Block(index = data['index'],
                          timestamp = data['timestamp'],
                          previous_hash = data['previous_hash'],
                          symbol = data['symbol'],
                          comment = data['comment'],
                          nonce = data['nonce']
                          )
            self.chain.append(block)
        
        self.genesis_time = time.time()

        # Create Genesis Block
        if len(self.chain) == 0:
            genesis_block = Block(
                0, self.genesis_time, "0", ":black_circle:", genesis_signature, 0
            )
            self.chain.append(genesis_block)
        
        #self.ownership = self.last_block.ownership
    
    def delete(self):
        if os.path.exists(self.file):
            os.remove(self.file)
        print('Chain {} removed.'.format(self.file))
        return
    
    def add(self, symbol, comment):
        last_block = self.last_block

        block = Block(index = last_block.index+1, 
                      timestamp = time.time(), 
                      previous_hash = last_block.compute_hash(),
                      symbol = symbol,
                      comment = comment)
        proof = self.proof_of_work(block)

        if (block.compute_hash() == proof):
            self.chain.append(block)
        
        self.save()
        return block.index
    
    def save(self):
        with open(self.file, 'w') as write_file:
            for block in self.chain:
                write_file.write(json.dumps(block.__dict__) + '\n')
        write_file.close()
        return
    
    @property
    def time_gap(self):
        try:
            if len(self.chain) > 1:
                time_gap = str(timedelta(seconds=(self.chain[-1].timestamp - self.chain[-2].timestamp)))
            else:
                raise GenesisOnly
        except GenesisOnly:
            time_gap = "N/A"
        return time_gap
    
    @property
    def last_block(self):
        return self.chain[-1]
    
    @property
    def genesis_block(self):
        return self.chain[0]
    
    @property
    def second_last_block(self):
        if len(self.chain) > 1:
            return self.chain[-2]
        else:
            return self.chain[-1]
    
    @property
    def pristine(self):
        verified = True
        for index in reversed(range(len(self.chain))):
            if index > 0:
                if self.chain[index-1].compute_hash() != self.chain[index].previous_hash:
                    verified = False
        return verified
    
    @property
    def pristine_genesis(self):
        return True if self.chain[0].comment == genesis_signature else False
    
    @property
    def pristine_difficulty(self):
        verified = True
        for index in reversed(range(len(self.chain))):
            if index > 0:
                if not self.chain[index].compute_hash().startswith('0' * Floor.difficulty):
                    verified = False
        return verified
    
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * Floor.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        
        return computed_hash
    
    difficulty = 2

class Block:
    '''# BLock
    `Block.compute_hash()` returns block hash, 
    which is required for creating a new block. This is
    how integrity is maintained.
    '''
    def __init__(self, index, timestamp, previous_hash, symbol, comment = "", nonce = 0):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.symbol = symbol
        self.comment = comment
        self.nonce = nonce

    def compute_hash(self):
        '''Compute the SHA256 hash of this class as a sum of the class data structure.'''
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()
    
    def compute_value(self):
        current_hash = self.compute_hash()
        current_difficulty = DetermineDifficulty(current_hash)
        difficulty_math = (current_difficulty*0.75) * (self.nonce/2)
        comment_value = (len(self.comment) / 2) * (current_difficulty*0.55)
        value = round(difficulty_math + comment_value)
        return value

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(bot_token)
