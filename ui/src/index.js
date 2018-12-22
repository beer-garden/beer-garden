import React from "react";
import { render } from "react-dom";
import { BrowserRouter as Router } from "react-router-dom";
import { Provider } from "react-redux";
import "typeface-roboto";
import Root from "./containers/Root";
import configureStore from "./store/configureStore";
import * as serviceWorker from "./serviceWorker";
import CssBaseline from "@material-ui/core/CssBaseline";

const store = configureStore();

render(
  <Provider store={store}>
    <Router>
      <>
        <CssBaseline />
        <Root />
      </>
    </Router>
  </Provider>,
  document.getElementById("root"),
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: http://bit.ly/CRA-PWA
serviceWorker.unregister();
