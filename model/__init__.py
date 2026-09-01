#%%
"""Fantasy football analytics."""

import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")

from model.fpl_api import FPLAPIClient
from model.model import predict_upcoming_fixtures_from_fpl


if __name__ == '__main__':

    client = FPLAPIClient(manager_id = 9836874)

    snapshot = client.load_snapshot()

#%%