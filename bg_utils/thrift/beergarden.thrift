
namespace py bg_utils

exception BaseException {
  1: string message
}

exception PublishException {
  1: string message
}

exception InvalidRequest {
  1: string id,
  2: string message
}

exception InvalidSystem {
  1: string systemName,
  2: string message
}

exception ConflictException {
  1: string message,
}

service BartenderBackend {

  // Systems
  string getSystem(1: string systemId, 2: bool includeCommands) throws (1:BaseException baseEx);

  string querySystems(
      1: map<string, string> filterParams,
      2: string orderBy,
      3: set<string> includeFields,
      4: set<string> excludeFields,
      5: bool dereferenceNested
  ) throws (1:BaseException baseEx);

  string createSystem(1: string system) throws (1:ConflictException ex, 2:BaseException baseEx);

  string updateSystem(1: string systemId, 2:string updates) throws (1:BaseException baseEx);

  void reloadSystem(1: string systemId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  void removeSystem(1: string systemId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  void rescanSystemDirectory() throws (1:BaseException baseEx);


  // Instances
  string getInstance(1: string instanceId) throws (1:BaseException baseEx);

  string initializeInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  string updateInstance(1: string instanceId, 2: string patch) throws (1:BaseException baseEx);

  string startInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  string stopInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  string updateInstanceStatus(1: string instanceId, 2: string newStatus) throws (1:BaseException baseEx);

  void removeInstance(1: string instanceId) throws (1:BaseException baseEx);

  void checkIn(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);


  // Requests
  string getRequest(1: string requestId) throws (1:BaseException baseEx);

  string getRequests(1: string query) throws (1:BaseException baseEx);

  string processRequest(1: string request, 2: double wait_timeout) throws (
      1:InvalidRequest ex, 2:PublishException pubEx, 3:BaseException baseEx
  );

   string updateRequest(1: string requestId, 2: string patch) throws (1: BaseException baseEx);


  // Queues
  i32 getQueueMessageCount(1: string queueName)
    throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

  string getAllQueueInfo() throws (1:BaseException baseEx);

  void clearQueue(1: string queueName) throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

  void clearAllQueues() throws (1:BaseException baseEx);

  // Jobs
  string getJob(1: string jobId) throws (1:BaseException baseEx);

  string getJobs(1: map<string, string> filterParams) throws (1:BaseException baseEx);

  string createJob(1: string job) throws (1:BaseException baseEx);

  string pauseJob(1: string jobName) throws (1:BaseException baseEx);

  string resumeJob(1: string jobName) throws (1:BaseException baseEx);

  void removeJob(1: string jobName) throws (1:BaseException baseEx);

  // Commands
  string getCommand(1: string commandId) throws (1:BaseException baseEx);

  string getCommands() throws (1:BaseException baseEx);

  // Logging
  string getPluginLogConfig(1: string systemName) throws (1:BaseException baseEx);

  string reloadPluginLogConfig() throws (1:BaseException baseEx);

  // Misc
  string getVersion();
}
