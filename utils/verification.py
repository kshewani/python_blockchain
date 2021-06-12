from utils import hash_util
from wallet import Wallet

class Verification:
    PROOF_OF_WORK_CONDITION = '00'

    @classmethod
    def valid_proof(cls, transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]) +
                 str(last_hash) + str(proof)).encode()
        guess_hash = hash_util.hash_string_256(guess)
        return guess_hash[0:2] == cls.PROOF_OF_WORK_CONDITION

    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.prev_hash != hash_util.hash_block(blockchain[index-1]):
                return False
            if not cls.valid_proof(block.transactions[:-1], block.prev_hash, block.proof):
                print('Invalid proof of work')
                return False
        return True

    @staticmethod
    def verify_transaction(transaction, get_balance, check_availabe_funds = True):
        if check_availabe_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(tx, get_balance, False) for tx in open_transactions])
