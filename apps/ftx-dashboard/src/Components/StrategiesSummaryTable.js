import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setStrategies } from '../Redux/Reducers/StrategiesReducer';
import BaseDataTable from './BaseDataTable/BaseDataTable';

const CHANNEL_NAME = 'public:ftx:accountinfo';

const TABLE_HEADER_CELLS = [
  { id: 'subaccount', label: 'Subaccount' },
  { id: 'account_value', label: 'Account Value', currency: true },
  { id: 'position_size', label: 'Position Size', currency: true },
  { id: 'collateral', label: 'Collateral', currency: true },
  { id: 'free_collateral', label: 'Free Collateral', currency: true },
  { id: 'today_pnl', label: 'Today PNL', currency: true },
  { id: 'pnl', label: 'PNL', currency: true },
];

function StrategiesSummaryTable({ strategies, setStrategies, latestUpdate }) {
  return (
    <BaseDataTable
      title="Strategies Summary"
      subtitle={null}
      headCells={TABLE_HEADER_CELLS}
      data={strategies}
      setData={setStrategies}
      latestUpdate={latestUpdate}
      wsChannel={CHANNEL_NAME}
    />
  );
}

function mapStateToProps({ strategies }) {
  return {
    strategies: strategies.strategies,
    latestUpdate: strategies.latestUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setStrategies,
    },
    dispatch,
  );
}

export default connect(
  mapStateToProps,
  mapDispatchToProps,
)(StrategiesSummaryTable);
