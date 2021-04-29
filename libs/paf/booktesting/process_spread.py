import logging
from paf.signals import SigSpread
import pandas as pd


def process_spread(book):
    # df = pd.DataFrame(columns=["avg_spread_change_60s", "px_change_60s"])
    # df = pd.DataFrame(columns=["avg_spread_change_60s"])
    # df.set_index("window", inplace=True, drop="True")

    spread = SigSpread()
    book.register_spread_update(spread.on_spread_update)
    book.build()

    # the last spread_per_minute has no mid_price_after_minute value
    df = pd.DataFrame(
        {
            "avg_spread_change_60s": spread.spread_per_minute[:-1],
            "mid_price_after_minute": spread.mid_price_after_minute,
        }
    )

    return df

    #     matched = len(orderflow.matching_flow_trade)
    #     unmatched = len(orderflow.unmatching_flow_trade)
    #     neutral = len(orderflow.neutral_flow)

    #     if matched == 0 and unmatched == 0 and neutral == 0:
    #         logging.info(
    #             f"Skipping empty {book.symbol} - {book.from_date} - {book.to_date}"
    #         )
    #         continue

    #     if df.index.isin([i]).any():
    #         df.loc[i] += [matched, unmatched, neutral]
    #     else:
    #         df.loc[i] = [matched, unmatched, neutral]

    #     orderflows_by_window.append((i, orderflow))

    # return df, orderflows_by_window
