import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {setMMStats} from '../Redux/Reducers/MMStatsReducer';
import BaseDataTable from './BaseDataTable/BaseDataTable';

const CHANNEL_NAME = 'public:ftx:mmstats';

const TABLE_HEADER_CELLS = [
  {id: 'date', label: 'Trade Date'},
  {id: 'market', label: 'Market'},
  {id: 'today_deep_pct', label: 'Today Deep %', currency: true},
  {id: 'today_bbo_pct', label: 'Today BBO %', currency: true},
  {id: 'month_deep_pct', label: 'Month Deep %', currency: true},
  {id: 'month_bbo_pct', label: 'Month BBO %', currency: true},
  {id: 'ui_deep_target', label: 'Daily Deep Target', currency: true},
  {id: 'ui_bbo_target', label: 'Daily BBO Target', currency: true},
  {id: 'subaccount', label: 'Subaccount'},
];

function MMStatsTable({mmstats, setMMStats, latestUpdate}) {
  return (
    <BaseDataTable
  title = 'MM Stats'
  subtitle = 'Note: trade date starts at 00:00 GMT'
  headCells = {TABLE_HEADER_CELLS} data = {mmstats} setData = {
      setMMStats} latestUpdate = {latestUpdate} wsChannel = {
    CHANNEL_NAME
  } />
  );
}

function mapStateToProps({ mmstats }) {
  return {
    mmstats: mmstats.mmstats,
    latestUpdate: mmstats.latestUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setMMStats,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(MMStatsTable);
