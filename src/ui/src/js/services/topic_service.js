import _ from 'lodash';

topicService.$inject = ['$q', '$http', '$interval'];

/**
 * topicService - Service for accessing the Topic API.
 * @param  {Object} $q                Angular $q object.
 * @param  {Object} $http             Angular $http object.
 * @param  {Object} $interval         Angular $interval object.
 * @return {Object}                   An Object for interacting with the Topic API.
 */
export default function topicService($q, $http, $interval) {

  const service = {
    getTopics: (data) => {
      return $http.get('api/v1/topics', {params: data});
    },
    getTopic: (id) => {
      return $http.get('api/v1/topics/' + id);
    },
    getTopicName: (name) => {
        return $http.get('api/v1/topics/name/' + name);
    },
    createTopic: (newTopic) => {
      return $http.post('api/v1/topics/', newTopic);
    },
    deleteTopic: (topicId) => {
      return $http.delete('api/v1/topics/' + topicId);
    },
    addSubscriber: (topicId, subscriber) => {
      return $http.patch('api/v1/topics/' + topicId, {
        operation: 'add',
        path: '',
        value: subscriber,
      });
    },
    removeSubscriber: (topicId, subscriber) => {
      return $http.patch('api/v1/topics/' + topicId, {
        operation: 'remove',
        path: '',
        value: subscriber,
      });
    },
    syncTopics: () => {
      return $http.patch('api/v1/topics', {
        operation: 'sync_all_topics',
      });
    },
    resetCount: (topicId, subscriber) => {
      return $http.patch('api/v1/topics/' + topicId, {
        operation: 'reset_count',
        path: '',
        value: subscriber,
      });
    }
  };

  return service;
}
