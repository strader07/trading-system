import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setOrders } from '../Redux/Reducers/OrdersReducer';
import BaseDataTable from './BaseDataTable/BaseDataTable';

const CHANNEL_NAME = 'public:ftx:orders';

const TABLE_HEADER_CELLS = [
  { id: 'symbol', label: 'Symbol' },
  { id: 'price', label: 'Price', currency: true },
  { id: 'size', label: 'Size', currency: true },
  { id: 'remaining_size', label: 'Remaining Size', currency: true },
  { id: 'filled_size', label: 'Filled Size', currency: true },
  { id: 'avg_fill_price', label: 'Avg. Fill Price', currency: true },
  { id: 'side', label: 'Side' },
  { id: 'type', label: 'Type' },
  { id: 'status', label: 'Status' },
];

function OpenOrdersTable({ orders, setOrders, latestUpdate }) {
  return (
    <BaseDataTable
      title="Open Orders"
      subtitle={null}
      headCells={TABLE_HEADER_CELLS}
      data={orders}
      setData={setOrders}
      latestUpdate={latestUpdate}
      wsChannel={CHANNEL_NAME}
    />
  );
}

function mapStateToProps({ orders }) {
  return {
    orders: orders.orders,
    latestUpdate: orders.latestUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setOrders,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(OpenOrdersTable);
