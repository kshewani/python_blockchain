from uuid import uuid4
from blockchain import BlockChain
from utils.verification import Verification
from wallet import Wallet


class Node:
    def __init__(self):
        # self.id = str(uuid4())
        self.wallet = Wallet()
        self.wallet.create_keys()
        self.blockchain = BlockChain(self.wallet.public_key)

    def print_blockchain_elements(self):
        for block in self.blockchain.chain:
            print('Outputting block')
            print(block)
        else:
            print('-' * 20)

    def get_user_choice(self):
        user_input = input("Your choice: ")
        return user_input

    def get_transaction_value(self):
        tx_recipient = input('Enter the recipient of the transaction: ')
        tx_amount = float(input('Enter the amount of the transaction: '))
        return (tx_recipient, tx_amount)

    def listen_for_input(self):
        waiting_for_input = True
        while waiting_for_input:
            print('Please choose')
            print("1: Add a new transation value")
            print("2: Mine a new block")
            print("3: Output the blockchain blocks")
            print("4: Verify transactions")
            print("5: Create wallet")
            print("6: Load wallet")
            print("7: Save keys")
            print("q: Quit")
            user_choice = self.get_user_choice()
            if user_choice == '1':
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                signature = self.wallet.sign_transaction(
                    self.wallet.public_key, recipient, amount)
                if self.blockchain.add_transaction(recipient, self.wallet.public_key, signature, amount=amount):
                    print('Transaction added')
                else:
                    print('Transaction failed')
                print(self.blockchain.get_open_transactions())
            elif user_choice == '2':
                if self.blockchain.mine_block():
                    print('Minig failed. Got no wallet?')
            elif user_choice == '3':
                self.print_blockchain_elements()
            elif user_choice == '4':
                verifier = Verification()
                if verifier.verify_transactions(self.blockchain.get_open_transactions(),
                                                self.blockchain.get_balance):
                    print('All transactions are valid')
                else:
                    print('There are invalid transations')
            elif user_choice == 'q':
                waiting_for_input = False
            elif user_choice == '5':
                self.wallet.create_keys()
                self.blockchain = BlockChain(self.wallet.public_key)
            elif user_choice == '6':
                self.wallet.create_keys()
                self.blockchain = BlockChain(self.wallet.public_key)
            elif user_choice == '7':
                self.wallet.save_keys()
            else:
                print('Invalid choice, please choose from the list')
            verifier = Verification()
            if not verifier.verify_chain(self.blockchain.chain):
                self.print_blockchain_elements()
                print("Invalid blockchain!")
                break
            # print(blockchain)
            print('Balance of {}: {:6.2f}'.format(self.wallet.public_key,
                                                  self.blockchain.get_balance()))
        print("Done!")


if __name__ == '__main__':
    node = Node()
    node.listen_for_input()
