import MuiButton from '@material-ui/core/Button';
import MuiCard from '@material-ui/core/Card';
import MuiCardContent from '@material-ui/core/CardContent';
import MuiCardHeader from '@material-ui/core/CardHeader';
import MuiLightGreen from '@material-ui/core/colors/lightGreen';
import MuiDivider from '@material-ui/core/Divider';
import MuiList from '@material-ui/core/List/List';
import MuiListItem from '@material-ui/core/ListItem/ListItem';
import makeStyles from '@material-ui/core/styles/makeStyles';
import MuiTooltip from '@material-ui/core/Tooltip';
import MuiTypography from '@material-ui/core/Typography';
import clsx from 'clsx';
import React, { useState } from 'react';
import ReactInterval from 'react-interval';

function ControlSection() {
  const classes = useStyles();
  const [date, setDate] = useState(new Date());
  const [stagingStarted, setStagingStarted] = useState(false);
  const [productionStarted, setProductionStarted] = useState(false);

  const toggleStaging = () => {
    if (stagingStarted) {
      // some logic to stop staging...
      setStagingStarted(false);
    } else {
      // some logic to start staging...
      setStagingStarted(true);
    }
  };

  const toggleProduction = () => {
    if (productionStarted) {
      // some logic to stop production...
      setProductionStarted(false);
    } else {
      // some logic to start production...
      setProductionStarted(true);
    }
  };

  return (
    <MuiCard>
      <MuiCardHeader
        title="Admin Controls"
        subheader={date.toLocaleTimeString()}
      />
      <MuiCardContent>
        <MuiList>
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              JPNS01 Staging
            </MuiTypography>
            <MuiTooltip
              title={`Click to ${stagingStarted ? 'Stop' : 'Start'}`}
              placement="top"
            >
              <MuiButton onClick={toggleStaging}>
                <MuiTypography
                  className={clsx({
                    [classes.stateStarted]: stagingStarted,
                    [classes.stateStopped]: !stagingStarted,
                  })}
                >
                  {stagingStarted ? 'started' : 'stopped'}
                </MuiTypography>
              </MuiButton>
            </MuiTooltip>
          </MuiListItem>
          <MuiDivider />
          <MuiListItem>
            <MuiTypography className={classes.listItemText}>
              JPNS01 Production
            </MuiTypography>
            <MuiTooltip
              title={`Click to ${productionStarted ? 'Stop' : 'Start'}`}
              placement="top"
            >
              <MuiButton onClick={toggleProduction}>
                <MuiTypography
                  className={clsx({
                    [classes.stateStarted]: productionStarted,
                    [classes.stateStopped]: !productionStarted,
                  })}
                >
                  {productionStarted ? 'started' : 'stopped'}
                </MuiTypography>
              </MuiButton>
            </MuiTooltip>
          </MuiListItem>
        </MuiList>
      </MuiCardContent>
      <ReactInterval
        timeout={1000}
        callback={() => setDate(new Date())}
        enabled
      />
    </MuiCard>
  );
}

const useStyles = makeStyles((theme) => ({
  stateStarted: {
    color: MuiLightGreen.A700,
  },
  stateStopped: {
    color: theme.palette.error.main,
  },
  buttonsGroup: {
    '& > *': {
      margin: theme.spacing(1),
    },
  },
  listItemText: {
    marginRight: 'auto !important',
  },
}));

export default ControlSection;
