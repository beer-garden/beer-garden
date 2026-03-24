import { jwtDecode, JwtPayload } from "jwt-decode";

import { Role } from "../models/brewtils-types";
import { GetToken } from "./token_service";

interface CustomJwtPayload extends JwtPayload {
  username?: string;
  roles?: string[];
}

export const GetCurrentUser = () => {
  const token = GetToken();
  if (token !== null) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.username) {
      return decode.username;
    }
  }
  return undefined;
};

export const GetCurrentRoles = (): Array<Role> | undefined => {
  const token = GetToken();
  if (token !== null) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.roles) {
      const userRoles = [] as Array<Role>;
      for (const role of decode.roles) {
        // The role can be a string or an object depending on how the token was generated
        if (typeof role === "string") {
          userRoles.push(JSON.parse(role) as Role);
        } else {
          userRoles.push(role as Role);
        }
      }
      return userRoles;
    }
  }
  return undefined;
};
