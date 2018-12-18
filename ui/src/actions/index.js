export const defaultErrorHandler = (error, dispatch, action) => {
  let newError = error;
  if (error.response && error.response.data && error.response.data.message) {
    newError = Error(error.response.data.message);
  }
  dispatch(action(newError));
};
