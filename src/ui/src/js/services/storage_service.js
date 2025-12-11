storageService.$inject = ['$rootScope', 'localStorageService'];

/**
 * storageService - Service for getting data from browser storage.
 * @param  {$rootScope} $rootScope       Angular's $rootScope object.
 * @param  {Object} localStorageService  Storage service
 * @return {Object}                      Object for interacting with the storage API.
 */
export default function storageService($rootScope, localStorageService) {
    const service = {        
        set: (key, value) => {
            if (localStorageService.prefix == "ls"){
                return
            }
            localStorageService.set(key, value);
        },
        get: (key, defaultValue) => {
            if (localStorageService.prefix == "ls"){
                return defaultValue;
            }
            const returnValue = localStorageService.get(key)

            if (returnValue == undefined || returnValue == null){
                localStorageService.set(key, defaultValue);
                return defaultValue;
            }

            return returnValue;
        },
        remove: (key) => {
            localStorageService.remove(key);
        },
    };

    service["reloadDefaults"] = () => {
        $rootScope.config.defaultHome = service.get('defaultHome', 'base.systems()');
        $rootScope.config.defaultHomePage = service.get('defaultHomePage', 'base.systems');
        $rootScope.config.defaultHomeParameters = service.get('defaultHomeParameters', {});   
    };
    service["setPrefix"] = (prefix) => {
        localStorageService.setPrefix(prefix);  
        service.reloadDefaults();
    };

    return service;
}