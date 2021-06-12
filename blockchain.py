import functools
import json
import requests

from block import Block
from utils import hash_util
from utils.verification import Verification
from transaction import Transaction
from wallet import Wallet

MINING_REWARD = 10


class BlockChain:
    def __init__(self, public_key, node_id):
        genesis_block = Block(0, '', [], 100, 0)
        self.__chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        self.load_data()

    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_transactions(self):
        return self.__open_transactions[:]

    def load_data(self):
        try:
            # with open('blockchain.p', mode='rb') as f:
            #     file_content = pickle.loads(f.read())
            #     global blockchain
            #     global open_transactions
            #     blockchain = file_content['chain']
            #     open_transactions =file_content['ot']

            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(tx['sender'],
                                                tx['recipient'],
                                                tx['signature'],
                                                tx['amount'])
                                    for tx in block['transactions']]
                    updated_block = Block(block['index'],
                                          block['prev_hash'],
                                          converted_tx,
                                          block['proof'],
                                          block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['sender'],
                                                      tx['recipient'],
                                                      tx['signature'],
                                                      tx['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            print('An error occurred while loading data')
        finally:
            print('Cleanup!')

    def save_data(self):
        try:
            # with open('blockchain.p', mode='wb') as f:
            # save_data = {
            #     'chain': blockchain,
            #     'ot': open_transactions
            # }
            # f.write(pickle.dumps(blockchain))

            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                saveable_chain = [block.__dict__ for block in
                                  [Block(block_el.index,
                                         block_el.prev_hash,
                                         [tx.__dict__
                                          for tx in block_el.transactions],
                                         block_el.proof, block_el.timestamp)
                                   for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_util.hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions,
                                           last_hash,
                                           proof):
            proof += 1
        return proof

    def get_balance(self, sender=None):
        if sender is None:
            if self.public_key is None:
                return None
            participant = self.public_key
        else:
            participant = self.public_key
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount
                          for tx in self.__open_transactions
                          if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = functools.reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                    if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

        tx_recipient = [[tx.amount for tx in block.transactions
                        if tx.recipient == participant]
                        for block in self.__chain]
        amount_received = functools.reduce(
            lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                    if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)
        return amount_received - amount_sent

    def get_last_blockchain_value(self):
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """Verifies and adds a transaction to open transactions list

        Args:
            recipient (string): The recipient in the transaction
            sender (string): The sender in the transaction
            amount (float, optional): The amount to be transferred.
            Defaults to 1.0.

        Returns:
            bool: True if the transaction is successfully added.
                  False otherwise.
        """
        # transaction = {
        #     'sender': sender,
        #     'recipient': recipient,
        #     'amount': amount
        # }
        # if self.public_key == None:
        #     return False
        transaction = Transaction(sender, recipient, signature, amount)
        is_verified = Verification.verify_transaction(
            transaction, self.get_balance, False)
        if is_verified:
            self.__open_transactions.append(transaction)
            print('****Open Transactions: ', len(self.__open_transactions))
            self.save_data()
            if not is_receiving:
                for node in self.__peer_nodes:
                    try:
                        url = 'http://{}/broadcast-transaction'.format(node)
                        response = requests.post(url, json={
                            'sender': sender,
                            'recipient': recipient,
                            'amount': amount,
                            'signature': signature
                        })
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolution.')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False

    def mine_block(self):
        if self.public_key is None:
            return None
        last_block = self.__chain[-1]
        hashed_block = hash_util.hash_block(last_block)
        proof = self.proof_of_work()
        # reward_transaction = {
        #     'sender': 'MINING',
        #     'recipient': owner,
        #     'amount': MINING_REWARD
        # }
        reward_transaction = Transaction(
            'MINING', self.public_key, '', MINING_REWARD)
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block,
                      copied_transactions, proof)
        self.__chain.append(block)
        self.save_data()
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            print('URL', url)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [
                tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Transaction declined, needs resolution.')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self, block):
        transactions = [Transaction(tx['sender'],
                                    tx['recipient'],
                                    tx['signature'],
                                    tx['amount'])
                        for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['prev_hash'], block['proof'])
        hashes_match = hash_util.hash_block(
            self.chain[-1]) == block['prev_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block['index'], block['prev_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        stored_open_transactions = self.__open_transactions[:]
        for itx in block['transactions']:
            for opentx in stored_open_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Transaction was already removed.')

        self.save_data()
        return True

    def resolve(self):
        winner_chain = self.chain
        replace = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'],
                                    block['prev_hash'],
                                    [Transaction(tx['sender'],
                                                 tx['recipient'],
                                                 tx['signature'],
                                                 tx['amount'])
                                    for tx in block['transactions']],
                                    block['proof'], block['timestamp'])
                              for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain
                    replace = True
            except requests.exceptions.ConnectionError:
                continue
        self.resolve_conflicts = False
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace

    def add_peer_node(self, node):
        """Adds a new node to the peer node set.

        Args:
            node (string): The node URL to be added.
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """Removes a node to the peer node set.

        Args:
            node (string): The node URL to be removed.
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """Returns a list of connected peer nodes"""
        return list(self.__peer_nodes)
