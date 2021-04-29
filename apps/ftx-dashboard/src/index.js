import { ThemeProvider } from '@material-ui/core';
import { cyan } from '@material-ui/core/colors';
import createMuiTheme from '@material-ui/core/styles/createMuiTheme';
import React from 'react';
import ReactDOM from 'react-dom';
import { Provider as ReduxProvider } from 'react-redux';
import App from './App';
import store from './Redux/Store';
import * as serviceWorker from './serviceWorker';

const MUI_THEME = createMuiTheme({
  palette: { type: 'dark', primary: cyan },
});

ReactDOM.render(
  <ReduxProvider store={store}>
    <ThemeProvider theme={MUI_THEME}>
      <App />
    </ThemeProvider>
  </ReduxProvider>,
  document.getElementById('root'),
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
