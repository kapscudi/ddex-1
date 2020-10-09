#!/usr/bin/env python3


# Warning:
#
# This version of dealseeker is using synchronous communications. This may not be ideal.
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

def askfall (
        pair: str,
        drop: str
        ) -> None:

    # Define high class.
    # Purpose: Stores the highest ask offer reached during the websocket connection session.
    class High:
        def __init__(self, price): self.__price = price
        def getvalue(self): return self.__price
        def setvalue(self, price): self.__price = price

    # Define deal class.
    # Purpose: Stores the deal (ask) offer reached during the websocket connection session.
    class Deal:
        def __init__(self, price): self.__price = price
        def getvalue(self): return self.__price
        def setvalue(self, price): self.__price = price

    # Instantiate high/deal objects.
    high = High(0)
    deal = Deal(0)

    # Construct subscription request.
    subscriptionrequest = f'{{ "type": "subscribe", "channels": [{{ "name": "orderbook", "marketIds": ["{pair}"]}}] }}'

    # Establish websocket connection.
    ws = create_connection(resourcelocator.sockserver)
    ws.send( subscriptionrequest )
    while True:
        newmessage = ws.recv()
        dictionary = json.loads( newmessage )
        percentoff = Decimal( drop )
        sessionmax = Decimal( high.getvalue() )

        # Unncomment this statement to debug messages: logger.debug(dictionary)

        # Process "type": "level2OrderbookSnapshot" messages.
        if 'level2OrderbookSnapshot' in dictionary['type']:
            if dictionary['asks'] != []:
                asks = dictionary['asks']

                # Rank bids and determine the highest bid in the orderbook from dYdX update response.
                askranking = [ Decimal(ask['price']) for ask in asks ]
                if askranking != []: minimumask = min(askranking)
                if minimumask.compare( Decimal(sessionmax) ) == 1 :
                        sessionmax = minimumask
                        high.setvalue(minimumask)

        # Process "type": "level2OrderbookUpdate" messages.
        if 'level2OrderbookUpdate' in dictionary['type']:
            if dictionary['changes'] != []:
                changes = dictionary['changes']

                # Rank bids and determine the highest bid in the orderbook from dYdX update response.
                askranking = [ Decimal(change['price']) for change in changes if change['side'] == 'sell' ]
                if askranking != []:
                    minimumask = min(askranking)
                    if minimumask.compare( Decimal(sessionmax) ) == 1 :
                            sessionmax = minimumask
                            high.setvalue(minimumask)

                    # Calculate movement away from high [if any].
                    move = 100 * ( sessionmax - minimumask ) / sessionmax

                    # Display impact of event information received.
                    logger.info( f'{move:.2f}% off highs [{sessionmax}] : {pair} is {minimumask} presently.' )

                    # Define bargain (sale) price.
                    sale = Decimal( sessionmax * ( 1 - percentoff ) )

                    # Exit loop if there's a sale.
                    if sale.compare( minimumask ) == 1 :
                        logger.info( f'{pair} [now {minimumask:.2f}] just went on sale [dropped below {sale:.2f}].' )
                        smsalert( f'There was a {percentoff*100}% drop in the ask offer [{minimumask}] on the {pair} pair on DDEX.' )

                        # Update deal price.
                        deal.setvalue(minimumask)
                        ws.close()
                        break

    # Return value on discount only.
    last = Decimal( deal.getvalue() )
    if last.compare(0) == 1 :
        return last
    else: return False
