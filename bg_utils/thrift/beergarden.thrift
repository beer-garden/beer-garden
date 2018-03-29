
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

struct QueueInfo {
  1: string name,
  2: i32 size
}

service BartenderBackend {

  // Systems
  void reloadSystem(1: string systemId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  void removeSystem(1: string systemId) throws (1:InvalidSystem ex, 2:BaseException baseEx);


  // Instances
  string initializeInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  string startInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  string stopInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  void restartInstance(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);

  void checkIn(1: string instanceId) throws (1:InvalidSystem ex, 2:BaseException baseEx);


  // Requests
  void processRequest(1:string id) throws (1:InvalidRequest ex, 2: PublishException pubEx,
    3:BaseException baseEx);


  // Queues
  QueueInfo getQueueInfo(1:string systemName, 2:string systemVersion, 3:string instanceName)
    throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

  void clearQueue(1:string queueName) throws (1:BaseException baseEx, 2:InvalidSystem invalidEx);

  void clearAllQueues() throws (1:BaseException baseEx);


  // Misc
  void ping();

  string getVersion();

  void rescanSystemDirectory() throws (1:BaseException baseEx);

}
