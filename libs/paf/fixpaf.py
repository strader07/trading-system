#!/usr/bin/env python
import argparse
import logging

from paf import strategies  # noqa: F401
from paf.fix_client import Client


def main(strategy_name):
    logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)

    # strategy has access to the book and we just notify it of the event change
    try:
        mod = __import__("paf.strategies", fromlist=[strategy_name])
        klass = getattr(mod, strategy_name)
        strategy = klass.Strategy()
    except:  # noqa: E722
        logging.error(
            f"Error instantiating strategy {strategy_name}. Strategy does not exist or you're passing invalid arguments "
        )
        raise

    client = Client(strategy, "BTC-USD")
    client.start()

    logging.info("All done... shutting down")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Analytical Framework [PAF]")
    parser.add_argument("strategy", type=str, help="strategy name")
    args = parser.parse_args()
    main(args.strategy)
