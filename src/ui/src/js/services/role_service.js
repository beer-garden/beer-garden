import _ from 'lodash';

roleService.$inject = ['$http'];

/**
 * roleService - Service for interacting with the role API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the role API.
 */
export default function roleService($http) {
  let service = {
    getRole: (roleId) => {
      return $http.get('api/v1/roles/' + roleId);
    },
    deleteRole: (roleId) => {
      return $http.delete('api/v1/roles/' + roleId);
    },
    updateRole: (roleId, operations) => {
      return $http.patch('api/v1/roles/' + roleId, {operations: operations});
    },
    getRoles: () => {
      return $http.get('api/v1/roles/');
    },
    createRole: (newRole) => {
      return $http.post('api/v1/roles/', newRole);
    },
  };

   _.assign(service, {
    addPermission: (roleId, permission) => {
      return service.updateRole(roleId, [{operation: 'add', path: '/permissions', value: permission}]);
    },
    removePermission: (roleId, permission) => {
      return service.updateRole(roleId, [{operation: 'remove', path: '/permissions', value: permission}]);
    },
    consolidatePermissions: (roles) => {

        let permissions = [];

        for (let i = 0; i < roles.length; i++){
            for (let j = 0; j < roles[i].permissions.length; j++){

                let permission = roles[i].permissions[j];
                let unmatched = true;
                for (let k = 0; k < permissions.length; k++){
                    if (permission.namespace == permissions[k].namespace || (permission.garden && permissions[k].garden)){
                        unmatched = false;
                        switch (permission.access){
                            case "ADMIN":
                                if (["MAINTAINER", "CREATE", "READ"].indexOf(permissions[k].access) > -1){
                                    permissions[k] = permission;
                                }
                                break;
                            case "MAINTAINER":
                                if (["CREATE", "READ"].indexOf(permissions[k].access) > -1){
                                    permissions[k] = permission;
                                }
                                break;
                            case "CREATE":
                                if (["READ"].indexOf(permissions[k].access) > -1){
                                    permissions[k] = permission;
                                }
                                break;
                            case "READ":
                                break;
                        }

                        break;
                    }
                }

                if (unmatched){
                    permissions.push(roles[i].permissions[j]);
                }

            }
        }

        return permissions;
    }
  });

  return service;
};
