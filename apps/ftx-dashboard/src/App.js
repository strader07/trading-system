import MuiContainer from '@material-ui/core/Container';
import MuiCssBaseline from '@material-ui/core/CssBaseline/CssBaseline';
import MuiGrid from '@material-ui/core/Grid';
import makeStyles from '@material-ui/core/styles/makeStyles';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import AccountSummary from './Components/AccountSummary';
import ControlSection from './Components/ControlSection';
import Footer from './Components/Footer';
import Router from './Components/Router';
import SideMenu from './Components/SideMenu';
import Toolbar from './Components/Toolbar';
import Socket from './Utils/Socket';
import SocketContext from './Utils/SocketContext';

function App() {
  const classes = useStyles();
  const socket = new Socket(
    new WebSocket('wss://dashboard.ftx.dev.muwazana.com/ws'),
  );

  return (
    <SocketContext.Provider value={{ socket }}>
      <BrowserRouter>
        <div className={classes.root}>
          <MuiCssBaseline />
          <Toolbar />
          <SideMenu />
          <main className={classes.content}>
            <MuiGrid container className={classes.root}>
              <MuiGrid item xs={12}>
                <MuiGrid container>
                  <MuiGrid item xs={12} md={6} className={classes.column}>
                    <MuiContainer
                      className={classes.container}
                      maxWidth={false}
                    >
                      <AccountSummary />
                    </MuiContainer>
                  </MuiGrid>
                  <MuiGrid item xs={12} md={4} className={classes.column}>
                    <MuiContainer
                      className={classes.container}
                      maxWidth={false}
                    >
                      <ControlSection />
                    </MuiContainer>
                  </MuiGrid>
                </MuiGrid>
              </MuiGrid>
              <MuiGrid item xs={12}>
                <Router />
                <MuiGrid container>
                  <MuiGrid item xs={12} className={classes.column}>
                    <MuiContainer
                      className={classes.container}
                      maxWidth={false}
                    >
                      <Footer />
                    </MuiContainer>
                  </MuiGrid>
                </MuiGrid>
              </MuiGrid>
            </MuiGrid>
          </main>
        </div>
      </BrowserRouter>
    </SocketContext.Provider>
  );
}

const useStyles = makeStyles((theme) => ({
  root: {
    background: theme.palette.background.default,
    flex: 1,
  },
  content: {
    flexGrow: 1,
    paddingTop: theme.spacing(10),
    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing(8),
    },
  },
  container: {
    [theme.breakpoints.down('sm')]: {
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
    },
  },
  column: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
}));

export default App;
