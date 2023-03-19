import json
import os
import time
import re
from hashlib import sha256

if os.name == 'nt':
    main_path = os.path.realpath(__file__).split('\\')
    main_path.remove(main_path[-1])
    main_path = '\\'.join(main_path) + '\\'
else:
    main_path = os.getcwd() + '/'

this_file = os.path.realpath(__file__)

with open(this_file,"r") as monitoring_script:
    this_dump = monitoring_script.read().encode('utf-8')
    this_hash = sha256(this_dump).hexdigest()
this_modified_time = time.ctime(os.path.getmtime(this_file))

main_folder = '{}.monitoring'.format(main_path)
genesis_signature = 'Genesis Block [shadowsword#0179] VERSION {} {}'.format(this_hash, this_modified_time) # or "Genesis"
'''Genesis Block Signature'''

if not os.path.exists(main_folder):
    os.makedirs(main_folder)
os.chdir(main_folder)

def Get():
    '''Return a list of Spaces class files in the cwd.'''
    zones = [Space(zone.replace('.zone','')) for zone in next(os.walk('.'))[2] if re.compile(r'.*.zone$').match(zone)]
    for idx, zone in list(enumerate(zones)):
        print('{}: {} Loaded'.format(idx, zone.space_name))
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

def manual():
    return print('''
        Space(name = str)
        Space.new_block(comment*, importance)
        Space.new_entity(name*, species, comment)
        Space.new_vehicle(plate*, comment, classification, manufacturer)
        Space.pristine (property)
        Space.last_block (property)
        Space.last_entity (property)
        Space.last_vehicle (property)
        Space.read_all()
        Space.read_blocks()
        Space.read_entities()
        Space.read_vehicles()
    ''')

class Space:
    '''# Space
    contains Blocks, Vehicles, Entities. They will have their own chains.
    ---
    They should save and load automatically.
    - `Space(name = "")`
    '''
    def __init__(self, name = "default"):
        self.autosave = True
        self.space_name = name.lower()
        self.space_file = '{}.zone'.format(self.space_name)

        self.chain_blocks_file = '{}_b.json'.format(self.space_name)
        self.chain_entities_file = '{}_e.json'.format(self.space_name)
        self.chain_vehicles_file = '{}_v.json'.format(self.space_name)

        chain_blocks_raw = [row for row in Load(self.chain_blocks_file)]
        chain_entities_raw = [row for row in Load(self.chain_entities_file)]
        chain_vehicles_raw = [row for row in Load(self.chain_vehicles_file)]

        self.chain_blocks = []
        self.chain_entities = []
        self.chain_vehicles = []

        # If any of the chains have data in their files, append them to self chains.
        for data in chain_blocks_raw:
            block = Block(index = data['index'],
                          timestamp = data['timestamp'],
                          previous_hash = data['previous_hash'],
                          comment = data['comment'],
                          importance = data['importance'],
                          nonce = data['nonce'])
            self.chain_blocks.append(block)

        for data in chain_entities_raw:
            entity = Entity(index = data['index'],
                            timestamp = data['timestamp'],
                            previous_hash = data['previous_hash'],
                            name = data['name'],
                            species = data['species'],
                            comment = data['comment'],
                            nonce = data['nonce'])
            self.chain_entities.append(entity)
        
        for data in chain_vehicles_raw:
            vehicle = Vehicle(index = data['index'],
                              timestamp = data['timestamp'],
                              previous_hash = data['previous_hash'],
                              plate = data['plate'],
                              classification = data['classification'],
                              manufacturer = data['manufacturer'],
                              comment = data['comment'],
                              nonce = data['nonce'])
            self.chain_vehicles.append(vehicle)
        
        self.genesis_time = time.time()

        # There must always be a genesis block for each class.
        if len(self.chain_blocks) == 0:
            genesis_block = Block(0, self.genesis_time, "0", genesis_signature, 0)
            self.chain_blocks.append(genesis_block)
        
        if len(self.chain_entities) == 0:
            genesis_block = Entity(0, self.genesis_time, "0", "", "", genesis_signature)
            self.chain_entities.append(genesis_block)
        
        if len(self.chain_vehicles) == 0:
            genesis_block = Vehicle(0, self.genesis_time, "0", "?? ?????", "", "", genesis_signature)
            self.chain_vehicles.append(genesis_block)

    def delete(self):
        for f in [self.space_file, self.chain_blocks_file, self.chain_entities_file, self.chain_vehicles_file]:
            if os.path.exists(f):
                os.remove(f)
        print('Space {} removed.'.format(self.space_name))
        return

    def in_block(self, index = -1):
        block = self.chain_blocks[index].__dict__
        print('{}: Block {}'.format(self.space_name, index))
        for item in block:
            if item == 'timestamp':
                print('{}: {}'.format(item, time.ctime(block[item])))
            else:
                print('{}: {}'.format(str(item), block[item]))
        return
    
    def in_entity(self, index = -1):
        entity = self.chain_entities[index].__dict__
        print('{}: Entity {}'.format(self.space_name, index))
        for item in entity:
            if item == 'timestamp':
                print('{}: {}'.format(item, time.ctime(entity[item])))
            else:
                print('{}: {}'.format(str(item), entity[item]))
        return
    
    def in_vehicle(self, index = -1):
        vehicle = self.chain_vehicles[index].__dict__
        print('{}: Vehicle {}'.format(self.space_name, index))
        for item in vehicle:
            if item == 'timestamp':
                print('{}: {}'.format(item, time.ctime(vehicle[item])))
            else:
                print('{}: {}'.format(str(item), vehicle[item]))
        return
    
    def read_blocks(self):
        for chain in self.chain_blocks:
            h = hex(chain.index).split('x')[-1]
            if chain.index != 0:
                print('[0x{:0>4}]:{}: "{}"'.format(h, chain.importance, chain.comment))

    def read_entities(self):
        # TODO: Add a dict here and only print the most recent one in the dict.
        for chain in self.chain_entities:
            h = hex(chain.index).split('x')[-1]
            if chain.index != 0:
                print('[0x{:0>4}]: {} ({}) "{}"'.format(h, chain.name, chain.species, chain.comment))

    def read_vehicles(self):
        for chain in self.chain_vehicles:
            h = hex(chain.index).split('x')[-1]
            if chain.index != 0:
                print('[0x{:0>4}]: [{}] {} {} "{}"'.format(h, chain.plate, chain.manufacturer, chain.classification, chain.comment))

    def read_all(self):
        print(self.space_name)
        self.read_blocks()
        self.read_entities()
        self.read_vehicles()
        return
    
    @property
    def modified(self):
        files = [f for f in [self.space_file, self.chain_blocks_file, self.chain_entities_file, self.chain_vehicles_file] if os.path.exists(f)]
        if len(files) > 0:
            last_modified = time.ctime(os.path.getmtime(max(files, key=os.path.getmtime)))
        else:
            last_modified = 'Space has no file.'
        return last_modified

    @property
    def pristine(self):
        '''Return True if hashes are consistent'''
        verified = True
        for chain in [self.chain_blocks, self.chain_entities, self.chain_vehicles]:
            for index in reversed(range(len(chain))):
                if index > 0:
                    if chain[index-1].compute_hash() != chain[index].previous_hash:
                        verified = False
        return verified
    
    @property
    def pristine_genesis(self):
        verified = True
        for chain in [self.chain_blocks, self.chain_entities, self.chain_vehicles]:
            genesis_block = chain[0]
            if (genesis_block.comment != genesis_signature):
                verified = False
        return verified

    @property
    def last_block(self):
        return self.chain_blocks[-1]
    
    @property
    def last_entity(self):
        return self.chain_entities[-1]
    
    @property
    def last_vehicle(self):
        return self.chain_vehicles[-1]
    
    def proof_of_work(self, block):
        '''Returns hash, within acceptable difficulty by raising nonce.
        ---
        This works for blocks, entities, and vehicles.'''
        block.nonce = 0
        computed_hash = block.compute_hash()
        
        while not computed_hash.startswith('0' * Space.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash
    
    def new_block(self, comment, importance = 0):
        '''`new_block(comment, importance = 0)`'''
        last_block = self.last_block

        new_block = Block(index = last_block.index+1,
                          timestamp = time.time(),
                          previous_hash = last_block.compute_hash(),
                          comment = str(comment),
                          importance = int(importance))
        # Run Hash Nonce until Proof of Work Satisfied
        proof = self.proof_of_work(new_block)

        # Ensure the new block's hash has been registered
        if (new_block.compute_hash() == proof):
            self.chain_blocks.append(new_block)

        if self.autosave:
            self.save()
        return new_block.index
    
    def new_entity(self, name, species = "", comment = ""):
        '''name*, species, comment'''
        last_entity = self.last_entity

        new_entity = Entity(index = last_entity.index+1,
                            timestamp = time.time(),
                            previous_hash = last_entity.compute_hash(),
                            name = str(name),
                            species = str(species),
                            comment=str(comment))
        proof = self.proof_of_work(new_entity)
        
        if (new_entity.compute_hash() == proof):
            self.chain_entities.append(new_entity)

        if self.autosave:
            self.save()
        return new_entity.index

    def new_vehicle(self, plate, comment = "", classification = "Vehicle", manufacturer = ""):
        '''plate*, comment, classification, manufacturer'''
        last_vehicle = self.last_vehicle

        new_vehicle = Vehicle(index = last_vehicle.index+1,
                              timestamp = time.time(),
                              previous_hash = last_vehicle.compute_hash(),
                              plate = plate,
                              classification = classification,
                              manufacturer = manufacturer,
                              comment = comment)
        proof = self.proof_of_work(new_vehicle)
        
        if (new_vehicle.compute_hash() == proof):
            self.chain_vehicles.append(new_vehicle)
        
        if self.autosave:
            self.save()
        return new_vehicle.index

    def save(self):
        if not os.path.exists(self.space_file):
            with open(self.space_file, 'w') as write_file:
                write_file.write(genesis_signature)
            write_file.close()

        with open(self.chain_blocks_file, 'w') as write_file:
            for block in self.chain_blocks:
                write_file.write(json.dumps(block.__dict__) + '\n')
        write_file.close()
        
        with open(self.chain_entities_file, 'w') as write_file:
            for entity in self.chain_entities:
                write_file.write(json.dumps(entity.__dict__) + '\n')
        write_file.close()

        with open(self.chain_vehicles_file, 'w') as write_file:
            for vehicle in self.chain_vehicles:
                write_file.write(json.dumps(vehicle.__dict__) + '\n')
        write_file.close()
        print('Save Successful ({})'.format(self.space_name))

    # '0' * difficulty in the SHA256 hash (Proof-of-Work)
    difficulty = 2

class Block:
    '''# BLock
    - index (int)
    - timestamp (float)
    - previous_hash (str)
    - comment (str)
    - importance (int)
    - nonce (int)
    ---
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

class Vehicle:
    '''# Vehicle
    - index (int)
    - timestamp (float)
    - previous_hash (str)
    - plate (str) || like "BC 99999"
    - classification (str) || like SUV, Truck, Car
    - manufacturer (str) || like Toyota, Dodge,..
    - comment (str)
    - nonce (int)'''
    def __init__(self, index, timestamp, previous_hash, 
                 plate = "?? ?????", classification = "Vehicle", manufacturer = "Unknown", comment = "",
                 nonce = 0):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.plate = plate
        self.classification = classification
        self.manufacturer = manufacturer
        self.comment = comment
        self.nonce = nonce

    def compute_hash(self):
        '''Compute the SHA256 hash of this class as a sum of the class data structure.'''
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Entity:
    '''# Entity
    - index
    - timestamp
    - previous_hash
    - name
    - species (str) || like Fae, Human, Cat, Dog
    - comment
    - nonce
    '''
    def __init__(self, index, timestamp, previous_hash,
                 name = "", species = "Entity", comment = "",
                 nonce = 0):
        self.index = index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.name = name.upper()
        self.species = species.upper()
        self.comment = comment
        self.nonce = nonce

    def compute_hash(self):
        '''Compute the SHA256 hash of this class as a sum of the class data structure.'''
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

z = Get()
print('Loaded',this_hash)