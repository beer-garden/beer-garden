import { createStore, applyMiddleware, compose } from "redux";
import thunk from "redux-thunk";
import { createLogger } from "redux-logger";
import rootReducer from "../reducers";

const configureStore = initialState => {
  const store = createStore(
    rootReducer,
    initialState,
    compose(
      applyMiddleware(thunk, createLogger()),
      window.__REDUX_DEVTOOLS_EXTENSION__
        ? window.__REDUX_DEVTOOLS_EXTENSION__()
        : f => f,
    ),
  );

  if (module.hot) {
    // Enable Webpack hot module replacment for reducers
    module.hot.accept("../reducers", () => {
      store.replaceReducer(rootReducer);
    });
  }

  return store;
};

export default configureStore;
