import logging
from paf.signals import SigOrderFlow
import pandas as pd


def book_update(data):
    pass


def process_orderflow(book, windows):
    df = pd.DataFrame(columns=["window", "matched", "unmatched", "neutral"])
    df.set_index("window", inplace=True, drop="True")

    orderflows_by_window = []

    for i in windows:
        orderflow = SigOrderFlow(book, max_len=i)
        book.register_trade(orderflow.on_trade_flow_match)
        book.register_book(book_update)
        book.build()

        matched = len(orderflow.matching_flow_trade)
        unmatched = len(orderflow.unmatching_flow_trade)
        neutral = len(orderflow.neutral_flow)

        if matched == 0 and unmatched == 0 and neutral == 0:
            logging.info(
                f"Skipping empty {book.symbol} - {book.from_date} - {book.to_date}"
            )
            continue

        if df.index.isin([i]).any():
            df.loc[i] += [matched, unmatched, neutral]
        else:
            df.loc[i] = [matched, unmatched, neutral]

        orderflows_by_window.append((i, orderflow))

    return df, orderflows_by_window
