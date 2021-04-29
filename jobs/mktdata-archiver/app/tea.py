async def generate_teafile(run):
    book_tf = TeaFile.create(
        f"{run.src_filename(FileType.ORDERBOOK)}",
        f"{BookCols()}",
        "ddddddddddddddddddddddddddddddddddddddddd",
        run.description(),
        {
            "exchange": run.exchange,
            "symbol": run.market.instrument,
            "type": "orderbook",
        },
    )

    trades_tf = TeaFile.create(
        f"{run.src_filename(FileType.TRADES)}",
        f"{TradesCols()}",
        "diddBB",
        run.description(),
        {
            "decimals": run.dp,
            "exchange": run.exchange,
            "symbol": run.market.instrument,
            "type": "trades",
        },
    )

    dates = [
        datetime.combine(run.date, datetime.min.time()),
        # datetime.combine(run.date, datetime.max.time())
        datetime(2020, 3, 19, 00, 20, 00, 0),
    ]

    orderbooks = await booksbuilder([run.market.market], [dates])
    for book in orderbooks.values():

        book_df, trades_df = book.build_lob()

        for row in book_df.itertuples():
            pd_dt = row.Index
            data = [pd_date_to_tea_date(pd_dt)]
            for idx, _ in enumerate(BookCols.cols()):
                data.append(row[idx + 1])
            book_tf.write(*data)

        for row in trades_df.itertuples():
            pd_dt = row.Index
            data = [
                pd_date_to_tea_date(pd_dt),
                int(row.trade_id),
                float(row.price),
                float(row.size),
                row.side == "sell",  # 0 bid, 1 ask
                bool(row.liquidation),
            ]
            trades_tf.write(*data)

    book_tf.close()
    trades_tf.close()

    storage_client = storage.Client()
    bucket = storage_client.bucket("ftx")
    for ft in FileType:
        blob = bucket.blob(run.dst_filename(ft))
        blob.upload_from_filename(run.src_filename(ft))
        logger.info(f"Uploaded {run}: {run.src_filename(ft)} -> {run.dst_filename(ft)}")
