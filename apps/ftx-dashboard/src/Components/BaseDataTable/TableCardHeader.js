import MuiCardHeader from '@material-ui/core/CardHeader';
import MuiFormControl from '@material-ui/core/FormControl';
import MuiIconButton from '@material-ui/core/IconButton';
import MuiInput from '@material-ui/core/Input';
import MuiInputAdornment from '@material-ui/core/InputAdornment';
import MuiInputLabel from '@material-ui/core/InputLabel';
import MuiClearIcon from '@material-ui/icons/Clear';
import React from 'react';

function TableCardHeader({
  title,
  subheader = null,
  filterText,
  onFilterTextChange,
}) {
  const handleFilterChange = (ev) => {
    onFilterTextChange(ev.target.value);
  };

  const handleClearButtonClick = () => {
    onFilterTextChange('');
  };

  const normalizedTitle = title.replace(/\s/g, '');

  return (
    <MuiCardHeader
      title={title}
      subheader={subheader && <small>{subheader}</small>}
      action={
        <MuiFormControl>
          <MuiInputLabel htmlFor={`${normalizedTitle}-table-filter`}>
            Filter
          </MuiInputLabel>
          <MuiInput
            id={`${normalizedTitle}-table-filter`}
            type="text"
            value={filterText}
            onChange={handleFilterChange}
            endAdornment={
              <MuiInputAdornment position="end">
                <MuiIconButton onClick={handleClearButtonClick}>
                  <MuiClearIcon />
                </MuiIconButton>
              </MuiInputAdornment>
            }
          />
        </MuiFormControl>
      }
    />
  );
}

export default TableCardHeader;
