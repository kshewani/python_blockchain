from collections import OrderedDict
from utils.printable import Printable


class Transaction(Printable):
    """[summary]

    Args:
        Printable ([type]): [description]
    """
    def __init__(self, sender, recipient, signature, amount) -> None:
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

    def to_ordered_dict(self):
        return OrderedDict([('sender', self.sender),
                            ('recipient', self.recipient),
                            ('amount', self.amount)])
