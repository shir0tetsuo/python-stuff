import discord
from discord.ext import commands
import json
import os
import time
from datetime import timedelta
import re
from hashlib import sha256

# Check if the Operating System is Windows(NT) or Linux(Posix) then make a path to a hidden folder with the chains in it.
if os.name == 'nt':
    main_path = os.path.realpath(__file__).split('\\')
    main_path.remove(main_path[-1])
    main_path = '\\'.join(main_path) + '\\'
    # The hidden folder with your chains.
    main_folder = '{}.avaira'.format(main_path)
    '''The place where all chain .json are stored.'''
else:
    main_path = os.getcwd() + '/'
    main_folder = '{}.avaira'.format(main_path)

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
'''Genesis Block Signature'''

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

#
#
# THE DISCORD SIDE OF THINGS
#
#

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}! use --help to display help.')

    async def on_message(self, message):
        if (str(message.author.id) == '303309686264954881'):

            if message.content.split(' ')[0].lower() == '--help':
                help_lines = [
                    '`in` inspects or appends to block in chunk ||in 0x00 :black_circle: test||',
                    '`list` displays the chunks in list',
                    '`trail` inspects the block index in chunk ||trail 0x00 0||',
                    '`rm` removes the chunk ||rm 0x00||',
                    '`--help` <- you are here'
                ]
                return await message.channel.send('\n'.join(help_lines))

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
                
                F = Floor(hex_index = args[1])
                B = F.chain[int(args[2])]

                pristine = ':green_circle:' if F.pristine else ':red_circle:'
                data = [
                        '__`{}`__ ({}) {}'.format(F.hex_index, F.numerical, pristine),
                        '> #{} {} "{}"'.format(B.index, B.symbol, B.comment),
                        '> `{}`'.format(B.compute_hash()),
                        '{} (since: {})'.format(time.ctime(B.timestamp), F.time_gap)
                    ]
                return await message.channel.send('\n'.join(data))


            if message.content.split(' ')[0].lower() == 'rm':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try:
                    int(args[1], base=16)
                except ValueError:
                    return
                
                Floor(hex_index = args[1]).delete()
                return await message.channel.send('Deleted {}'.format(args[1]))

            if message.content.split(' ')[0].lower() == 'in':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    int(args[1], base=16)
                except ValueError:
                    return await message.channel.send('Not base 16')

                chain = Floor(hex_index = args[1])
                last_block = chain.last_block

                if len(args) == 2:
                    pristine = ':green_circle:' if chain.pristine else ':red_circle:'
                    data = [
                        '__`{}`__ ({}) {}'.format(chain.hex_index, chain.numerical, pristine),
                        '> #{} {} "{}"'.format(last_block.index, last_block.symbol, last_block.comment),
                        '> `{}`'.format(last_block.compute_hash()),
                        '{} (since: {})'.format(time.ctime(last_block.timestamp), chain.time_gap)
                    ]
                    return await message.channel.send('\n'.join(data))
                
                if len(args) > 2:
                    symbol = args[2]
                    trail_position = len(args[0]) + len(args[1]) + len(args[2]) + 3
                    comment = message.content[trail_position:]
                    if not comment:
                        comment = ""
                    Floor(hex_index = args[1]).add(symbol, comment)
                    return await message.channel.send("Data added.")

            if message.content.split(' ')[0].lower() == 'list':
                args = message.content.split(' ')
                if len(args) < 2:
                    return
                
                try: 
                    point = int(args[1], base=16)
                except ValueError:
                    return await message.channel.send('Not base 16')
                
                # start, stop, step 1
                lowest = point - 5
                highest = point + 6
                all_pt = []
                for index in reversed(range(lowest, highest, 1)):
                    pt = Floor(hex_index = hex(index))
                    if index == point:
                        all_pt.append('> -> {} `{}` "{}"'.format(pt.last_block.symbol, pt.hex_index, pt.last_block.comment))
                    else:
                        all_pt.append('> {} `{}`'.format(pt.last_block.symbol, pt.hex_index))
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
client.run('') # YOUR BOT KEY
