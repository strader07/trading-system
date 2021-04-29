import MuiDivider from '@material-ui/core/Divider';
import MuiDrawer from '@material-ui/core/Drawer';
import MuiIconButton from '@material-ui/core/IconButton';
import MuiList from '@material-ui/core/List';
import MuiListItem from '@material-ui/core/ListItem';
import MuiListItemIcon from '@material-ui/core/ListItemIcon';
import MuiListItemText from '@material-ui/core/ListItemText';
import { makeStyles } from '@material-ui/core/styles';
import MuiTooltip from '@material-ui/core/Tooltip';
import MuiAssignmentIcon from '@material-ui/icons/Assignment';
import MuiChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import MuiTimelineIcon from '@material-ui/icons/Timeline';
import clsx from 'clsx';
import React from 'react';
import { connect } from 'react-redux';
import { Link } from 'react-router-dom';
import { bindActionCreators } from 'redux';
import { DRAWER_WIDTH, setDrawerOpen } from '../Redux/Reducers/LayoutReducer';

function SideMenu(props) {
  const classes = useStyles();

  return (
    <MuiDrawer
      variant="permanent"
      className={clsx(classes.drawer, {
        [classes.drawerOpen]: props.drawerOpen,
        [classes.drawerClose]: !props.drawerOpen,
      })}
      classes={{
        paper: clsx({
          [classes.drawerOpen]: props.drawerOpen,
          [classes.drawerClose]: !props.drawerOpen,
        }),
      }}
    >
      <div className={classes.toolbar}>
        <MuiIconButton onClick={() => props.setDrawerOpen(false)}>
          <MuiChevronLeftIcon />
        </MuiIconButton>
      </div>
      <MuiDivider />
      <MuiList>
        <MuiListItem component={Link} to="/summaries" button>
          <MuiTooltip title="Summaries">
            <MuiListItemIcon>
              <MuiAssignmentIcon />
            </MuiListItemIcon>
          </MuiTooltip>
          <MuiListItemText>Summaries</MuiListItemText>
        </MuiListItem>
        <MuiDivider />
        <MuiListItem component={Link} to="/trading-monitor" button>
          <MuiTooltip title="Trading Monitor">
            <MuiListItemIcon>
              <MuiTimelineIcon />
            </MuiListItemIcon>
          </MuiTooltip>
          <MuiListItemText>Trading Monitor</MuiListItemText>
        </MuiListItem>
      </MuiList>
      <MuiDivider />
    </MuiDrawer>
  );
}

const useStyles = makeStyles((theme) => ({
  drawer: {
    width: DRAWER_WIDTH,
    flexShrink: 0,
    whiteSpace: 'nowrap',
  },
  drawerOpen: {
    width: DRAWER_WIDTH,
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawerClose: {
    transition: theme.transitions.create('width', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: 'hidden',
    width: 0,
    [theme.breakpoints.up('sm')]: {
      width: theme.spacing(7) + 1,
    },
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: theme.spacing(0, 1),
    ...theme.mixins.toolbar,
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

export default connect(mapStateToProps, mapDispatchToProps)(SideMenu);
