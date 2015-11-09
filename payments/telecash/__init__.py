""" Telecash. """
import logging
import urllib
from decimal import Decimal
from django.shortcuts import redirect

from .. import (
    BasicProvider)

# Get an instance of a logger
logger = logging.getLogger(__name__)

CENTS = Decimal('0.01')


class TelecashProvider(BasicProvider):

    """ Telecash Paymnet Gateway. """

    def __init__(self, *args, **kwargs):
        """ Telecash. """
        self.storename = kwargs.pop('storeid')
        self.uri = kwargs.pop(
            'uri', 'https://test.ipg-online.com/connect/gateway/processing')
        self.currency = kwargs.pop('currency')
        self.passphrase = kwargs.pop('passphrase')
        self.paymode = kwargs.pop('paymode')
        kwargs.pop('auto_submit')

        super(TelecashProvider, self).__init__(*args, **kwargs)

    def create_hash(self, data):
        """ convert data to hash 1. Hex 2. Sha1:TCStoreID + timestamp. """
        """+ fAmount + TCCurrency + TCPassphrase. """
        hash = data.encode('hex')
        import hashlib
        return hashlib.sha1(hash).hexdigest()

    def get_hidden_fields(self):
        """ Hidden fields for post action."""
        return_url = self.get_return_url()
        hash_data = "%s%s%s%s%s" % (self.storename, self.payment.created.strftime("%Y:%m:%d-%H:%M:%S"), self.payment.total, self.currency, self.passphrase)
        myhash = self.create_hash(hash_data)

        data = {
                'timezone': 'CET',
                'txntype': 'sale',
                'oid': self.payment.orderid,
                'storename': self.storename,
                'responseFailURL': return_url,
                'responseSuccessURL': return_url,
                'mode': self.paymode,
                'txndatetime': self.payment.created.strftime("%Y:%m:%d-%H:%M:%S"),
                'chargetotal': self.payment.total,
                'currency': self.currency,
                'hash': myhash
        }
        self.payment.extra_data = urllib.urlencode(data)
        self.payment.transaction_id = myhash
        self.payment.save()

        return data

    @property
    def _action(self):
        return self.uri

    def process_data(self, request):
        """ check response: compare hashcodes, processor_response_code==00. """
        # stringToHash = TCPassphrase & Request("approval_code") & Request("chargetotal") & Request("currency") & oDDD("Result") & TCStoreID
        hash_data = "%s%s%s%s%s%s" % (self.passphrase, request.POST['approval_code'], request.POST['chargetotal'], request.POST['currency'], self.payment.created.strftime("%Y:%m:%d-%H:%M:%S"), self.storename)

        self.payment.extra_data = request.POST.urlencode()
        if request.POST.get('oid'):
            self.payment.transaction_id = request.POST.get('oid')
        if not request.POST['response_hash'] == self.create_hash(hash_data):
            self.payment.change_status('rejected')
            return redirect(self.payment.get_failure_url())

        success_url = self.payment.get_success_url()
        if self.payment.status == 'waiting':
            if request.POST.get('processor_response_code') == '00':
                self.payment.change_status('confirmed')
                return redirect(success_url)
            else:
                self.payment.change_status('rejected')
                return redirect(self.payment.get_failure_url())
        return redirect(success_url)
