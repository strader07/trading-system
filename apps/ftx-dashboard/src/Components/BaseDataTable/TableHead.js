import makeStyles from '@material-ui/core/styles/makeStyles';
import MuiTableCell from '@material-ui/core/TableCell';
import MuiTableHead from '@material-ui/core/TableHead';
import MuiTableRow from '@material-ui/core/TableRow';
import MuiTableSortLabel from '@material-ui/core/TableSortLabel';
import React from 'react';

function TableHead({ headCells, order, orderBy, onRequestSort }) {
  const classes = useStyles();

  const createSortHandler = (property) => (event) => {
    onRequestSort(event, property);
  };

  return (
    <MuiTableHead>
      <MuiTableRow>
        {headCells.map((headCell, index) => (
          <MuiTableCell
            key={headCell.id}
            align={index ? 'right' : 'left'}
            padding="default"
            sortDirection={orderBy === headCell.id ? order : false}
          >
            <MuiTableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <span className={classes.visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </span>
              ) : null}
            </MuiTableSortLabel>
          </MuiTableCell>
        ))}
      </MuiTableRow>
    </MuiTableHead>
  );
}

const useStyles = makeStyles({
  visuallyHidden: {
    border: 0,
    clip: 'rect(0 0 0 0)',
    height: 1,
    margin: -1,
    overflow: 'hidden',
    padding: 0,
    position: 'absolute',
    top: 20,
    width: 1,
  },
});

export default TableHead;
