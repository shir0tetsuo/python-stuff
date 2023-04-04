import discord
from discord.ext import commands
import random
import json
import os
import time
from datetime import timedelta
import re
from hashlib import sha256
# just a discord_token.py file with bot_token string
import discord_token
bot_token = discord_token.bot_token

shadow_folder = '.inpw'
'''This is the folder where all of the .json will be saved.'''

# Check if the Operating System is Windows(NT) or Linux(Posix) then make a path to a hidden folder with the chains in it.
if os.name == 'nt':
    main_path = os.path.realpath(__file__).split('\\')
    main_path.remove(main_path[-1])
    main_path = '\\'.join(main_path) + '\\'
    # The hidden folder with your chains.
    main_folder = '{}{}'.format(main_path, shadow_folder)
    '''The place where all chain .json are stored.'''
else:
    main_path = os.getcwd() + '/'
    main_folder = '{}{}'.format(main_path, shadow_folder)

# MODIFY FOR YOUR PURPOSES.

bot_handler_users = [
    '303309686264954881'
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
genesis_signature = 'Genesis Block [shadowsword#0179] VERSION {} {}'.format(this_hash, this_modified_time) # or "Genesis"
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

def RandomHex():
    return hex(random.randint(0,65536))
#
#
# THE DISCORD SIDE OF THINGS
#
#

def command_help():
    '''The Discord-side help command execution, returns prepared string.'''
    help_lines = [
                    '`in` inspects or appends to block in chunk ||in 0x0 :black_circle: test||',
                    '`list` displays the chunks in list ||list 0x0 (int(chunk-index))||',
                    '`trail` inspects the block index in chunk ||trail 0x0 0||',
                    '`rm` removes the chunk ||rm 0x0||',
                    '`--random` returns hex value between 0 and 65536',
                    '`--help` <- you are here'
                ]
    return '\n'.join(help_lines)

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}! use --help to display help.')

    async def on_message(self, message):
        if (str(message.author.id) in bot_handler_users):

            # --HELP
            if message.content.split(' ')[0].lower() == '--help':
                return await message.channel.send(command_help())

            # GETRANDHEX
            if message.content.split(' ')[0].lower() == '--random':
                return await message.channel.send('`{}`'.format(RandomHex()))

            # TRAIL
            if message.content.split(' ')[0].lower() == 'trail':
                args = message.content.split(' ')
                if len(args) < 3:
                    return
                
                # hex_index
                try:
                    int(args[1], base=16)
                except ValueError:
                    return await message.channel.send('Not base 16')
                
                # index number
                try:
                    int(args[2])
                except ValueError:
                    return await message.channel.send('Index Unknown')
                
                F = Floor(hex_index = args[1].lower())
                B = F.chain[int(args[2])]

                pristine = ':green_circle:' if F.pristine else ':red_circle:'
                pristine_diff = ':green_circle:' if F.pristine_difficulty else ':red_circle:'
                pristine_gen = ':green_circle:' if F.pristine_genesis else ':red_circle:'
                data = [
                        '__`{}`__ ({})'.format(F.hex_index, F.numerical, pristine),
                        '> #{} {} "{}"'.format(B.index, B.symbol, B.comment),
                        '> `{}`'.format(B.compute_hash()),
                        '',
                        '> `history` {} `difficulty` {} `genesis version` {} '.format(pristine, pristine_diff, pristine_gen),
                        '> `prev_hash {}`'.format(B.previous_hash),
                        '{} (since: {})'.format(time.ctime(B.timestamp), F.time_gap)
                    ]
                return await message.channel.send('\n'.join(data))

            # RM
            if message.content.split(' ')[0].lower() == 'rm':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try:
                    int(args[1], base=16)
                except ValueError:
                    return
                
                Floor(hex_index = args[1].lower()).delete()
                return await message.channel.send('Deleted {}'.format(args[1]))

            # IN
            if message.content.split(' ')[0].lower() == 'in':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    int(args[1], base=16)
                except ValueError:
                    return

                chain = Floor(hex_index = args[1].lower())
                last_block = chain.last_block

                if len(args) == 2:
                    pristine = ':scroll:' if chain.pristine else ':fire:'
                    pristine_diff = ':chains:' if chain.pristine_difficulty else ':wrench:'
                    pristine_gen = ':milky_way:' if chain.pristine_genesis else ':city_sunset:'
                    data = [
                        '__`{}`__ ({})'.format(chain.hex_index, chain.numerical),
                        '> #{} {} "{}"'.format(last_block.index, last_block.symbol, last_block.comment),
                        '> `{}`'.format(last_block.compute_hash()),
                        '> :lab_coat: ||{}{}{}||'.format(pristine, pristine_diff, pristine_gen),
                        '{} (since: {})'.format(time.ctime(last_block.timestamp), chain.time_gap),
                        
                    ]
                    return await message.channel.send('\n'.join(data))
                
                if len(args) > 2:
                    symbol = args[2]
                    trail_position = len(args[0]) + len(args[1]) + len(args[2]) + 3
                    comment = message.content[trail_position:]
                    if not comment:
                        comment = ""
                    Floor(hex_index = args[1].lower()).add(symbol, comment)
                    return await message.channel.send("Data added.")

            # LIST
            if message.content.split(' ')[0].lower() == 'list':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    point = int(args[1], base=16)
                except ValueError:
                    return await message.channel.send('Not base 16')
                
                # start, stop, step 1
                lowest = point - 8
                highest = point + 9
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
                    return await message.channel.send('\n'.join(all_pt))

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

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(bot_token)
