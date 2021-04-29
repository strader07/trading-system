import MuiCard from '@material-ui/core/Card';
import MuiCardActions from '@material-ui/core/CardActions';
import MuiCardContent from '@material-ui/core/CardContent';
import MuiFormControlLabel from '@material-ui/core/FormControlLabel';
import { makeStyles } from '@material-ui/core/styles';
import MuiSwitch from '@material-ui/core/Switch';
import MuiTable from '@material-ui/core/Table';
import MuiTableBody from '@material-ui/core/TableBody';
import MuiTableCell from '@material-ui/core/TableCell/TableCell';
import MuiTablePagination from '@material-ui/core/TablePagination';
import MuiTableRow from '@material-ui/core/TableRow/TableRow';
import React, { useContext, useEffect, useState } from 'react';
import { normalizeToLocalString } from '../../Utils/NormalizeToLocalString';
import SocketContext from '../../Utils/SocketContext';
import {
  filterTableRows,
  getSorting,
  rowsPerPageOptions,
  stableSort,
} from '../../Utils/tableUtils';
import TableCardHeader from './TableCardHeader';
import TableHead from './TableHead';

function BaseDataTable({
  title,
  subtitle,
  headCells,
  data,
  setData,
  latestUpdate,
  wsChannel,
  mapDataToRows = null,
}) {
  const classes = useStyles();
  const [order, setOrder] = useState('asc');
  const [orderBy, setOrderBy] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [viewAll, setViewAll] = useState(false);
  const [filterText, setFilterText] = useState('');
  const { socket } = useContext(SocketContext);

  useEffect(() => {
    socket.on(wsChannel, setData);
    return () => {
      socket.remove(wsChannel, setData);
    };
  }, [setData, socket, wsChannel]);

  const handleRequestSort = (_, property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (_, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (ev) => {
    setRowsPerPage(parseInt(ev.target.value, 10));
    setPage(0);
  };

  const handleViewAllChange = (ev) => {
    setViewAll(ev.target.checked);
    setRowsPerPage(ev.target.checked ? data.length : 5);
  };

  const filteredRows = filterTableRows(data, filterText);

  const sortedRows = stableSort(filteredRows, getSorting(order, orderBy));

  const rows = sortedRows.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage,
  );

  const dataToRowMapping = mapDataToRows || defaultDataToRowsMapping(headCells);

  return (
    <MuiCard className={classes.root}>
      <TableCardHeader
        title={title}
        subheader={subtitle}
        filterText={filterText}
        onFilterTextChange={setFilterText}
      />
      <MuiCardContent>
        <MuiTable className={classes.table} size="small">
          <caption>Latest Update: {latestUpdate}</caption>
          <TableHead
            headCells={headCells}
            classes={classes}
            order={order}
            orderBy={orderBy}
            onRequestSort={handleRequestSort}
          />
          <MuiTableBody>{rows.map(dataToRowMapping)}</MuiTableBody>
        </MuiTable>
      </MuiCardContent>
      <MuiCardActions>
        <MuiFormControlLabel
          control={
            <MuiSwitch
              checked={viewAll}
              onChange={handleViewAllChange}
              value="viewAll"
              color="primary"
            />
          }
          label="View All"
          labelPlacement="start"
        />
        <span className={classes.spacer} />
        {!viewAll && (
          <MuiTablePagination
            rowsPerPageOptions={rowsPerPageOptions(filteredRows.length)}
            component="div"
            count={filteredRows.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onChangePage={handleChangePage}
            onChangeRowsPerPage={handleChangeRowsPerPage}
          />
        )}
      </MuiCardActions>
    </MuiCard>
  );
}

function defaultDataToRowsMapping(headCells) {
  return (obj, objIndex) => (
    <MuiTableRow key={objIndex} hover>
      {headCells.map((cell, cellIndex) => {
        let property = obj[headCells[cellIndex].id];
        if (cell.currency) {
          property = normalizeToLocalString(property);
        }
        return cellIndex === 0 ? (
          <MuiTableCell key={cellIndex} component="th" scope="row" size="small">
            {property}
          </MuiTableCell>
        ) : (
          <MuiTableCell key={cellIndex} align="right" size="small">
            {property}
          </MuiTableCell>
        );
      })}
    </MuiTableRow>
  );
}

const useStyles = makeStyles({
  root: {
    minWidth: '100%',
    overflowX: 'auto',
  },
  table: {
    minWidth: 650,
  },
  spacer: {
    flex: 1,
  },
});

export default BaseDataTable;
