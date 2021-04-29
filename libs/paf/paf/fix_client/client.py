#!/usr/bin/python3
import logging
from typing import List

from pyfix.connection import ConnectionState, MessageDirection
from pyfix.client_connection import FIXClient
from pyfix.engine import FIXEngine
from pyfix.message import FIXMessage, FIXContext

from paf.fix_client.enums import State
from paf.fix_client.order import Order
from paf.events import MarketSnapshot, MarketRefresh, MDEntry, Side


class Client(FIXEngine):
    def __init__(self, strategy, symbol, depth=0, journal_file=None):
        FIXEngine.__init__(self, journal_file)

        # TODO: remove?
        # Limits and thresholds
        # Threshold away from oppose bid or offer from price signal to get out
        # self.bbo_threshold = 0.02
        # Threshold away from last order to get out
        # self.last_threshold = 0.01
        # Percent below/above last price to turn limit order into quasi market order
        # self.force_limit = 0.5

        self.symbol = symbol
        self.depth = depth

        # Order state
        self.clOrdID = 0
        self.current_order = None
        self.current_position = 0
        self.position_price = 0

        # Position adjuster
        # self.orderAdjuster = None

        # Algorithm Runner
        self.strategy = strategy

        # create a FIX Client using the FIX 4.4 standard
        self.client = FIXClient(self, "pyfix.FIX44", "TRADER", "PYTHON")

        # we register some listeners since we want to know when the connection goes up or down
        self.client.addConnectionListener(self.onConnect, ConnectionState.CONNECTED)
        self.client.addConnectionListener(
            self.onDisconnect, ConnectionState.DISCONNECTED
        )

    def start(self):
        # start our event listener indefinitely
        self.client.start("localhost", int("4222"))
        while True:
            self.eventManager.waitForEventWithTimeout(10.0)

        # some clean up before we shut down
        self.client.removeConnectionListener(self.onConnect, ConnectionState.CONNECTED)
        self.client.removeConnectionListener(
            self.onConnect, ConnectionState.DISCONNECTED
        )

    # # TODO: fix/change
    # def update_position(self, price, fill, side):
    #     self.position_price = price
    #     if side == Side.bid:
    #         self.current_position += fill
    #     elif side == Side.ask:
    #         self.current_position -= fill

    #     self.position_price = price if self.current_position != 0 else 0

    # # TODO: fix/change
    # def check_positions(self, connectionHandler):
    #     """ If market is far from our price, get out """

    #     if self.current_order and self.current_order.state in (
    #         State.created,
    #         State.pending,
    #     ):
    #         # We skip checking while we have orders in pending state
    #         return
    #     elif self.current_order and self.current_order.state is State.partial_fill:
    #         # TODO: Handle partial fills. Timer on them?
    #         return
    #     elif self.last_trade_price <= 0:
    #         return

    #     ref_price = 0
    #     func = None
    #     order = None

    #     if self.current_order:
    #         ref_price = self.current_order.price
    #         func = self.cancelOrder
    #         order = self.current_order

    #     elif self.current_position != 0:
    #         ref_price = self.position_price
    #         func = self.sendOrder
    #         side = Side.bid if self.current_position < 0 else Side.ask
    #         order = Order(
    #             self.last_bid_price if side == Side.bid else self.last_ask_price,
    #             abs(self.current_position),
    #             side,
    #         )

    #     else:
    #         return

    #     trade_upper = (1.0 + self.last_threshold) * ref_price
    #     trade_lower = (1.0 - self.last_threshold) * ref_price
    #     ask_upper = (1.0 + self.bbo_threshold) * ref_price
    #     bid_lower = (1.0 - self.bbo_threshold) * ref_price

    #     adjustment_conditions = [
    #         self.last_trade_price >= trade_upper,
    #         self.last_trade_price <= trade_lower,
    #         order and order.side == Side.bid and self.last_ask_price >= ask_upper,
    #         order and order.side == Side.ask and self.last_bid_price <= bid_lower,
    #     ]

    #     if any(adjustment_conditions):
    #         func(connectionHandler, self.symbol, order)

    # TODO: remove
    def sizer(self, signal):
        """ This is the execution strategy. In the future, move to different class. """

        size = self.position_size
        side = Side.from_signal(signal)

        if self.current_order and self.current_order.state in (
            State.created,
            State.pending,
            State.opened,
            State.partial_fill,
        ):
            # TODO: handle that the pending/open order is in the opposite direction
            return None, None

        elif self.current_position:
            # Adjust size
            if side == Side.BID:
                if self.current_position > 0:
                    return None, None
                size = self.current_position * -1 + self.position_size
            elif side == Side.ASK:
                if self.current_position < 0:
                    return None, None
                size = self.current_position * -1 - self.position_size
            elif side is None:
                size = -self.current_position
                side = Side.BID if self.current_position < 0 else Side.ASK

        logging.info("Signal: %s | Side: %s | Size: %s" % (signal, side, size))

        return size, side

    def onConnect(self, session):
        logging.info("Established connection to %s" % (session.address(),))
        # register to receive message notifications on the session which has just been created
        session.addMessageHandler(
            self.onLogin, MessageDirection.INBOUND, self.client.protocol.msgtype.LOGON
        )
        session.addMessageHandler(
            self.onMktSnapshot,
            MessageDirection.INBOUND,
            self.client.protocol.msgtype.MARKETDATASNAPSHOTFULLREFRESH,
        )
        session.addMessageHandler(
            self.onMktRefresh,
            MessageDirection.INBOUND,
            self.client.protocol.msgtype.MARKETDATAINCREMENTALREFRESH,
        )
        session.addMessageHandler(
            self.onExecutionReport,
            MessageDirection.INBOUND,
            self.client.protocol.msgtype.EXECUTIONREPORT,
        )

    def onDisconnect(self, session):
        logging.info("%s has disconnected" % (session.address(),))
        # we need to clean up our handlers, since this session is disconnected now
        session.removeMessageHandler(
            self.onLogin, MessageDirection.INBOUND, self.client.protocol.msgtype.LOGON
        )
        session.removeMessageHandler(
            self.onExecutionReport,
            MessageDirection.INBOUND,
            self.client.protocol.msgtype.EXECUTIONREPORT,
        )
        # if self.orderAdjuster:
        #     self.eventManager.unregisterHandler(self.orderAdjuster)

    def onLogin(self, connectionHandler, msg):
        logging.info("Logged in")

        self.subscribeMktData(connectionHandler, self.symbol, 60)
        # self.orderAdjuster = TimerEventRegistration(
        #     lambda type, closure: self.check_positions(closure), 10, connectionHandler
        # )
        # self.eventManager.registerHandler(self.orderAdjuster)

    def subscribeMktData(self, connectionHandler, symbol, vwap_n_sec):
        codec = connectionHandler.codec
        msg = FIXMessage(codec.protocol.msgtype.MARKETDATAREQUEST)
        msg.setField(codec.protocol.fixtags.SubscriptionRequestType, 1)

        msg.setField(codec.protocol.fixtags.MarketDepth, self.depth)
        msg.setField(codec.protocol.fixtags.MDUpdateType, 0)

        # Subscribe to bids
        bidgrp = FIXContext()
        bidgrp.setField(codec.protocol.fixtags.MDEntryType, 0)
        bidgrp.setField(codec.protocol.fixtags.Symbol, self.symbol)
        msg.addRepeatingGroup(codec.protocol.fixtags.NoMDEntryTypes, bidgrp)

        # Subscribe to asks
        askgrp = FIXContext()
        askgrp.setField(codec.protocol.fixtags.MDEntryType, 1)
        askgrp.setField(codec.protocol.fixtags.Symbol, self.symbol)
        msg.addRepeatingGroup(codec.protocol.fixtags.NoMDEntryTypes, askgrp)

        # Subscribe to matches
        matchgrp = FIXContext()
        matchgrp.setField(codec.protocol.fixtags.MDEntryType, 2)
        matchgrp.setField(codec.protocol.fixtags.Symbol, self.symbol)
        msg.addRepeatingGroup(codec.protocol.fixtags.NoMDEntryTypes, matchgrp)

        connectionHandler.sendMsg(msg)

    def processMarketDataEntries(self, msg, codec) -> (str, int, List):
        symbol = msg.getField(codec.protocol.fixtags.Symbol)
        # TODO: TradeVolume, OpenInterest - BitMEX and deribit custom
        no_entries, group = msg.getRepeatingGroup(codec.protocol.fixtags.NoMDEntries)

        entries = []
        for item in group:
            mdentrytype = int(item.getField(codec.protocol.fixtags.MDEntryType))
            price = item.getField(codec.protocol.fixtags.MDEntryPx)
            size = item.getField(codec.protocol.fixtags.MDEntrySize)
            aggressor = (
                Side(int(item.getField(codec.protocol.fixtags.AggressorIndicator)))
                if mdentrytype == 2
                else Side.UNINITIALIZED
            )
            date = item.getField(codec.protocol.fixtags.MDEntryDate)
            entries.append(
                MDEntry(int(mdentrytype), float(price), float(size), aggressor, date)
            )

        return symbol, no_entries, entries

    def onMktSnapshot(self, connectionHandler, msg):
        codec = connectionHandler.codec
        logging.debug(
            "<--- [%s] %s"
            % (
                codec.protocol.msgtype.msgTypeToName(msg.msgType),
                msg.getField(codec.protocol.fixtags.Symbol),
            )
        )

        symbol, no_entries, entries = self.processMarketDataEntries(msg, codec)
        # TODO: get volume and OI
        snapshot = MarketSnapshot(
            symbol,
            msg.getField(codec.protocol.fixtags.MsgSeqNum),
            0,
            0,
            no_entries,
            entries,
        )
        self.strategy.on_market_snapshot(snapshot)

    def onMktRefresh(self, connectionHandler, msg):
        codec = connectionHandler.codec
        # logging.debug(
        #     "<--- [%s] %s"
        #     % (
        #         codec.protocol.msgtype.msgTypeToName(msg.msgType),
        #         msg.getField(codec.protocol.fixtags.Symbol),
        #     )
        # )

        symbol, no_entries, entries = self.processMarketDataEntries(msg, codec)
        # TODO: get volume and OI
        entry_date = entries[0].MDEntryDate if entries else None
        refresh = MarketRefresh(
            symbol,
            msg.getField(codec.protocol.fixtags.MsgSeqNum),
            0,
            0,
            no_entries,
            entries,
            entry_date,
        )

        self.strategy.on_market_refresh(refresh)

    def cancelOrder(self, connectionHandler, symbol, order):
        """ Cancel an order """
        codec = connectionHandler.codec
        msg = FIXMessage(codec.protocol.msgtype.ORDERCANCELREQUEST)
        origClOrdID = str(order.clOrdID)
        clOrdID = Order.get_next_id()

        msg.setField(codec.protocol.fixtags.ClOrdID, clOrdID)
        msg.setField(codec.protocol.fixtags.Symbol, symbol)
        msg.setField(codec.protocol.fixtags.OrigClOrdID, origClOrdID)
        msg.setField(codec.protocol.fixtags.Side, int(order.side))

        connectionHandler.sendMsg(msg)
        logging.debug("---> Cancelling [%s] : %s" % (origClOrdID, clOrdID))

    def sendOrder(self, connectionHandler, symbol, order):
        codec = connectionHandler.codec
        msg = FIXMessage(codec.protocol.msgtype.NEWORDERSINGLE)
        msg.setField(codec.protocol.fixtags.ClOrdID, str(order.clOrdID))
        msg.setField(codec.protocol.fixtags.Symbol, symbol)
        msg.setField(codec.protocol.fixtags.Price, order.price)
        msg.setField(codec.protocol.fixtags.OrderQty, order.size)
        msg.setField(codec.protocol.fixtags.OrdType, 2)
        msg.setField(codec.protocol.fixtags.Side, int(order.side))
        msg.setField(codec.protocol.fixtags.HandlInst, "1")
        msg.setField(codec.protocol.fixtags.ExecInst, "6")  # 6 == Maker Only

        connectionHandler.sendMsg(msg)

        self.current_order = order
        self.current_order.state = State.pending
        # self.orderAdjuster.reset()

        side = Side(int(msg.getField(codec.protocol.fixtags.Side)))
        logging.debug(
            "---> Sending [%s] %s: %s %s %s@%s"
            % (
                codec.protocol.msgtype.msgTypeToName(msg.msgType),
                msg.getField(codec.protocol.fixtags.ClOrdID),
                msg.getField(codec.protocol.fixtags.Symbol),
                side.name,
                msg.getField(codec.protocol.fixtags.OrderQty),
                msg.getField(codec.protocol.fixtags.Price),
            )
        )

    def onExecutionReport(self, connectionHandler, msg):
        codec = connectionHandler.codec
        if codec.protocol.fixtags.ExecType in msg:
            if msg.getField(codec.protocol.fixtags.ExecType) == "0":
                self.current_order.state = State.opened
                side = Side(int(msg.getField(codec.protocol.fixtags.Side)))

                logging.debug(
                    "<--- New [%s] %s: %s %s %s@%s"
                    % (
                        codec.protocol.msgtype.msgTypeToName(
                            msg.getField(codec.protocol.fixtags.MsgType)
                        ),
                        msg.getField(codec.protocol.fixtags.ClOrdID),
                        msg.getField(codec.protocol.fixtags.Symbol),
                        side.name,
                        msg.getField(codec.protocol.fixtags.OrderQty),
                        msg.getField(codec.protocol.fixtags.Price),
                    )
                )

            elif msg.getField(codec.protocol.fixtags.ExecType) == "1":
                self.current_order.state = State.partial_fill
                side = Side(int(msg.getF3ield(codec.protocol.fixtags.Side)))
                # self.update_position(
                #     float(msg.getField(codec.protocol.fixtags.Price)),
                #     float(msg.getField(codec.protocol.fixtags.LastQty)),
                #     side,
                # )

                logging.debug(
                    "<--- Partial Fill [%s] %s: %s %s %s@%s (%s)"
                    % (
                        codec.protocol.msgtype.msgTypeToName(
                            msg.getField(codec.protocol.fixtags.MsgType)
                        ),
                        msg.getField(codec.protocol.fixtags.ClOrdID),
                        msg.getField(codec.protocol.fixtags.Symbol),
                        side.name,
                        msg.getField(codec.protocol.fixtags.OrderQty),
                        msg.getField(codec.protocol.fixtags.Price),
                        msg.getField(codec.protocol.fixtags.LastQty),
                    )
                )

            elif msg.getField(codec.protocol.fixtags.ExecType) == "2":
                self.current_order.state = State.filled
                side = Side(int(msg.getField(codec.protocol.fixtags.Side)))
                # self.update_position(
                #     float(msg.getField(codec.protocol.fixtags.Price)),
                #     float(msg.getField(codec.protocol.fixtags.LastQty)),
                #     side,
                # )

                self.current_order = None

                logging.debug(
                    "<--- Filled Order [%s] %s: %s %s %s@%s (%s)"
                    % (
                        codec.protocol.msgtype.msgTypeToName(
                            msg.getField(codec.protocol.fixtags.MsgType)
                        ),
                        msg.getField(codec.protocol.fixtags.ClOrdID),
                        msg.getField(codec.protocol.fixtags.Symbol),
                        side.name,
                        msg.getField(codec.protocol.fixtags.OrderQty),
                        msg.getField(codec.protocol.fixtags.Price),
                        msg.getField(codec.protocol.fixtags.LastQty),
                    )
                )

            elif msg.getField(codec.protocol.fixtags.ExecType) == "3":
                side = Side(int(msg.getField(codec.protocol.fixtags.Side)))
                logging.debug(
                    "<--- Done Order [%s] %s: %s %s %s@%s"
                    % (
                        codec.protocol.msgtype.msgTypeToName(
                            msg.getField(codec.protocol.fixtags.MsgType)
                        ),
                        msg.getField(codec.protocol.fixtags.ClOrdID),
                        msg.getField(codec.protocol.fixtags.Symbol),
                        side.name,
                        msg.getField(codec.protocol.fixtags.OrderQty),
                        msg.getField(codec.protocol.fixtags.Price),
                    )
                )

            elif msg.getField(codec.protocol.fixtags.ExecType) == "4":
                clOrdID = int(msg.getField(codec.protocol.fixtags.ClOrdID))
                if clOrdID != self.current_order.clOrdID:
                    logging.debug(
                        "<--- Cancellation for unknown [%s] %s: %s %s %s@%s"
                        % (
                            codec.protocol.msgtype.msgTypeToName(
                                msg.getField(codec.protocol.fixtags.MsgType)
                            ),
                            msg.getField(codec.protocol.fixtags.ClOrdID),
                            msg.getField(codec.protocol.fixtags.Symbol),
                            side.name,
                            msg.getField(codec.protocol.fixtags.OrderQty),
                            msg.getField(codec.protocol.fixtags.Price),
                        )
                    )
                    return

                self.current_order.state = State.cancelled
                self.current_order = None
                side = Side(int(msg.getField(codec.protocol.fixtags.Side)))

                logging.debug(
                    "<--- Cancelled [%s] %s: %s %s %s@%s"
                    % (
                        codec.protocol.msgtype.msgTypeToName(
                            msg.getField(codec.protocol.fixtags.MsgType)
                        ),
                        msg.getField(codec.protocol.fixtags.ClOrdID),
                        msg.getField(codec.protocol.fixtags.Symbol),
                        side.name,
                        msg.getField(codec.protocol.fixtags.OrderQty),
                        msg.getField(codec.protocol.fixtags.Price),
                    )
                )

            elif msg.getField(codec.protocol.fixtags.ExecType) == "8":
                self.current_order.state = None
                reason = (
                    "Unknown"
                    if codec.protocol.fixtags.Text not in msg
                    else msg.getField(codec.protocol.fixtags.Text)
                )
                logging.info("Order Rejected '%s'" % (reason,))

        else:
            logging.error("Received execution report without ExecType")
