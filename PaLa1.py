import random
import time
import queue
import hashlib
from threading import *
from treelib import Node, Tree
from datetime import timedelta
import threading

lock = Lock()

n = 3 # numero di processi nella rete (cardinalità della rete)

broadcast_proposal = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

broadcast_vote = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

broadcast_clock = {
		"1" : queue.Queue(),
        "2" : queue.Queue(),
        "3" : queue.Queue()
}

# Funzione che restituisce il proponente per l'epoca, data una certa epoca
def proposer(e):
    return "1"
    #return random.randint(1, n) # It's possible to change this implementation of selection

# restituisce un hash di un oggetto processo fuso con un oggetto blocco
def sign_block(process, block):
    signature = (process.identifier, block)
    return hash(signature)

# restituisce un hash di un oggetto processo fuso con un oggetto clock
def sign_clock(process, clock):
    signature = (process.identifier, clock)
    return hash(signature)

def vrfy_block(process, block, signature):
    if sign_block(process,block) == signature:
        return True
    else:
        return False


# Un blocco ha un solo identificativo
class Block:
    def __init__(self, epoch, TXs, hash=0):
        self.epoch = epoch # Identificativo numerico dell'epoca del blocco
        self.TXs = TXs # Transazioni del blocco
        self.hash = hash # hash del blocco precedente (riferimento ricorsivo alla catena)

# Classe che rappresenta un "albero" di blocchi
class Chain:
    def __init__(self):
        self.root = Tree()
        self.root.create_node(0, 0) # Genesis block
        

    # Aggiunge un blocco ad una catena
    def add_block(self, block):
        node = self.root.create_node(block.epoch, hash(block), block.hash)
        node.data = block

    # Stampa graficamente la catena in forma di albero
    def print_chain(self):
        self.root.show()

    # restituisce i blocchi di tutta la blockchain, sottoforma di lista
    def return_nodes_data(self):
        nodes = self.root.all_nodes()
        nodes_data = []
        for i in range(1,len(nodes)):
            nodes_data.append(nodes[i].data)
        if len(nodes_data) == 0:
            nodes_data.append(0)
        return nodes_data

    # Resituisce la lista degli identificativi (numeri) delle foglie dell'albero (catena)
    def leaves(self):
        leaves = self.root.leaves(nid=None)
        leaves_identifiers = []
        for i in range(len(leaves)):
            leaves_identifiers.append(leaves[i].identifier)
        return leaves_identifiers   

    # ritorna tutte le epoche associate ai nodi della blockchain
    '''
    def return_nodes(self):
        nodes = self.root.all_nodes()
        nodes_identifiers = []
        for i in range(len(nodes)):
            nodes_identifiers.append(nodes[i].tag)
        return nodes_identifiers
    '''

    # restituisce il blocco (oggetto) con l'epoca maggiore nella Chain
    def block_max_epoch(self): 
        nodes = self.root.all_nodes()
        max_epoch = 0
        block_max = 0
        for i in range(len(nodes)):
            if nodes[i].tag > max_epoch:
                max_epoch = nodes[i].tag
                block_max = nodes[i].data
        return block_max

# -------------------------------------------------------------------------------------

# Proposal rappresenta la proposta del blocco vera e propria
class Proposal:
    def __init__(self, sender, block, signature):
        self.sender = sender # mittente della proposta (identificativo)
        self.block = block # blocco proposto
        self.signature = signature # firma associata al blocco

# Vote rappresenta un singolo voto inviato da un certo processo
class Vote:
    def __init__(self, sender, block, signature):
        self.sender = sender # mittente del voto (identificativo)
        self.block = block # blocco proposto
        self.signature = signature # firma associata al blocco

# Clock rappresenta una volontà di avanzare dall'epoca e (mandata nel clock) all'epoca e + 1
class Clock:
    def __init__(self, sender, epoch, signature):
        self.sender = sender # mittente del clock (identificativo)
        self.epoch = epoch # epoca
        self.signature = signature # firma associata all'epoca













class Processo(Thread):
    def __init__(self, identifier):
        super(Processo, self).__init__()

        self.B = Chain() # Blockchain del singolo processo, inizializzata al Genesis Block
        self.e = 1 # Numero di epoca associato a un processo
        self.has_voted = [False for i in range(200)] # gli indici sono le epoche e i valori corrispondenti indicano se si è votato oppure no per quell'epoca
        self.prop_rec = ['⊥' for i in range(200)] # gli indici sono le epoche e i valori corrispondenti sono proprio dei blocchi ricevuti in quell'epoca
        #self.fchain = ['⊥' for i in range(50)] # Output: ovvero la catena corrente del nodo finalizzata
        
        self.identifier = identifier # stringa identificativa di un processo
        self.TX = 'transactions pool' # simula un intero pool di transazioni di un processo

        #self.delta = 30 # orologio temporale per cambio di epoca
        self.votes = {} # contatore di voti per ogni blocco
        #self.clocks = {} # contatore di clock per ogni epoca

    '''
    Decrementa l'orologio 'delta'
    
    def countdown(self):
        while self.delta > 0:
            self.delta = self.delta - 1
            time.sleep(1)
    '''

    '''
    Campiona il numero dei voti per ogni blocco che arriva
    '''
    def counter_votes(self):
        while True:
            vote = broadcast_vote[self.identifier].get() # attende sulla sua coda. vote sarà un oggetto di tipo voto
            if vote.block not in self.votes:
                self.votes[vote.block] = 1
            else:
                self.votes[vote.block] = self.votes[vote.block] + 1 # aumenta il contatore di voti relativo a un blocco
            time.sleep(1)
    
    '''
    Campiona il numero dei clock per ogni epoca che arriva
    
    def counter_clocks(self):
        while True:
            clock = broadcast_clock[self.e].get()
            if clock.epoch not in self.clocks:
                self.clocks[clock.epoch] = 1
            else:
                self.clocks[clock.epoch] = self.clocks[clock.epoch] + 1
            time.sleep(0.1)
    '''
        
    '''
    EVENTO 1: scatta quando il valore di 'e' cambia
    '''
    def new_epoch_start(self):
        e_prec = 0
        while True:
            if self.identifier == proposer(self.e) and e_prec != self.e: # se io sono il proponente dell'epoca
                e_prec = self.e
                
                lb = self.B.block_max_epoch() # lb is the "last block"

                
                b = Block(self.e, self.TX, hash(lb)) # creation of a new block b


                my_proposal = Proposal(self, b, sign_block(self, b)) # create the Proposal object
                for k in broadcast_proposal:
                    broadcast_proposal[k].put(my_proposal)

                

                

            time.sleep(1)
            
            
    '''
    EVENTO 2: accettazione di una PROPOSTA DI BLOCCO (prima e unica volta!)
    '''
    def new_proposal(self):
        
        while True:
            proposal = broadcast_proposal[self.identifier].get() # attende sulla sua coda di proposte


            if vrfy_block(proposal.sender, proposal.block, proposal.signature) and proposal.sender.identifier == proposer(proposal.block.epoch) and self.prop_rec[proposal.block.epoch] == '⊥' :
                self.prop_rec[proposal.block.epoch] = proposal.block

            time.sleep(1)
    

    '''
    EVENTO 3: contatore di voti per AGGIORNAMENTO BLOCKCHAIN e CAMBIO DI EPOCA
    '''
    def update_blockchain(self):
        while True:
            for b in self.votes:
                if self.votes[b] >= 2*n/3:
                    # TODO: aggiungere un meccanismo per controllare le firme
                    self.B.add_block(b)
                    self.votes[b] = -1
                    #finalize()
                    self.e = max(self.e , b.epoch + 1) # aggiorna l'epoca
                    #self.delta = 30 # aggiorna delta per l'attesa della prossima epoca

            time.sleep(1)
    

    '''
    EVENTO 4: divulgazione del clock per EVENTUALE CAMBIO DI EPOCA
    
    def clock_broadcast(self):
        while True:
            if self.delta == 0:
                my_clock = Clock(self.e, signc(self, self.e))
                for k in array_clock:
                    array_clock[k].put(my_clock)
                self.delta = -1 # In questo modo non manda più nessun messaggio
            time.sleep(0.1)
    '''
                
    '''
    EVENTO 5: contatore di clock per un EVENTUALE CAMBIO DI EPOCA
    
    def change_epoch(self):
        while True:
            for e in self.clocks:
                if self.clocks[e] >= 2*n/3:
                    # TODO: aggiungere un meccanismo per controllare le firme

                    self.e = max(self.e , e + 1) # Aggiorna l'epoca corrente

                    self.delta = 30 # aggiorna delta per l'attesa della prossima epoca

            time.sleep(0.1)
    '''


    '''
    EVENTO 6: VOTO
    '''
    def vote(self):

        while True:
            b_parent = None



            for block in self.B.return_nodes_data():
                if self.prop_rec[self.e] != '⊥' and hash(block) == self.prop_rec[self.e].hash:
                    b_parent = block
                    break
                
            
            if self.prop_rec[self.e] != '⊥' and self.has_voted[self.e] == False and b_parent != None:
                b = self.prop_rec[self.e]            
                # Broadcast
                my_vote = Vote(self, b, sign_block(self,b))
                for k in broadcast_vote:
                    broadcast_vote[k].put(my_vote)
                self.has_voted[self.e] = True

            time.sleep(1)

    def stampa_prova(self):
        while True:
            with lock:
                print('.............')
                print('blockchain of ' + self.identifier + ':')
                self.B.print_chain()
                print('.............')

            time.sleep(3)

                
    
    
    def run(self):

        # Sotto-thread (contatori e altro)
        #p1 = Thread(target = self.countdown)
        p2 = Thread(target = self.counter_votes)
        #p3 = Thread(target = self.counter_clocks)

        # Sotto-thread (EVENTI)
        
        e1 = Thread(target = self.new_epoch_start)

        e2 = Thread(target = self.new_proposal)
        e3 = Thread(target = self.update_blockchain)
        #e4 = Thread(target = self.clock_broadcast)
        #e5 = Thread(target = self.change_epoch)
        e6 = Thread(target = self.vote)


        #p1.start()
        p2.start()
        #p3.start()
        e1.start()
        e2.start()
        e3.start()
        #e4.start()
        #e5.start()
        e6.start()

        stampa_prova = Thread(target = self.stampa_prova)
        stampa_prova.start()
        




def main():

    processo_1 = Processo("1")
    processo_1.start()

    processo_2 = Processo("2")
    processo_2.start()

    processo_3 = Processo("3")
    processo_3.start()   
    


    


if __name__ == '__main__':
    main();