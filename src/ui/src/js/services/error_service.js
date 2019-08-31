import _ from 'lodash';

/**
 * errorService - Service for displaying errors
 * @return {Object}      The service
 */
export default function errorService() {
  const errorMap = {
    401: {
      common: [
        {
          problem: 'Not Logged In',
          description:
            'You\'re not logged in and anonymous users aren\'t able to view ' +
            'this data or perform this action.',
          resolution:
            'Log in using the button at the top of the screen.',
        },
      ],
    },
    403: {
      common: [
        {
          problem: 'Insufficient Permissions',
          description:
            'You don\'t have the necessary permission to view this data or ' +
            'perform this action.',
          resolution:
            'Contact your administrator and request to be given permission.',
        },
          {
            problem: 'Signature verification failed',
            description:
              'The signature of the token used in the request couldn\'t be ' +
              'validated by the server.',
            resolution:
              'Log out (if currently logged in) and log in again to generate ' +
              'a new token.',
          },
      ],
    },
    404: {
      common: [
        {
          problem: 'No plugins',
          description:
            'If no one has developed any plugins then there won\'t be ' +
            'anything here. You\'ll need to build and deploy some plugins.',
          resolution: 'Develop a Plugin',
        },
        {
          problem: 'Wrong identifier',
          description:
            'The identifiers for the resource may be off. For example, a ' +
            'system bookmark may be for an old version that\'s been removed.',
          resolution: 'Double-check that all identifiers are correct',
        },
      ],
      request: [
        {
          problem: 'Request was removed',
          description:
            'Beergarden can be set to remove requests after several ' +
            'minutes, so this request may have been removed.',
          resolution: 'Go back to the list of all requests',
        },
      ],
    },
    503: {
      common: [
        {
          problem: 'Bartender Stopped',
          description: 'Bartender is not running for some reason.',
          resolution: 'Have your system administrator start Bartender.',
        },
      ],
    },
  };

  return {
    getErrors: (specific, statusCode) => {
      if (!_.has(errorMap, statusCode)) return [];

      return _.concat(
        _.get(errorMap[statusCode], specific, []),
        _.get(errorMap[statusCode], 'common', [])
      );
    },
  };
};
