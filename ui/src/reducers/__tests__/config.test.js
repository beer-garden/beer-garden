import configReducer from '../config';
import * as types from '../../constants/ActionTypes';

describe('config reducer', () => {
  it('should return the initial state', () => {
    expect(configReducer(undefined, {})).toEqual({
      config: {},
      configLoading: false,
      configError: null,
    });
  });

  it('should handle FETCH_CONFIG_BEGIN', () => {
    expect(
      configReducer(
        { config: {}, configError: 'someError' },
        {
          type: types.FETCH_CONFIG_BEGIN,
        }
      )
    ).toEqual({
      config: {},
      configLoading: true,
      configError: 'someError',
    });
  });

  it('should handle FETCH_CONFIG_SUCCESS', () => {
    expect(
      configReducer(
        { config: {}, configError: 'someError', configLoading: true },
        {
          type: types.FETCH_CONFIG_SUCCESS,
          payload: { config: 'configPayload' },
        }
      )
    ).toEqual({
      config: 'configPayload',
      configLoading: false,
      configError: null,
    });
  });

  it('should handle FETCH_CONFIG_FAILURE', () => {
    expect(
      configReducer(
        { config: {}, configError: null, configLoading: true },
        {
          type: types.FETCH_CONFIG_FAILURE,
          payload: { error: new Error('some error') },
        }
      )
    ).toEqual({
      config: {},
      configLoading: false,
      configError: new Error('some error'),
    });
  });
});
