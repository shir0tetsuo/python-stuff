import random, json, os, time, statistics, re, argparse
from hashlib import sha256
from datetime import timedelta

# Modify as desired.
folder_name = '.hcfs'
main_folder = f'{os.getcwd()}{folder_name}'
program_version = '1.0.0'

# Ensure main folder path exists
if not os.path.exists(main_folder):
    os.makedirs(main_folder)
os.chdir(main_folder)

# Location of this file
this_file = os.path.realpath(__file__)

# Calculate this file's hash and mod time
with open(this_file,"r") as this_script:
    this_hash = sha256(this_script.read().encode('utf-8')).hexdigest()
this_modified_time = time.ctime(os.path.getmtime(this_file))

# Use the calculated hash / mod time as the Genesis/Program Signature
program_signature = f'Genesis {this_hash} @{this_modified_time}'
'''Genesis Block Signature'''

# Command Line Arguments
parser = argparse.ArgumentParser(description="Hex Chain File System")
parser.add_argument('--ver', dest='version', action='store_true', help="Print program diagnostic.")
parser.add_argument('--addr', dest='address', type=str, help='Hexadecimal Address (such as 0x1) (*Required)')
parser.add_argument('--gen', action='store_true', help="Display Genesis segments.")
parser.add_argument('--blk', dest='block', type=int, help='Review Block Index Number (Integer).')
parser.add_argument('--sym', dest='symbol', type=str, help='Symbol (Emoji).')
parser.add_argument('--dat', dest='data', type=str, help="Data (String).")
parser.add_argument('--map', action='store_true', help="Display map segments.")
parser.add_argument('--msize', dest='mapsize', type=int, help="Map Size (Integer).")
parser.add_argument('--his', dest='history', action='store_true', help="Display History Retrospect.")
parser.add_argument('--tw', dest='timewarp', action='store_true', help="Display Timewarp Map.")
args = parser.parse_args()

class GenesisOnly(Exception):
    "Only Genesis Block found, Nothing to compare."
    pass

if (args.version):
    print(f'Dir: {main_folder}')
    print(program_version, program_signature)
    exit

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

def Load(filename):
    '''# Load JSON Rows from File.
    json object <= line <= filename'''
    loaded = []
    if os.path.exists(filename):
        with open(filename) as f:
            for line in f:
                loaded.append(json.loads(line.rstrip()))
    return loaded

class Address:
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
                0, self.genesis_time, "0", "🦾", program_signature, 0
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
        return True if self.chain[0].comment == program_signature else False
    
    @property
    def pristine_difficulty(self):
        verified = True
        for index in reversed(range(len(self.chain))):
            if index > 0:
                if not self.chain[index].compute_hash().startswith('0' * Address.difficulty):
                    verified = False
        return verified
    
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * Address.difficulty):
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
    
if (args.address):
    try:
        int(args.address, base=16)
    except ValueError:
        print('Address: ValueError')
        exit
    
    if not args.address.startswith('0x'):
        print('Address: Missing 0x')
        exit

    a_dec = int(args.address, base=16)
    a_hex = hex(a_dec)

    #chain = Address(hex_index = args.address.lower())
    chain = Address(hex_index = a_hex)
    chain_pristine = chain.pristine
    last_block = chain.last_block
    last_block_hash = last_block.compute_hash()
    last_block_value = last_block.compute_value()

    # PRINT LAST BLOCK
    # status line
    '''
    if (args.block):
        if (args.block <= len(chain.chain)):
            blk = args.block
            msg = f'== {chain.hex_index} #{args.block} '
        else:
            blk = last_block.index
            msg = f'== {chain.hex_index} last block '
        print(msg + '='*(len(last_block_hash)-len(msg)+3))
    
        # index, symbol, timestamp, value, pristine
        pristine_status = '\033[1;32mTrue\033[0m' if chain_pristine else '\033[1;33mFalse\033[0m'
        print(f'#{chain.chain[blk].index} {chain.chain[blk].symbol} ({ptime(chain.chain[blk].timestamp)}) ${chain.chain[blk].compute_value()} &Pristine: {pristine_status}')
    '''    

    pristine_status = '\033[1;32mTrue\033[0m' if chain_pristine else '\033[1;33mFalse\033[0m'

    if (args.block) and (args.block <= last_block.index):
        BLOCK = chain.chain[args.block]
        msg = f'== {chain.hex_index} # {BLOCK.index}/{last_block.index} '
        print(msg + '='*(len(last_block_hash)-len(msg)+3))

        # GENESIS 0,1
        print(f'#0 {chain.genesis_block.symbol} Subject: {chain.chain[1].comment}')
        print(f'#1 {chain.chain[1].symbol} ({ptime(chain.genesis_block.timestamp)})')
        print(f'    [{subtract_time(BLOCK.timestamp,chain.genesis_block.timestamp)}] (Genesis -- Selected)')
        print(f'    [{subtract_time(time.time(),chain.genesis_block.timestamp)}] (Genesis -- Now) ')

        # SELECTED
        print(f'\n\033[5m#{BLOCK.index}\033[0m {BLOCK.symbol} ({ptime(BLOCK.timestamp)}) ${BLOCK.compute_value()} &Pristine: {pristine_status}')
        print(f'    [{subtract_time(time.time(),BLOCK.timestamp)}] (Selected -- Now) ')
        print(f'    [{subtract_time(last_block.timestamp,BLOCK.timestamp)}] (Selected -- Last) ')

        print(f'\n#{chain.second_last_block.index} {chain.second_last_block.symbol} ({ptime(chain.second_last_block.timestamp)}) ${chain.second_last_block.compute_value()} [{subtract_time(last_block.timestamp,chain.second_last_block.timestamp)}] (-2 -- Last)')
        print(f'#{last_block.index} {last_block.symbol} ({ptime(last_block.timestamp)}) ${last_block_value} [{subtract_time(time.time(),last_block.timestamp)}] (Last -- Now)')
        print(f'\n#0 {chain.genesis_block.symbol} -[{subtract_time(BLOCK.timestamp,chain.genesis_block.timestamp)}]- #{BLOCK.index} {BLOCK.symbol} -[{subtract_time(last_block.timestamp,BLOCK.timestamp)}]- #{last_block.index} {last_block.symbol}')

        print('\n== Hash')
        print(f'🦾 {BLOCK.previous_hash}')
        print(f'🥽 {BLOCK.compute_hash()}')
        print(f'\n== {chain.hex_index} \033[5m#{BLOCK.index}\033[0m {BLOCK.symbol} Data')
        print(BLOCK.comment)

        if (args.history):
            print('\n== 30 Day Retrospection')
            historic_chunks = objects_between_timestamps(chain.chain, (BLOCK.timestamp-2628288),BLOCK.timestamp)
            historic = [
                f'#{h.index} {h.symbol} ({ptime(h.timestamp)}) {h.comment}' for h in historic_chunks
            ]
            for h in historic:
                print(h)
        
        if (args.timewarp):
            if (args.mapsize):
                above = a_dec + (args.mapsize)
                below = a_dec - ((args.mapsize)+1)
            else:
                above = a_dec + 8
                below = a_dec - 9
            print(f'\n== Timewarp Map ({ptime(BLOCK.timestamp)})')
            for addr in range(above,below,-1):
                ADDR = Address(hex_index=hex(addr))
                hex_raw = str(hex(addr)).split('x')[-1] # visual address part
                if (str(ADDR.hex_index) == str(a_hex)):
                    print('\033[1;33m\033[5m0x{:0>6}\033[0m\033[1;33m {:<2}#{:0>2} {}\033[0m'.format(hex_raw, BLOCK.symbol, BLOCK.index, BLOCK.comment))
                else:
                    using_chunk_index = 0
                    for chunk in ADDR.chain: # ++
                        if not chunk.timestamp > BLOCK.timestamp:
                            using_chunk_index = chunk.index # sticky to chunk index
                    inspect_chunk = ADDR.chain[using_chunk_index] # the data chunk
                    if (using_chunk_index == 0):
                        print('0x{:0>6} {:<2}#00 \033[1;30m\033[44mGenesis\033[0m'.format(hex_raw, inspect_chunk.symbol))
                    else:
                        print('0x{:0>6} {:<2}#{:0>2} {} [{}]'.format(hex_raw, inspect_chunk.symbol, inspect_chunk.index, inspect_chunk.comment[:32], subtract_time(BLOCK.timestamp,inspect_chunk.timestamp)))

    else:
        msg = f'== {chain.hex_index} last block #{last_block.index} '
        print(msg + '='*(len(last_block_hash)-len(msg)+3))

        # index, symbol, timestamp, value, pristine
        
        print(f'#{last_block.index} {last_block.symbol} ({ptime(last_block.timestamp)}) ${last_block_value} &Pristine: {pristine_status}')
        
        print('\n== Hash')
        print(f'🦾 {last_block.previous_hash}')
        print(f'🥽 {last_block_hash}')
        print('\n== Data')
        print(last_block.comment)
        if (args.data):
            print('\n== Insert Data Block')
            if (args.symbol):
                print(f'{args.symbol}: {args.data}')
                chain.add(args.symbol, args.data)
            else:
                print(f'{last_block.symbol}: {args.data}')
                chain.add(last_block.symbol, args.data)
            print('OK - Write Success.')

        if (args.history):
            print('\n== 30 Day Retrospection')
            historic_chunks = objects_between_timestamps(chain.chain, (last_block.timestamp-2628288),last_block.timestamp)
            historic = [
                f'#{h.index} {h.symbol} ({ptime(h.timestamp)}) {h.comment}' for h in historic_chunks
            ]
            for h in historic:
                print(h)

    if (args.gen):
        msg = f'\n== Genesis Block '
        print(msg)
        GENESIS = chain.genesis_block
        print(f'#0 {GENESIS.symbol} ({ptime(GENESIS.timestamp)}) [{subtract_time(time.time(),GENESIS.timestamp)}] (Genesis -- Now)')
        print(f'🥽 {GENESIS.compute_hash()}')
        print(f'{GENESIS.comment}')

    # map
    if (args.map):
        msg = f'\n== Map '
        print(msg)

        if (args.mapsize):
            above = a_dec + (args.mapsize)
            below = a_dec - ((args.mapsize)+1)
        else:
            above = a_dec + 8
            below = a_dec - 9
        for addr in range(above, below, -1):
            ADDR = Address(hex_index=hex(addr)) # Address
            hex_raw = str(hex(addr)).split('x')[-1] # visual address part
            if (ADDR.last_block.index > 0):
                MapCommentBlock = ADDR.last_block.comment[:32] +f' ({ptime(ADDR.last_block.timestamp)})'
            else:
                MapCommentBlock = '\033[1;30m\033[44mGenesis\033[0m'

            if (str(ADDR.hex_index) == str(a_hex)):
                MapPointerBlock = '\033[1;33m'
                print('\033[5m{}0x{:0>6}\033[0m {:<2}{}#{:0>2} {}\033[0m'.format(MapPointerBlock, hex_raw, ADDR.last_block.symbol, MapPointerBlock, ADDR.last_block.index, ADDR.last_block.comment))
                #print('\033[5m{}0x{:0>6}\033[0m {:<2}{}#{:0>2}\033[0m'.format(MapPointerBlock, hex_raw, ADDR.last_block.symbol, MapPointerBlock, ADDR.last_block.index))
            else:
                print('0x{:0>6} {:<2}#{:0>2} {}'.format(hex_raw, ADDR.last_block.symbol, ADDR.last_block.index, MapCommentBlock))
        
    msg = f'== EOF '
    print(msg + '='*(len(last_block_hash)-len(msg)+3))
