export function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  if (match) return match[2];
  return null;
}

export function deleteCookie(name, sPath, sDomain) {
  document.cookie =
    encodeURIComponent(name) +
    "=; expires=Thu, 01 Jan 1970 00:00:00 GMT" +
    (sDomain ? "; domain=" + sDomain : "") +
    (sPath ? "; path=" + sPath : "");
}

export function isEmpty(obj) {
  if (obj) {
    return Object.keys(obj).length === 0;
  }
  return true;
}
