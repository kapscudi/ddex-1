#!/usr/bin/env python3


# Warning:
#
# This version of rentseeker is using synchronous communications. This may not be ideal.
# If the messages are processed faster than they are received, this code is good. If not,
# you are going to lose money.
#
# According to https://pypi.org/project/websocket_client/ [Short-lived one-off send-receive]:
# This is if you want to communicate a short message and disconnect immediately when done.


import requests
import ssl
import json
import datetime
import time

from decimal import Decimal
from websocket import create_connection

from libraries.logger import logger as logger
from libraries.messenger import smsalert as smsalert

import libraries.resourcelocator as resourcelocator

def bidrise (
        pair: str,
        gain: str
        ) -> None:

    # Define base class.
    # Purpose: Stores the first best bid offer of the websocket connection session.
    class Base:
        def __init__(self, price): self.__price = price
        def getvalue(self): return self.__price
        def setvalue(self, price): self.__price = price

    # Instantiate base object.
    base = Base(0)

    # Construct subscription request.
    subscriptionrequest = f'{{ "type": "subscribe", "channels": [{{ "name": "orderbook", "marketIds": ["{pair}"]}}] }}'

    # Establish websocket connection.
    ws = create_connection(resourcelocator.sockserver)
    ws.send( subscriptionrequest )
    while True:
        newmessage = ws.recv()
        dictionary = json.loads( newmessage )
        profitable = Decimal( gain )

        # Unncomment this statement to debug messages: logger.debug(dictionary)

        # Process "type": "level2OrderbookSnapshot" messages.
        if 'level2OrderbookSnapshot' in dictionary['type']:
            if dictionary['bids'] != []:
                bids = dictionary['bids']

                # Rank bids and determine the highest bid in the orderbook from dYdX update response.
                bidranking = [ Decimal(bid['price']) for bid in bids ]
                if bidranking != []: maximumbid = max(bidranking)
                base.setvalue( maximumbid )

                # Define bargain (sale) bid offer.
                deal = Decimal( Decimal( base.getvalue() ) * ( 1 + profitable ) )

        # Process "type": "level2OrderbookUpdate" messages.
        if 'level2OrderbookUpdate' in dictionary['type']:
            if dictionary['changes'] != []:
                changes = dictionary['changes']

                # Rank bids and determine the highest bid in the orderbook from dYdX update response.
                bidranking = [ Decimal(change['price']) for change in changes if change['side'] == 'buy' ]
                if bidranking != []:
                    maximumbid = max(bidranking)
                    if maximumbid.compare( deal ) == 1 :
                        logger.info( f'{pair} [now {maximumbid:.2f}] just rose above {deal:.2f}.' )
                        smsalert( f'There was a {profitable*100}% rise in the bid offer [{maximumbid}] on the {pair} pair on DDEX.' )
                        ws.close()
                        break

                    else:
                        # Calculate movement away from base [if any].
                        move = 100 * ( maximumbid - base.getvalue() ) / base.getvalue()

                        # Display impact of event information received.
                        logger.info( f'{move:.2f}% move away from [{base.getvalue()}] : {pair} is {maximumbid} presently.' )

    # Return value on discount only.
    if maximumbid.compare(0) == 1 :
        return maximumbid
    else: return False
