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
else:
    main_path = os.getcwd() + '/'

# Path of this script on the operating system.
this_file = os.path.realpath(__file__)

# this_hash, this_modified_time can be used for other things
with open(this_file,"r") as monitoring_script:
    this_dump = monitoring_script.read().encode('utf-8')
    this_hash = sha256(this_dump).hexdigest()
this_modified_time = time.ctime(os.path.getmtime(this_file))

# The hidden folder with your chains.
main_folder = '{}.mono'.format(main_path)
'''The place where all chain .json are stored.'''

# This will appear in every Genesis Block and is required for pristine_genesis.
genesis_signature = 'Genesis Block [shadowsword#0179] VERSION {} {}'.format(this_hash, this_modified_time) # or "Genesis"
'''Genesis Block Signature'''

# a generalized exception
class GenesisOnly(Exception):
    "Only Genesis Block found, Nothing to compare."
    pass

# All operations will take place in the main_folder
if not os.path.exists(main_folder):
    os.makedirs(main_folder)
os.chdir(main_folder)

# Quick return of what is in the main folder. Starting here, can be modified to include server nodes etc...
def Get():
    '''Return a list of Chains class files with `Chains.Get()`.'''
    zones = [Chain(ch.replace('.json','')) for ch in next(os.walk('.'))[2] if re.compile(r'.*.json$').match(ch)]
    for idx, ch in list(enumerate(zones)):
        print('{}: {} Loaded'.format(idx, ch.name))
    return zones

def Load(filename):
    '''# Load JSON Rows from File.
    json object <= line <= filename'''
    loaded = []
    if os.path.exists(filename):
        with open(filename) as f:
            for line in f:
                loaded.append(json.loads(line.rstrip()))
    return loaded

class Chain:
    '''# Chain
    Just a simple blockchain engine centered around small note-taking.
    ---
    `.autosave, .name, .chain_blocks_file, .chain_blocks, .genesis_time, .genesis_signature`
    `.delete(), .read_index(int), .read(), .save()`
    `.modified, .value, .pristine, .pristine_genesis, .last_block, .last_block_dict, .time_gap`
    `.block(comment, importance = int)`'''
    def __init__(self, name = "default"):
        self.autosave = True
        self.name = name.lower()

        self.chain_blocks_file = '{}.json'.format(self.name)

        chain_blocks_raw = [row for row in Load(self.chain_blocks_file)]

        self.chain_blocks = []

        # If any of the chains have data in their files, append them to self chains.
        for data in chain_blocks_raw:
            block = Block(index = data['index'],
                          timestamp = data['timestamp'],
                          previous_hash = data['previous_hash'],
                          comment = data['comment'],
                          importance = data['importance'],
                          nonce = data['nonce'])
            self.chain_blocks.append(block)
        
        self.genesis_time = time.time()
        self.genesis_signature = genesis_signature

        # There must always be a genesis block for each class.
        if len(self.chain_blocks) == 0:
            genesis_block = Block(0, self.genesis_time, "0", genesis_signature, 0)
            self.chain_blocks.append(genesis_block)
        
    def delete(self):
        if os.path.exists(self.chain_blocks_file):
            os.remove(self.chain_blocks_file)
        print('Chain {} removed.'.format(self.name))
        return

    def read_index(self, index = -1):
        block = self.chain_blocks[index].__dict__
        print('{}: Block {}'.format(self.name, index))
        for item in block:
            if item == 'timestamp':
                print('{}: {}'.format(item, time.ctime(block[item])))
            else:
                print('{}: {}'.format(str(item), block[item]))
        return
    
    def read(self):
        for chain in self.chain_blocks:
            h = hex(chain.index).split('x')[-1]
            if chain.index != 0:
                print('[0x{:0>4}]:{}: "{}"'.format(h, chain.importance, chain.comment))
    
    @property
    def modified(self):
        if os.path.exists(self.chain_blocks_file):
            last_modified = time.ctime(os.path.getmtime(self.chain_blocks_file))
        else:
            last_modified = 'No File.'
        return last_modified
    
    @property
    def value(self):
        block_values = [blk.nonce for blk in self.chain_blocks]
        value = 0
        for block_value in block_values:
            value = value + block_value
        return value
    
    @property
    def pristine(self):
        verified = True
        for index in reversed(range(len(self.chain_blocks))):
            if index > 0:
                if self.chain_blocks[index-1].compute_hash() != self.chain_blocks[index].previous_hash:
                    verified = False
        return verified
    
    @property
    def pristine_genesis(self):
        verified = True
        genesis_block = self.chain_blocks[0]
        if (genesis_block.comment != self.genesis_signature):
            verified = False
        return verified

    @property
    def last_block(self):
        return self.chain_blocks[-1]
    
    @property
    def last_block_dict(self):
        return self.chain_blocks[-1].__dict__
    
    @property
    def time_gap(self):
        try:
            if len(self.chain_blocks) > 1:
                time_gap = str(timedelta(seconds=(self.chain_blocks[-1].timestamp - self.chain_blocks[-2].timestamp)))
            else:
                raise GenesisOnly
        except GenesisOnly:
            time_gap = "Only the Genesis Block was found."
        return time_gap
    
    def proof_of_work(self, block):
        '''Returns hash, within acceptable difficulty by raising nonce.'''
        block.nonce = 0
        computed_hash = block.compute_hash()
        
        while not computed_hash.startswith('0' * Chain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash
    
    def block(self, comment, importance = 0):
        '''`block(comment, importance = 0)`'''
        last_block = self.last_block

        block = Block(index = last_block.index+1,
                          timestamp = time.time(),
                          previous_hash = last_block.compute_hash(),
                          comment = str(comment),
                          importance = int(importance) or 0)
        # Run Hash Nonce until Proof of Work Satisfied
        proof = self.proof_of_work(block)

        # Ensure the new block's hash has been registered
        if (block.compute_hash() == proof):
            self.chain_blocks.append(block)

        if self.autosave:
            self.save()
        return block.index

    def save(self):
        with open(self.chain_blocks_file, 'w') as write_file:
            for block in self.chain_blocks:
                write_file.write(json.dumps(block.__dict__) + '\n')
        write_file.close()
        print('Save Successful ({})'.format(self.name))

    # '0' * difficulty in the SHA256 hash (Proof-of-Work)
    difficulty = 2

class Block:
    '''# BLock
    `Block.compute_hash()` returns block hash, 
    which is required for creating a new block. This is
    how integrity is maintained.
    '''
    def __init__(self, index, timestamp, previous_hash, comment = "", importance = 0, nonce = 0):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.comment = comment
        self.importance = importance
        self.nonce = nonce

    def compute_hash(self):
        '''Compute the SHA256 hash of this class as a sum of the class data structure.'''
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

z = Get()
