import React from 'react';
import { render } from 'react-dom';
import { BrowserRouter as Router } from 'react-router-dom';
import { Provider } from 'react-redux';
import 'typeface-roboto';
import Root from './containers/Root';
import configureStore from './store/configureStore';
import * as serviceWorker from './serviceWorker';
import CssBaseline from '@material-ui/core/CssBaseline';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core';

const store = configureStore();
const defaultTheme = createMuiTheme({ typography: { useNextVariants: true } });
const darkTheme = createMuiTheme({
  typography: { useNextVariants: true },
  palette: { type: 'dark' },
});

render(
  <Provider store={store}>
    <MuiThemeProvider theme={defaultTheme}>
      <Router>
        <CssBaseline>
          <Root />
        </CssBaseline>
      </Router>
    </MuiThemeProvider>
  </Provider>,
  document.getElementById('root')
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();
