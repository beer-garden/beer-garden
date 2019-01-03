import { userLoginFailure } from "./auth";

export const defaultErrorHandler = (error, dispatch, action) => {
  let newError = error;
  if (error.response) {
    if (error.response.data && error.response.data.message) {
      newError = Error(error.response.data.message);
    }

    // This means we though we were logged in successfully, and tried
    // to hit a route we shouldn't have, which means we need to clean up
    // the user state which is done through a userLoginFailure.
    if (error.response.status === 401) {
      dispatch(userLoginFailure(newError));
      if (action === userLoginFailure) {
        action = null;
      }
    }
  }

  if (action) {
    dispatch(action(newError));
  }
};
