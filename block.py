from utils.printable import Printable
from time import time


class Block(Printable):
    def __init__(self, index, prev_hash, transactions, proof, timestamp=None) -> None:
        self.index = index
        self.prev_hash = prev_hash
        self.transactions = transactions
        self.proof = proof
        self.timestamp = time() if timestamp is None else timestamp
