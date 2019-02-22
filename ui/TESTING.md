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

Make sure your tests describe _what_ the component does, not _how_ it does it
in your `test('calls')`

## Running the tests

To run the tests:

    npm install
    npm test

To generate coverage:

npm test -- --coverage # (notice the middle '--')

## Notes

### HOC

If you are testing a [High Order Component (HOC)](https://reactjs.org/docs/higher-order-components.html)
then you should be exporting the lower component as a non default export. For
example, if you have the following redux and/or material-ui connected
component:

    // raw, unconnected component for testing
    export function HeaderLinks(props) {
        ...
        return (
            <Grid container item className={classes.nav}>
                <HeaderMenu renderMenuLinks={() => menuLinks} />
            </Grid>
        )
    }

    // connected (or any other sort of HOC component) for use in App.
    export default connect(mapStateToProps)(compose(withStyles(styles), withWidth())(HeaderLinks));

This results in imports in the tests looking like:

    import { HeaderLinks } from '../HeaderLinks'

and imports in the application looking like:

    import HeaderLinks from './components/HeaderLinks'
    
### Testing async functions

In jest, if we have functions that involve kicking off a promise chain, the way
to test that would be to import the `flushPromises` function in the `testHelper.js`
then make your test function `async` and then `await` the `flushPromises` call. 
For example:

```ecmascript 6
import { flushPromises } from './src/testHelpers'

it('should return the correct thing', async () => {
  const { component } = setup();
  component.instance().thingThatKicksOffPromiseChain();
  await flushPromises();
  expect(component.state().value).toEqual(false);
})
```
