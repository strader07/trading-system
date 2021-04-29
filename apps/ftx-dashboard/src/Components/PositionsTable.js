import { makeStyles } from '@material-ui/core';
import { green, red } from '@material-ui/core/colors';
import MuiTableCell from '@material-ui/core/TableCell/TableCell';
import MuiTableRow from '@material-ui/core/TableRow/TableRow';
import clsx from 'clsx';
import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setPositions } from '../Redux/Reducers/PositionsReducer';
import { normalizeToLocalString } from '../Utils/NormalizeToLocalString';
import BaseDataTable from './BaseDataTable/BaseDataTable';

const CHANNEL_NAME = 'public:ftx:positions';

const TABLE_HEADER_CELLS = [
  { id: 'symbol', label: 'Symbol' },
  { id: 'entry_price', label: 'Entry Price', currency: true },
  { id: 'net_size', label: 'Net Size', currency: true },
  { id: 'cost', label: 'Cost', currency: true },
  { id: 'avg_price', label: 'Avg. Price', currency: true },
  { id: 'side', label: 'Side' },
  { id: 'est_liq_price', label: 'Liq. Price', currency: true },
  { id: 'recent_pnl', label: 'Recent PNL', currency: true },
  { id: 'unrealized_pnl', label: 'Unrealized PNL', currency: true },
  { id: 'realized_pnl', label: 'Realized PNL', currency: true },
  { id: 'subaccount', label: 'Family' },
];

function PositionsTable({ positions, setPositions, latestUpdate }) {
  const classes = useStyles();

  return (
    <BaseDataTable
      title="Positions"
      subtitle={null}
      headCells={TABLE_HEADER_CELLS}
      data={positions}
      setData={setPositions}
      latestUpdate={latestUpdate}
      wsChannel={CHANNEL_NAME}
      mapDataToRows={positionToRowsMapping(classes)}
    />
  );
}

function positionToRowsMapping(classes) {
  return (position, pIndex) => (
    <MuiTableRow key={pIndex} hover>
      {TABLE_HEADER_CELLS.map((cell, cIndex) =>{
        let property = position[TABLE_HEADER_CELLS[cIndex].id];
        if (cell.currency) {
          property = normalizeToLocalString(property);
        }
        return cIndex === 0 ? (
          <MuiTableCell
            key={cIndex}
            component="th"
            scope="row"
            size="small"
            className={clsx({
              [classes.sellSideCell]: position.side === 'sell',
              [classes.buySideCell]: position.side === 'buy',
            })}
          >
            {property}
          </MuiTableCell>
        ) : (
          <MuiTableCell
            key={cIndex}
            align="right"
            size="small"
            className={clsx({
              [classes.sellSideCell]: position.side === 'sell',
              [classes.buySideCell]: position.side === 'buy',
            })}
          >
            {property}
          </MuiTableCell>
        )
      })}
    </MuiTableRow>
  );
}

const useStyles = makeStyles({
  sellSideCell: {
    color: red.A100,
  },
  buySideCell: {
    color: green.A100,
  },
});

function mapStateToProps({ positions }) {
  return {
    positions: positions.positions,
    latestUpdate: positions.latestUpdate,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setPositions,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(PositionsTable);
