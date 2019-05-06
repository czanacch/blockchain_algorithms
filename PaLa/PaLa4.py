import random
import time
import queue
import hashlib
from threading import *
from treelib import Node, Tree
from datetime import timedelta
import threading

lock = Lock() # Global LOCK (use to mutual exclusion)

n = 3 # Network cardinality (number of processes in the network)

growth_speed = 0.1 # regulates the growth rate of process blockchains

global_Δ = 2 # global time parameter Δ 

# BROADCAST COMMUNICATION ABSTRACTION

# Channel of PROPOSAL messages
broadcast_proposal = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

# Channel of VOTE messages
broadcast_vote = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

# Channel of CLOCK messages
broadcast_clock = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

# Given an epoch e, it randomly returns the proponent of this epoch (deterministically)
def proposer(e):
    random.seed(e)
    return str(random.randint(1, n)) # It's possible to change this implementation of random selection

# Returns an hash of a single Process identifier together with a Block object
def sign_block(process, block):
    signature = (process.identifier, block)
    return hash(signature)

# Returns an hash of a single Process identifier together with a Clock object
def sign_clock(process, clock):
    signature = (process.identifier, clock)
    return hash(signature)

def vrfy_block(process, block, signature):
    if sign_block(process,block) == signature:
        return True
    else:
        return False

# Class representing a single block
class Block:
    def __init__(self, epoch, TXs, hash=0):
        self.epoch = epoch # Block's local epoch
        self.TXs = TXs # Transactions
        self.hash = hash # Previous block hash (recursive reference to the chain)

# Class representing an entire tree of blocks
class BlockChain:
    def __init__(self):
        self.root = Tree()
        self.root.create_node(0, 0) # Genesis block
        
    # Adds a block to a blockchain
    def add_block(self, block):
        node = self.root.create_node(block.epoch, hash(block), block.hash)
        node.data = block

    # Print the blockchain graphically
    def print_chain(self):
        self.root.show()

    # Returns the list containing all the blocks of the entire blockchain
    def return_nodes_data(self):
        nodes = self.root.all_nodes()
        nodes_data = []
        for i in range(1,len(nodes)):
            nodes_data.append(nodes[i].data)
        if len(nodes_data) == 0:
            nodes_data.append(0)
        return nodes_data

    # Returns the list of identifiers of the leaves of the tree (blockchain)
    def leaves(self):
        leaves = self.root.leaves(nid=None)
        leaves_identifiers = []
        for i in range(len(leaves)):
            leaves_identifiers.append(leaves[i].identifier)
        return leaves_identifiers   

    # returns the Block object with the major epoch in the blockchain
    def block_max_epoch(self): 
        nodes = self.root.all_nodes()
        max_epoch = 0
        block_max = 0
        for i in range(len(nodes)):
            if nodes[i].tag > max_epoch:
                max_epoch = nodes[i].tag
                block_max = nodes[i].data
        return block_max

# Proposal message object
class Proposal:
    def __init__(self, sender, block, signature):
        self.sender = sender
        self.block = block
        self.signature = signature

# Vote message object
class Vote:
    def __init__(self, sender, block, signature):
        self.sender = sender
        self.block = block
        self.signature = signature

# Clock message object
class Clock:
    def __init__(self, sender, epoch, signature):
        self.sender = sender
        self.epoch = epoch
        self.signature = signature


# Class representing a single process
class Process(Thread):
    def __init__(self, identifier):
        super(Process, self).__init__()

        self.B = BlockChain() # Process blockchain, initialized to Genesis Block
        self.e = 1 # Number of local epoch
        self.has_voted = [False for i in range(200)]
        self.prop_rec = ['⊥' for i in range(200)]
        self.fchain = ['⊥' for i in range(200)] # Output: current finalized chain
        
        self.identifier = identifier
        self.TX = 'Transactions pool' # It simulates an entire transaction pool of a process

        self.Δ = global_Δ # Local time clock for epoch change
        self.votes = {} # Vote counter for each block
        self.clocks = {} # Clock counter for each epoch

    
    # Time passing simulator: every second the local Δ is decreased by 1
    def countdown(self):
        while self.Δ > 0:
            self.Δ = self.Δ - 1
            time.sleep(1)

    # Update the number of votes for each Block object that arrives
    def counter_votes(self):
        while True:
            vote = broadcast_vote[self.identifier].get() # It waits on the queue
            if vote.block not in self.votes:
                self.votes[vote.block] = 1
            else:
                self.votes[vote.block] = self.votes[vote.block] + 1 # aumenta il contatore di voti relativo a un blocco
            
            # TODO: FLOODING
            
            time.sleep(growth_speed)
    

    # Update the number of clocks for each Epoch object that arrives
    def counter_clocks(self):
        while True:
            clock = broadcast_clock[self.identifier].get() # It waits on the queue
            if clock.epoch not in self.clocks:
                self.clocks[clock.epoch] = 1
            else:
                self.clocks[clock.epoch] = self.clocks[clock.epoch] + 1

            # TODO: FLOODING
        
            time.sleep(growth_speed)
    
        
    '''
    EVENT 1: trigger when the value of 'e' changes
    '''
    def New_epoch_start(self):
        e_prec = 0
        while True:
            if self.identifier == proposer(self.e) and e_prec != self.e: # se io sono il proponente dell'epoca
                
                e_prec = self.e # to not repeat the function twice
                
                lb = self.B.block_max_epoch() # lb is the "last block"

                b = Block(self.e, self.TX, hash(lb)) # creation of a new block b

                my_proposal = Proposal(self, b, sign_block(self, b)) # create the Proposal object
                
                # Proposal object broadcast
                for k in broadcast_proposal:
                    # time.sleep(random.uniform(0.0, 3.0)) # It simulates different speeds in the network
                    broadcast_proposal[k].put(my_proposal)

            time.sleep(growth_speed)
            
            
    '''
    EVENT 2: acceptance of a Block proposal (first and only time!)
    '''
    def New_proposal(self):
        
        while True:
            proposal = broadcast_proposal[self.identifier].get() # It waits on the queue

            if vrfy_block(proposal.sender, proposal.block, proposal.signature) and proposal.sender.identifier == proposer(proposal.block.epoch) and self.prop_rec[proposal.block.epoch] == '⊥' :
                self.prop_rec[proposal.block.epoch] = proposal.block

            time.sleep(growth_speed)
    

    '''
    EVENT 3: counter of votes for blockchain update and change of epoch
    '''
    def Update_blockchain(self):
        while True:
            for b in self.votes:
                if self.votes[b] >= 2*n/3:
                    
                    # TODO: aggiungere un meccanismo per controllare le firme
                    
                    self.B.add_block(b)
                    self.votes[b] = -1
                    
                    self.finalize()
                    
                    self.e = max(self.e , b.epoch + 1) # update epoch
                    self.Δ = global_Δ # update Δ for waiting for the next age

            time.sleep(growth_speed)

    '''
    EVENT 4: broadcast of the clock message for possible epoch update
    '''
    def Clock_broadcast(self):
        while True:
            if self.Δ == 0:
                print('cloook')
                my_clock = Clock(self, self.e, sign_clock(self,self.e)) # Clock message object
                for k in broadcast_clock:
                    # time.sleep(random.uniform(0.0, 3.0)) # It simulates different speeds in the network
                    broadcast_clock[k].put(my_clock)
                self.Δ = -1 # To prevent it from continuing to send messages
            time.sleep(growth_speed)

                
    '''
    EVENT 5: clock counter for possible epoch update
    '''
    def Change_epoch(self):
        while True:
            for e in self.clocks:
                if self.clocks[e] >= 2*n/3:
                    # TODO: aggiungere un meccanismo per controllare le firme
                    self.e = max(self.e, e + 1) # Update current epoch
                    self.Δ = global_Δ # update Δ for waiting for the next age

            time.sleep(growth_speed)


    '''
    EVENT 6: Vote event
    '''
    def Vote(self):

        while True:
            b_parent = None

            for block in self.B.return_nodes_data():
                if self.prop_rec[self.e] != '⊥' and hash(block) == self.prop_rec[self.e].hash:
                    if self.B.block_max_epoch() == block:
                        b_parent = block
                        break

            if self.prop_rec[self.e] != '⊥' and self.has_voted[self.e] == False and b_parent != None:
                b = self.prop_rec[self.e]
                my_vote = Vote(self, b, sign_block(self,b))
                for k in broadcast_vote:
                    time.sleep(random.uniform(0.0, 7.0)) # It simulates different speeds in the network
                    broadcast_vote[k].put(my_vote)
                self.has_voted[self.e] = True

            time.sleep(growth_speed)

    # Updates the finalized chain
    def finalize(self):

        '''
        N = set() # N is the set of "normal blocks"
        for b in self.B.return_nodes_data(): # b is a block
            for b_1 in self.B.return_nodes_data(): # b_1 is a block
                if b.epoch + 1 == b_1.epoch and hash(b) == b_1.hash:
                    N.add(b)

        max_epoch = 0
        lnb = None # Last 'normal block'
        for b in N:
                if b.epoch >= max_epoch:
                    max_epoch = b.epoch
                    lnb = b



        self.fchain[max_epoch] = lnb

        '''


    def print_demonstration(self):
        while True:
            with lock:
                           
                print('.............')
                print('blockchain of ' + self.identifier + ' (epoch ' + str(self.e) + '):')
                if proposer(self.e) == self.identifier:
                    print('PROPOSER')
                self.B.print_chain()
                print('.............')  
                
            time.sleep(1)

                
    
    
    def run(self):

        # Sotto-thread (contatori e altro)
        p1 = Thread(target = self.countdown)
        p2 = Thread(target = self.counter_votes)
        p3 = Thread(target = self.counter_clocks)

        # Sotto-thread (EVENTI)
        e1 = Thread(target = self.New_epoch_start)
        e2 = Thread(target = self.New_proposal)
        e3 = Thread(target = self.Update_blockchain)
        e4 = Thread(target = self.Clock_broadcast)
        e5 = Thread(target = self.Change_epoch)
        e6 = Thread(target = self.Vote)

        p1.start()
        p2.start()
        p3.start()
        e1.start()
        e2.start()
        e3.start()
        e4.start()
        e5.start()
        e6.start()

        print_demonstration = Thread(target = self.print_demonstration)
        print_demonstration.start()



def main():

    process_1 = Process("1")
    process_1.start()

    process_2 = Process("2")
    process_2.start()

    process_3 = Process("3")
    process_3.start()

if __name__ == '__main__':
    main();