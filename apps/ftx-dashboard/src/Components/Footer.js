import MuiAppBar from '@material-ui/core/AppBar/AppBar';
import makeStyles from '@material-ui/core/styles/makeStyles';
import MuiToolbar from '@material-ui/core/Toolbar/Toolbar';
import MuiTypography from '@material-ui/core/Typography/Typography';
import React from 'react';

function Footer() {
  const classes = useStyles();

  return (
    <MuiAppBar position="static" color="default">
      <MuiToolbar className={classes.toolbar}>
        <MuiTypography align="center">
          &copy; {new Date().getFullYear()} Muwazana.
        </MuiTypography>
      </MuiToolbar>
    </MuiAppBar>
  );
}

const useStyles = makeStyles(() => ({
  toolbar: {
    justifyContent: 'center',
  },
}));

export default Footer;
