#!/usr/bin/env python3


# Strategy Outline:
#  1. Waiting for a drop in the ask offer for ETH.
#
# Execution:
#   - Copy this file from the strategies directory to the level below. Run with python3.

import json
import requests

from decimal import Decimal

from libraries.logger import logger
from libraries.dealseeker import askfall

pair = 'ETH-USDC'
drop = '0.03'

# Open websocket connection.
# Wait for asks to fall in price.
logger.info(f'waiting for {pair} to drop {Decimal(drop)*100}% in price.')
deal = askfall( pair, drop )
