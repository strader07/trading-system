import logging
from datetime import datetime, timezone
from typing import Tuple

from paf.events.enums import Side
from paf.tardis_client.orderbook import OrderBook

from pandas import DataFrame
import pyarrow as pa
from numpy import nan


class Book:
    def __init__(self, exchange, symbol, from_date, to_date, messages):
        self.exchange = exchange
        self.symbol = symbol
        self.from_date = from_date
        self.to_date = to_date
        self.messages = messages
        self.book = OrderBook()
        self.event_id = 0

        self.trades = []
        self.liquidations = messages[-1][1]

    @property
    def title(self):
        return f"{self.symbol}: {self.from_date} - {self.to_date}"

    def generate_pyarrow_lob(self, depth):
        """
        Yields a generator of pyarrow batch objects, which is more memory efficient for streaming.
        User needs to handle PyArrow RecordBatches and build a table.
        See helper build_lob_table below for building the table.
        """
        # PyArrow is in columnar format. So we will store each column separately.

        dt_col = []
        exchange_col = []
        symbol_col = []
        bids_prices_cols = [[] for _ in range(depth)]
        bids_sizes_cols = [[] for _ in range(depth)]
        asks_prices_cols = [[] for _ in range(depth)]
        asks_sizes_cols = [[] for _ in range(depth)]

        # Build schema
        bids_fields_lsts = [
            ((f"BidPrice{i}", pa.float64()), (f"BidSize{i}", pa.float64()))
            for i in range(depth)
        ]
        bids_fields = []
        for lst in bids_fields_lsts:
            bids_fields.extend(lst)
        asks_fields_lsts = [
            ((f"AskPrice{i}", pa.float64()), (f"AskSize{i}", pa.float64()))
            for i in range(depth)
        ]
        asks_fields = []
        for lst in asks_fields_lsts:
            asks_fields.extend(lst)
        fields = [
            ("time", pa.timestamp("us")),
            ("exchange", pa.string()),
            ("symbol", pa.string()),
        ]
        fields.extend(bids_fields)
        fields.extend(asks_fields)
        schema = pa.schema(fields)

        count = 0
        batch_size = 1000

        for message in self.messages:
            self.on_message(message)
            if message[0] == "L":
                continue

            try:
                dt = message[1][0][0].date if message[0] == "S" or message[0] == "Q" else message[1].date
            except:
                dt = message[1][1][0].date if message[0] == "S" or message[0] == "Q" else message[1].date

            dt = dt.replace(tzinfo=timezone.utc)
            dt_col.append(int(dt.timestamp() * 1000000))
            exchange_col.append(self.exchange)
            symbol_col.append(self.symbol)

            bids_price_levels = self.book.bids.keys()
            asks_price_levels = self.book.asks.keys()

            for i in range(depth):
                try:
                    size = float(self.book.bids.values()[-i-1])
                except IndexError:
                    bids_prices_cols[i].append(nan)
                    bids_sizes_cols[i].append(nan)
                else:
                    price = float(bids_price_levels[-i-1])
                    bids_prices_cols[i].append(price)
                    bids_sizes_cols[i].append(size)
                    
                try:
                    size = float(self.book.asks.values()[i])
                except IndexError:
                    asks_prices_cols[i].append(nan)
                    asks_sizes_cols[i].append(nan)
                else:
                    price = float(asks_price_levels[i])
                    asks_prices_cols[i].append(price)
                    asks_sizes_cols[i].append(size)

            if count + 1 < batch_size:
                count += 1
            else:
                yield self.get_record_batch(
                    schema,
                    depth,
                    dt_col,
                    exchange_col,
                    symbol_col,
                    bids_prices_cols,
                    bids_sizes_cols,
                    asks_prices_cols,
                    asks_sizes_cols,
                )

                # Clean up cache
                dt_col = []
                exchange_col = []
                symbol_col = []
                bids_prices_cols = [[] for _ in range(depth)]
                bids_sizes_cols = [[] for _ in range(depth)]
                asks_prices_cols = [[] for _ in range(depth)]
                asks_sizes_cols = [[] for _ in range(depth)]
                data_cache = []
                count = 0

        if bids_prices_cols:
            yield self.get_record_batch(
                schema,
                depth,
                dt_col,
                exchange_col,
                symbol_col,
                bids_prices_cols,
                bids_sizes_cols,
                asks_prices_cols,
                asks_sizes_cols,
            )

    def build_lob_table(self, depth=20):
        """
        Builds the PyArrow table from streaming batches for each tick.
        """
        book_batches = []
        for book_batch in self.generate_pyarrow_lob(depth):
            book_batches.append(book_batch)

        book_table = pa.Table.from_batches(book_batches) if book_batches else None

        trades_table = (
            pa.Table.from_batches([self.get_trades_record_batch(self.trades)])
            if self.trades
            else None
        )

        return book_table, trades_table

    @staticmethod
    def get_record_batch(
        schema,
        depth,
        dt_col,
        exchange_col,
        symbol_col,
        bids_prices_cols,
        bids_sizes_cols,
        asks_prices_cols,
        asks_sizes_cols,
    ):
        # Place arrays per the schema order
        data = [
            pa.array(dt_col),
            pa.array(exchange_col),
            pa.array(symbol_col),
        ]
        for i in range(depth):
            data.append(pa.array(bids_prices_cols[i]))
            data.append(pa.array(bids_sizes_cols[i]))
        for i in range(depth):
            data.append(pa.array(asks_prices_cols[i]))
            data.append(pa.array(asks_sizes_cols[i]))
        return pa.RecordBatch.from_arrays(data, schema=schema)

    def get_trades_record_batch(self, trades):
        fields = [
            ("time", pa.timestamp("us")),
            ("exchange", pa.string()),
            ("symbol", pa.string()),
            ("trade_id", pa.uint64()),
            ("price", pa.float64()),
            ("size", pa.float64()),
            ("side", pa.string()),
            ("liquidation", pa.bool_()),
        ]
        schema = pa.schema(fields)

        time_col = []
        exchange_col = []
        symbol_col = []
        trade_id_col = []
        price_col = []
        size_col = []
        side_col = []
        liquidation_col = []

        for trade in trades:
            time_col.append(trade["time"])
            exchange_col.append(trade["exchange"])
            symbol_col.append(trade["symbol"])
            trade_id_col.append(trade["trade_id"])
            price_col.append(trade["price"])
            size_col.append(trade["size"])
            side_col.append(Side.to_string(trade["side"]))
            liquidation_col.append(trade["liquidation"])

        data = [
            pa.array(time_col),
            pa.array(exchange_col),
            pa.array(symbol_col),
            pa.array(trade_id_col),
            pa.array(price_col),
            pa.array(size_col),
            pa.array(side_col),
            pa.array(liquidation_col),
        ]

        return pa.RecordBatch.from_arrays(data, schema=schema)

    def lob_trade(self, trade):
        t = {
            "time": trade.date,
            "exchange": self.exchange,
            "symbol": trade.symbol,
            "trade_id": trade.id_,
            "price": float(trade.price),
            "size": float(trade.size),
            "side": trade.side,
            "liquidation": trade.id_ in self.liquidations,
        }
        self.trades.append(t)

    def process_quote(self, quote):
        self.book.update_level(
            quote.side,
            quote.size,
            quote.price,
        )

    def on_message(self, message):
        if message[0] == "S":
            self.book.clear_level()
            for bid in message[1][0]:
                self.process_quote(bid)
            for ask in message[1][1]:
                self.process_quote(ask)

        elif message[0] == "Q" and self.book:
            for bid in message[1][0]:
                self.process_quote(bid)
            for ask in message[1][1]:
                self.process_quote(ask)

        elif message[0] == "T":
            trade = message[1]
            self.book.add_trade(
                datetime.timestamp(trade.date),
                self.symbol,
                trade.size,
                str(trade.price),
            )

            self.lob_trade(trade)
