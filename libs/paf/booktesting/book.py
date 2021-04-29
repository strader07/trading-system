#!/usr/bin/env python

import time
import traceback
import curses

from pylimitbook import book

# from pylimitbook.bookViewerBook import BookViewerBook
from pylimitbook.researchBook import ResearchBook
from pylimitbook.tick import convert_price
from pylimitbook.bookViewer import BookViewer

from datetime import datetime  # , time


def ms_time():
    now = datetime.now()
    return int(time.mktime(now.timetuple()) * 1e3 + now.microsecond)


def start_viewer():
    try:
        # Initiate window
        stdscr = curses.initscr()
        curses.noecho()  # hide cursor

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)  # Hide cursor

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        stdscr.keypad(1)
        bookViewer = BookViewer()
        bookViewer.main(stdscr)  # Enter the main loop

        # Set everything back to normal
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()  # Terminate curses
    except KeyboardInterrupt:
        # ctrl-c
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
    except:
        # In the event of an error, restore the terminal
        # to a sane state.
        stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        traceback.print_exc()  # Print the exception


if __name__ == "__main__":
    # book = BookViewerBook()
    book = ResearchBook()
    book.save_tseries = True
    book.bid_split("AAPL", 1, 10, "1000.00", ms_time())
    book.bid_split("AAPL", 2, 100, "1100.00", ms_time())
    book.ask_split("AAPL", 3, 60, "1150.00", ms_time())
    book.trade_split("AAPL", 4, "1150.00", ms_time())  # why not removing?

    print(book.top_bid_price)
    print(book.spread)
    print(book.midpoint_price)

    print("---")

    print(book)

    # serialize the book into a CSV file, and pass it

    # convert the book to a file and pass that file

    # start_viewer()

    for t, val in book.time_series.items():
        print("{}: {}".format(t, val))
        # add function to serialize to csv and pass that to viewer as a file or something
        # `B,<symbol>,<exchange>,<id>,<quantity>,<price>,<timestamp>`
        # `A,<symbol>,<exchange>,<id>,<quantity>,<price>,<timestamp>`
        # `T,<symbol>,<exchange>,,<quantity>,<price>,<timestamp>`
