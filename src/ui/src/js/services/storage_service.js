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
            // ls is the default prefix if non is provided
            // so don't set the value
            if (localStorageService.prefix == "ls") {
                return
            }
            localStorageService.set(key, value);
        },
        get: (key, defaultValue) => {
            // ls is the default prefix if non is provided
            // so return defaults until prefix is set
            if (localStorageService.prefix == "ls") {
                return defaultValue;
            }
            const returnValue = localStorageService.get(key)

            if (returnValue == undefined || returnValue == null) {
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
        // Don't need to pull from $rootScope.user because we run changeUser after 
        // the prefix is set, so User DB settings will always have the proper prefix
        $rootScope.config.defaultHome = service.get('defaultHome', 'base.systems()');
        $rootScope.config.defaultHomePage = service.get('defaultHomePage', 'base.systems');
        $rootScope.config.defaultHomeParameters = service.get('defaultHomeParameters', {});

        let theme = service.get('currentTheme', theme);
        for (const key of Object.keys($rootScope.themes)) {
            $rootScope.themes[key] = key == theme;
        }
    };
    service["setPrefix"] = (prefix) => {
        localStorageService.setPrefix(prefix);
        service.reloadDefaults();
    };

    return service;
}