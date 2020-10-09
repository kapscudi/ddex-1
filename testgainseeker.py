#!/usr/bin/env python3


# Strategy Outline:
#  1. Waiting for a rise in the bid offer for ETH.
#
# Execution:
#   - Copy this file from the strategies directory to the level below. Run with python3.

import json
import requests

from decimal import Decimal

from libraries.logger import logger
from libraries.rentseeker import bidrise

pair = 'ETH-USDC'
rise = '0.001'

# Open websocket connection.
# Wait for asks to fall in price.
logger.info(f'waiting for {pair} to rise {Decimal(rise)*100}% in price.')
deal = bidrise( pair, rise )
