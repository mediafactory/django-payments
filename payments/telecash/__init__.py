import logging
from .. import (
    BasicProvider, get_credit_card_issuer, PaymentError, RedirectNeeded)

# Get an instance of a logger
logger = logging.getLogger(__name__)

CENTS = Decimal('0.01')

class TelecashProvider(BasicProvider):
    '''
    www.telecash.de payment provider
    '''
