import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setWallets } from '../Redux/Reducers/WalletsReducer';
import BaseDataTable from './BaseDataTable/BaseDataTable';

const CHANNEL_NAME = 'public:ftx:wallets';

const TABLE_HEADER_CELLS = [
  { id: 'coin', label: 'Coin' },
  { id: 'free', label: 'Free', currency: true },
  { id: 'total', label: 'Total', currency: true },
  { id: 'usd_value', label: 'USD Value', currency: true },
  { id: 'subaccount', label: 'Subaccount' },
];

function WalletsTable({ wallets, setWallets, latestUpdate }) {
  return (
    <BaseDataTable
      title="Wallets"
      subtitle={null}
      headCells={TABLE_HEADER_CELLS}
      data={wallets}
      setData={setWallets}
      latestUpdate={latestUpdate}
      wsChannel={CHANNEL_NAME}
    />
  );
}

function mapStateToProps({ wallets }) {
  return {
    wallets: wallets.wallets,
    latestUpdate: wallets.latestUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setWallets,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(WalletsTable);
