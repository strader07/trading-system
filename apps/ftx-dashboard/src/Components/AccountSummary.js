import MuiCard from '@material-ui/core/Card';
import MuiCardContent from '@material-ui/core/CardContent';
import MuiCardHeader from '@material-ui/core/CardHeader';
import MuiDivider from '@material-ui/core/Divider';
import MuiList from '@material-ui/core/List';
import MuiListItem from '@material-ui/core/ListItem';
import makeStyles from '@material-ui/core/styles/makeStyles';
import MuiTypography from '@material-ui/core/Typography';
import React, { useContext, useEffect } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { setAccountInfo } from '../Redux/Reducers/AccountInfoReducer';
import { normalizeToLocalString } from '../Utils/NormalizeToLocalString';
import SocketContext from '../Utils/SocketContext';

const CHANNEL_NAME = 'public:ftx:accountinfo';

function AccountSummary(props) {
  const classes = useStyles();
  const { socket } = useContext(SocketContext);

  useEffect(() => {
    socket.on(CHANNEL_NAME, props.setAccountInfo);
    return () => {
      socket.remove(CHANNEL_NAME, props.setAccountInfo);
    };
  }, [props.setAccountInfo, socket]);

  return (
    <MuiCard>
      <MuiCardHeader
        title={
          <MuiTypography variant="h5" display="inline">
            Account Summary
          </MuiTypography>
        }
      />
      <MuiCardContent>
        <MuiList>
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              Total Account Value
            </MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.account_value)}
            </MuiTypography>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              Total Position Size
            </MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.position_size)}
            </MuiTypography>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              Collateral
            </MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.collateral)}
            </MuiTypography>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              Free Collateral
            </MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.free_collateral)}
            </MuiTypography>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              Today PNL
            </MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.today_pnl)}
            </MuiTypography>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>PNL</MuiTypography>
            <MuiTypography>
              ${normalizeToLocalString(props.info.pnl)}
            </MuiTypography>
          </MuiListItem>
        </MuiList>
      </MuiCardContent>
    </MuiCard>
  );
}

const useStyles = makeStyles(() => ({
  listItemText: {
    marginRight: 'auto !important',
  },
}));

function mapStateToProps({ account }) {
  return { info: account.info };
}

function mapDispatchToProps(dispatch) {
  return bindActionCreators(
    {
      setAccountInfo,
    },
    dispatch,
  );
}

export default connect(mapStateToProps, mapDispatchToProps)(AccountSummary);
