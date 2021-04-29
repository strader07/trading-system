function descSort(a, b, orderBy) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

export function stableSort(array, cmp) {
  const stabilizedThis = array.map((el, index) => [el, index]);
  stabilizedThis.sort((a, b) => {
    const order = cmp(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

export function getSorting(order, orderBy) {
  return order === 'desc'
    ? (a, b) => descSort(a, b, orderBy)
    : (a, b) => -descSort(a, b, orderBy);
}

export function rowsPerPageOptions(rowsLength) {
  const opts = [5];
  for (const opt of [10, 25, 50, 75, 100]) {
    if (rowsLength >= opt) {
      opts.push(opt);
    }
  }
  if (rowsLength > opts[opts.length - 1]) {
    opts.push(rowsLength);
  }
  return opts;
}

export function filterTableRows(rows, filterText) {
  if (!filterText || !`${filterText}`.length) {
    return rows;
  }
  return rows
    .filter((row) => {
      for (const v of Object.values(row)) {
        if (`${v}`.toLowerCase().includes(filterText.toLowerCase())) {
          return row;
        }
      }
      return null;
    })
    .filter((w) => w !== null);
}
