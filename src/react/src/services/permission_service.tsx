import React, { PropsWithChildren, useCallback, useState, createContext } from "react";
import { User, Role} from "../models/brewtils-types";

//context


const LOCAL_STORAGE_KEY_USER = "__permissionUser";
const LOCAL_STORAGE_KEY_AUTH_ENABLED = "__permissionAuthEnabled";

export interface PermissionAuthContext {
    setUser: (user: User) => void;
    setAuthEnabled: (authEnabled: boolean) => void;
    isAuthorized: (permission: string, check: PermissionCheck) => Promise<boolean>;
    isLoading: boolean;
}

export interface PermissionCheck {
    global?: boolean;
    gardenName?: string;
    namespace?: string;
    system_name?: string;
    system_version?: string;
    command_name?:string;
    instance_name?:string;
}

const noUser = (): never => {
    throw new Error("You didn't set User!");
};

const PermissionContext = createContext<PermissionAuthContext>({
    setUser: noUser,
    isAuthorized: noUser,
    setAuthEnabled: noUser,
    isLoading: false,
});

const PermissionProvider = ({
    children
}: PropsWithChildren) => {
    const [isLoading, setIsLoading] = useState<boolean>(false);

    const updateUser = (newUser: User | undefined) => {
        if (newUser === undefined){
            localStorage.removeItem(LOCAL_STORAGE_KEY_USER);
        } else {
            localStorage.setItem(LOCAL_STORAGE_KEY_USER, JSON.stringify(newUser));
        }
    };

    const setAuthEnabled = (authEnabled: boolean) => {
        localStorage.setItem(LOCAL_STORAGE_KEY_AUTH_ENABLED, authEnabled ? "true" : "false");
    }
    
    const isAuthorized = useCallback(async (permission: string, check: PermissionCheck): Promise<boolean> => {
        
        if (localStorage.getItem(LOCAL_STORAGE_KEY_AUTH_ENABLED) !== null && localStorage.getItem(LOCAL_STORAGE_KEY_AUTH_ENABLED) === "false"){
            return true;
        }
        let hasAuthorization: boolean = false;
        const storedUser = localStorage.getItem(LOCAL_STORAGE_KEY_USER) ? JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY_USER) ?? "") : undefined;

        setIsLoading(true)
        if(storedUser) {
            hasAuthorization = await CheckUserHasRoles(storedUser, permission, check)
        }
        setIsLoading(false)

        return hasAuthorization
    }, []);

    const GetPermissions = (permission: string): Array<string> => {
            switch (permission) {
                case "READ_ONLY":
                  return ["READ_ONLY", "OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"];
                case "OPERATOR":
                    return ["OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"];
                case "PLUGIN_ADMIN":
                    return ["PLUGIN_ADMIN", "GARDEN_ADMIN"];
                case "GARDEN_ADMIN":
                    return ["GARDEN_ADMIN"];
                default:
                  return [];
              }
        }

    const CheckRole = (role: Role, permission: string, check: PermissionCheck) : boolean => {
        if (role.permission === undefined || role.permission === null || !GetPermissions(permission).includes(role.permission)){
            return false;
        }
        return true;
    }

    const CheckUserHasRoles = async (storedUser: User, permission: string, check: PermissionCheck): Promise<boolean> => {

        if (storedUser.localRoles?.some((role)=> CheckRole(role, permission, check))){
            return true;
        }

        if (storedUser.upstreamRoles?.some((role)=> CheckRole(role, permission, check))){
            return true;
        }
        
        return false;
    };

    return <PermissionContext.Provider value={{
        setUser: updateUser,
        isAuthorized,
        setAuthEnabled,
        isLoading
    }}>{children}
    </PermissionContext.Provider>;
};

export default PermissionProvider;