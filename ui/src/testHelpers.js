export const flushPromises = () =>
  new Promise(resolve => setImmediate(resolve));
