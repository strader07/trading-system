import { makeStyles } from '@material-ui/core';
import MuiAppBar from '@material-ui/core/AppBar';
import MuiIconButton from '@material-ui/core/IconButton';
import MuiToolbar from '@material-ui/core/Toolbar';
import MuiTypography from '@material-ui/core/Typography';
import MuiMenuIcon from '@material-ui/icons/Menu';
import clsx from 'clsx';
import React from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { DRAWER_WIDTH, setDrawerOpen } from '../Redux/Reducers/LayoutReducer';

function Toolbar(props) {
  const classes = useStyles();

  return (
    <MuiAppBar
      position="fixed"
      color="default"
      className={clsx(classes.appBar, {
        [classes.appBarShift]: props.drawerOpen,
      })}
    >
      <MuiToolbar>
        <MuiIconButton
          color="inherit"
          aria-label="open drawer"
          onClick={() => props.setDrawerOpen(true)}
          edge="start"
          className={clsx(classes.menuButton, {
            [classes.hide]: props.drawerOpen,
          })}
        >
          <MuiMenuIcon />
        </MuiIconButton>
        <MuiTypography variant="h6" noWrap>
          Muwazana Dashboard
        </MuiTypography>
      </MuiToolbar>
    </MuiAppBar>
  );
}

const useStyles = makeStyles((theme) => ({
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  appBarShift: {
    marginLeft: DRAWER_WIDTH,
    width: `calc(100% - ${DRAWER_WIDTH}px)`,
    transition: theme.transitions.create(['width', 'margin'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  menuButton: {
    marginRight: 36,
  },
  hide: {
    display: 'none',
  },
}));

function mapStateToProps({ layout }) {
  return {
    drawerOpen: layout.drawerOpen,
  };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setDrawerOpen,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(Toolbar);
