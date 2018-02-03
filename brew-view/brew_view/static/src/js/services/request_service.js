
requestService.$inject = ['$q', '$http', '$timeout'];
export default function requestService($q, $http, $timeout) {
  var RequestService = {};

  RequestService.complete_statuses = ['SUCCESS', 'ERROR', 'CANCELED'];

  RequestService.errorMap = {
    'empty': {
      'solutions' : [
        {
          problem: 'Request was removed',
          description: 'INFO-type requests are removed after several minutes',
          resolution:  'Go back to the list of all requests'
        },
        {
          problem: 'ID is Incorrect',
          description: 'The ID Specified is incorrect. It does not refer to a valid request',
          resolution:  'Go back to the list of all requests'
        }
      ]
    }
  }

  RequestService.getRequests = function(data) {
    return $http.get('api/v1/requests', {params: data});
  };

  RequestService.getRequest = function(id) {
    return $http.get('api/v1/requests/' + id);
  };

  RequestService.createRequest = function(request) {
    return $http.post('api/v1/requests', request);
  };

  RequestService.createRequestWait = function(request) {
    var deferred = $q.defer();
    var timeoutRequest;

    // Create our checker function and immediately invoke it
    var checkForCompletion = function(id) {
      RequestService.getRequest(id).then(
        function(response) {
          if(RequestService.complete_statuses.indexOf(response.data.status) == -1) {
            // If request isn't done then we need to keep checking
            timeoutRequest = $timeout(function() {
              checkForCompletion(id);
            }, 500);
          } else {
            // All done! Resolve the original promise with the response
            response.data = JSON.parse(response.data.output);
            deferred.resolve(response);
          }
      });
    };

    RequestService.createRequest(request).then(
      function(response) {
        checkForCompletion(response.data.id);
      }
    );

    return deferred.promise;
  };

  RequestService.getCommandId = function(request) {
    var promise = $http.get('api/v1/systems', {params: {name: request.system, include_commands: true} })
      .then(function(response) {
        var commandId = null;
        if(response.data.length > 0) {
          for(var i = 0; i < response.data[0].commands.length; i++) {
            var command = response.data[0].commands[i]
            if(command.name === request.command) {
              commandId = command.id;
              break;
            }
          }
        }
        return commandId;
      });
    return promise;
  };

  return RequestService;
};
