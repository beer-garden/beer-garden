
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

    // Namespaces
    string getLocalNamespace() throws (1:BaseException baseEx);

    set<string> getRemoteNamespaces() throws (1:BaseException baseEx);

    // Systems
    string getSystem(
        1: string nameSpace,
        2: string systemId,
        3: bool includeCommands,
    ) throws (1:BaseException baseEx);

    string querySystems(
        1: string nameSpace,
        2: map<string, string> filterParams,
        3: string orderBy,
        4: set<string> includeFields,
        5: set<string> excludeFields,
        6: bool dereferenceNested,
    ) throws (1:BaseException baseEx);

    string createSystem(
        1: string nameSpace,
        2: string system,
    ) throws (1:ConflictException ex, 2:BaseException baseEx);

    string updateSystem(
        1: string nameSpace,
        2: string systemId,
        3:string updates,
    ) throws (1:BaseException baseEx);

    void reloadSystem(
        1: string nameSpace,
        2: string systemId,
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);

    void removeSystem(
        1: string nameSpace,
        2: string systemId,
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);

    void rescanSystemDirectory(
        1: string nameSpace,
    ) throws (1:BaseException baseEx);


    // Instances
    string getInstance(
        1: string nameSpace,
        2: string instanceId,
    ) throws (1:BaseException baseEx);

    string initializeInstance(
        1: string nameSpace,
        2: string instanceId
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);

    string updateInstance(
        1: string nameSpace,
        2: string instanceId,
        3: string patch,
    ) throws (1:BaseException baseEx);

    string startInstance(
        1: string nameSpace,
        2: string instanceId,
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);

    string stopInstance(
        1: string nameSpace,
        2: string instanceId,
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);

    string updateInstanceStatus(
        1: string nameSpace,
        2: string instanceId,
        3: string newStatus,
    ) throws (1:BaseException baseEx);

    void removeInstance(
        1: string nameSpace,
        2: string instanceId,
    ) throws (1:BaseException baseEx);

    void checkIn(
        1: string nameSpace,
        2: string instanceId,
    ) throws (1:InvalidSystem ex, 2:BaseException baseEx);


    // Requests
    string getRequest(
        1: string nameSpace,
        2: string requestId,
    ) throws (1:BaseException baseEx);

    string getRequests(
        1: string nameSpace,
        2: string query,
    ) throws (1:BaseException baseEx);

    string processRequest(
        1: string nameSpace,
        2: string request,
        3: double wait_timeout,
    ) throws (1:InvalidRequest ex, 2:PublishException pubEx, 3:BaseException baseEx);

    string updateRequest(
        1: string nameSpace,
        2: string requestId,
        3: string patch,
    ) throws (1: BaseException baseEx);


    // Queues
    i32 getQueueMessageCount(
        1: string nameSpace,
        2: string queueName,
    ) throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

    string getAllQueueInfo(
        1: string nameSpace,
    ) throws (1:BaseException baseEx);

    void clearQueue(
        1: string nameSpace,
        2: string queueName,
    ) throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

    void clearAllQueues(
        1: string nameSpace
    ) throws (1:BaseException baseEx);


    // Jobs
    string getJob(
        1: string nameSpace,
        2: string jobId,
    ) throws (1:BaseException baseEx);

    string getJobs(
        1: string nameSpace,
        2: map<string, string> filterParams,
    ) throws (1:BaseException baseEx);

    string createJob(
        1: string nameSpace,
        2: string job,
    ) throws (1:BaseException baseEx);

    string pauseJob(
        1: string nameSpace,
        2: string jobName,
    ) throws (1:BaseException baseEx);

    string resumeJob(
        1: string nameSpace,
        2: string jobName,
    ) throws (1:BaseException baseEx);

    void removeJob(
        1: string nameSpace,
        2: string jobName,
    ) throws (1:BaseException baseEx);


    // Commands
    string getCommand(
        1: string nameSpace,
        2: string commandId,
    ) throws (1:BaseException baseEx);

    string getCommands(
        1: string nameSpace,
    ) throws (1:BaseException baseEx);


    // Logging
    string getPluginLogConfig(
        1: string nameSpace,
        2: string systemName,
    ) throws (1:BaseException baseEx);

    string reloadPluginLogConfig(
        1: string nameSpace,
    ) throws (1:BaseException baseEx);


    // Misc
    string getVersion(
        1: string nameSpace,
    );
}
