# UI Testing

This document describes the thought process and best practices for testing
the Beer Garden UI. It is designed to guide developers towards writing the
best possible tests for Beer Garden and new contributors to know the
expectations for adding new functionality to the UI.

## Tools

To test the UI, we use the following tools:

- [Jest](https://jestjs.io/)
- [Enzyme](https://airbnb.io/enzyme/)
- [Material-UI](https://material-ui.com/guides/testing/)

## Conventions

Each folder under `src/` should have a corresponding `__tests__` folder
from which you should write the tests. The reason we do this is to keep
our tests close to the code we are testing so that our imports don't have
to be creazy.

Tests should _never_ rely on an external service. No exceptions.

If you are adding/modifying functionality of the request form page, you must
generate a new snapshot and include it in the PR.

Use the `setup()` helper instead of `beforeEach()`. This helps us read your
test more easily and in isolation.

Write a smoke test first (i.e. does the component render), then test behavior.

Make sure your tests describe _what_ the component does, not _how_ it does it in your `test('calls')`

## Running the tests

To run the tests:

    npm install
    npm test

To generate coverage:
  
 npm test -- --coverage # (notice the middle '--')

## Notes

When testing a component that uses `withStyles` you will almost certainly
need to `.dive()` on any shallow copies you make. This is because you are
creating a [High Order Component (HOC)](https://reactjs.org/docs/higher-order-components.html)
