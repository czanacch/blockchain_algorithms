import random
import time
import queue
import hashlib
from threading import *
from treelib import Node, Tree
from datetime import timedelta
import threading

lock = Lock()

# Canale per il consenso dell'insieme maggiore
consensus_channel = {
    1 : queue.Queue(),
    2 : queue.Queue(),
    3 : queue.Queue(),
    4 : queue.Queue(),
    5 : queue.Queue(),
    6 : queue.Queue()
}


# Canale per la raccolta di proposte dei proposers
proposers_proposals = {
    1 : queue.Queue(),
    2 : queue.Queue(),
    3 : queue.Queue(),
    4 : queue.Queue(),
    5 : queue.Queue(),
    6 : queue.Queue()
}

# Canale per la raccolta di ACK dei proposers
proposers_ack = {
    1 : queue.Queue(),
    2 : queue.Queue(),
    3 : queue.Queue(),
    4 : queue.Queue(),
    5 : queue.Queue(),
    6 : queue.Queue()
}

# Canale per la raccolta di NACK dei proposers
proposers_nack = {
    1 : queue.Queue(),
    2 : queue.Queue(),
    3 : queue.Queue(),
    4 : queue.Queue(),
    5 : queue.Queue(),
    6 : queue.Queue()
}


class Proposal:
    def __init__(self, proposedValue, proposalNumber, UID):
        self.proposedValue = proposedValue
        self.proposalNumber = proposalNumber
        self.UID = UID

class ACK:
    def __init__(self, proposedValue, proposalNumber, proposerId):
        self.proposedValue = proposedValue
        self. proposalNumber = proposalNumber
        self.proposerId = proposerId

class NACK:
    def __init__(self, proposedValue, proposalNumber, proposerId):
        self.proposedValue = proposedValue
        self. proposalNumber = proposalNumber
        self.proposerId = proposerId


class Proposer(Thread):
    def __init__(self, UID, initialValue):
        super(Proposer, self).__init__()

        self.UID = UID # numero identificativo univoco di un processo
        self.status = 'passive'
        self.ackCount = 0
        self.nackCount = 0
        self.proposalNumber = 0

        self.initialValue = initialValue # Valore iniziale proposto (insieme di transazioni)
        self.proposedValue = set() # Insieme vuoto
        self.outputValue = set() # Insieme vuoto

        self.acceptedValue = set() # Gioca il ruolo di Acceptor condiviso

        self.consensus_set = set() # Insieme finale che sarà condiviso da tutti
    
    
    
    
    '''
    Funzione aggiuntiva che serve a concordare il set più grande (cardinalità maggiore)
    Funziona soltanto DOPO il Lattice Agreement
    
    def Consensus(self):
        while True:
            transaction_set = consensus_channel[self.UID].get() # è arrivato un insieme. Un processo ha 'finito'
            if len(transaction_set) > len(self.consensus_set):
                self.consensus_set = transaction_set
            time.sleep(0.01)
    '''

    '''
    Si attiva ogni volta che arriva un messaggio Proposal
    (simula l'Acceptor della 'versione standard')
    '''

    def ReceiveValue(self):
        while True:
            proposal = proposers_proposals[self.UID].get() # Attende sulla sua coda di proposte
            if self.acceptedValue.issubset(proposal.proposedValue):
                with lock:
                    self.acceptedValue = proposal.proposedValue
                    my_ack = ACK(proposal.proposedValue, proposal.proposalNumber, proposal.UID)
                    proposers_ack[proposal.UID].put(my_ack)
            else:
                with lock:
                    self.acceptedValue = self.acceptedValue.union(proposal.proposedValue)
                    my_nack = NACK(self.acceptedValue, proposal.proposalNumber, proposal.UID)
                    proposers_nack[proposal.UID].put(my_nack)
            time.sleep(0.01)




    '''
    (1) - Evento PROPOSAL
    '''
    def Propose(self):
        while True:
            if self.proposalNumber == 0:
                with lock:
                    self.proposedValue = self.initialValue # il valore proposto diventa il valore iniziale
                    
                    self.status = 'active'

                    if 
                    self.proposalNumber = self.proposalNumber + 1 # incrementa il numero di proposte attive
                    
                    
                    self.ackCount = 0
                    self.nackCount = 0
                    my_proposal = Proposal(self.proposedValue, self.proposalNumber , self.UID)
                    for k in proposers_proposals:
                        proposers_proposals[k].put(my_proposal)
            time.sleep(0.01)


    def ProcessACK(self):
        while True:
            ack = proposers_ack[self.UID].get() # è arrivato un ack
            if ack.proposalNumber == self.proposalNumber:
                with lock:
                    self.ackCount = self.ackCount + 1
            time.sleep(0.01)

    def ProcessNACK(self):
        while True:
            nack = proposers_nack[self.UID].get() # è arrivato un ack
            if nack.proposalNumber == self.proposalNumber:
                with lock:
                    self.proposedValue = self.proposedValue.union(nack.proposedValue)
                    self.nackCount = self.nackCount + 1
            time.sleep(0.01)

    def Refine(self):
        while True:
            if self.nackCount > 0 and (self.nackCount + self.ackCount) >= 1:
                with lock:
                    self.proposalNumber = self.proposalNumber + 1
                    self.ackCount = 0
                    self.nackCount = 0
                    my_proposal = Proposal(self.proposedValue, self.proposalNumber , self.UID)
                    for k in proposers_proposals:
                        proposers_proposals[k].put(my_proposal)
            time.sleep(0.01)

    def Decide(self):
        while True:
            if self.ackCount >= 1 and self.status == 'active':
                with lock:
                    self.outputValue = self.proposedValue
                    self.status = 'passive'

                    # Trasmissione per ottenere il consenso
                    for k in consensus_channel:
                        consensus_channel[k].put(self.outputValue)
            time.sleep(0.01)

    def printSet(self):
        while True:
            with lock:
                print(self.UID)
                print('ha come insieme: ')
                print(self.outputValue)
            time.sleep(1)

        
    def run(self):
        propose = Thread(target = self.Propose)
        propose.start()

        processACK = Thread(target = self.ProcessACK)
        processACK.start()

        processNACK = Thread(target = self.ProcessNACK)
        processNACK.start()

        refine = Thread(target = self.Refine)
        refine.start()

        decide = Thread(target = self.Decide)
        decide.start()

        receiveValue = Thread(target = self.ReceiveValue)
        receiveValue.start()

        #consensus = Thread(target = self.Consensus)
        #consensus.start()

        printSet = Thread(target = self.printSet)
        printSet.start()

    

# -------------------------------------------------------------------------------------------              

def main():

    proposer_1 = Proposer(1, {'b1'})
    
    proposer_2 = Proposer(2, {'b2'})

    proposer_3 = Proposer(3, {'b3'})

    proposer_4 = Proposer(4, {'b4'})

    proposer_5 = Proposer(5, {'b5'})

    proposer_6 = Proposer(6, {'b6'})

    proposer_6.start()

    time.sleep(0.5)

    proposer_2.start()

    time.sleep(0.5)
    
    proposer_3.start()

    time.sleep(0.5)

    proposer_4.start()

    time.sleep(0.5)
    
    proposer_5.start()

    time.sleep(0.5)
    
    proposer_1.start()
    



    




if __name__ == '__main__':
    main();