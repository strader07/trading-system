import MuiContainer from '@material-ui/core/Container/Container';
import MuiGrid from '@material-ui/core/Grid/Grid';
import makeStyles from '@material-ui/core/styles/makeStyles';
import React from 'react';
import MMStatsTable from '../Components/MMStatsTable';
import OpenOrdersTable from '../Components/OpenOrdersTable';
import PositionsTable from '../Components/PositionsTable';

function TradingMonitor() {
  const classes = useStyles();

  return (
    <MuiGrid container>
      <MuiGrid item xs={12} className={classes.column}>
        <MuiContainer className={classes.container} maxWidth={false}>
          <MMStatsTable />
        </MuiContainer>
      </MuiGrid>
      <MuiGrid item xs={12} className={classes.column}>
        <MuiContainer className={classes.container} maxWidth={false}>
          <PositionsTable />
        </MuiContainer>
      </MuiGrid>
      <MuiGrid item xs={12} className={classes.column}>
        <MuiContainer className={classes.container} maxWidth={false}>
          <OpenOrdersTable />
        </MuiContainer>
      </MuiGrid>
    </MuiGrid>
  );
}

const useStyles = makeStyles((theme) => ({
  column: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  container: {
    [theme.breakpoints.down('sm')]: {
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
    },
  },
}));

export default TradingMonitor;
