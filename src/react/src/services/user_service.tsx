import { jwtDecode, JwtPayload } from "jwt-decode";

interface CustomJwtPayload extends JwtPayload {
  username?: string;
  roles?: string[];
}

export const GetCurrentUser = (token: string) => {
  if (token) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.username) {
      return decode.username;
    }
  }
  return undefined;
};

export const GetCurrentRoles = (token: string) => {
  if (token) {
    const decode = jwtDecode<CustomJwtPayload>(token);
    if (decode.roles) {
      return decode.roles;
    }
  }
  return undefined;
};
