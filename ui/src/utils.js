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

export function hasPermissions(userData, permissions) {
  if (
    isEmpty(userData) ||
    !userData.permissions ||
    userData.permissions.length === 0
  ) {
    return false;
  }

  if (userData.permissions.includes("bg-all")) {
    return true;
  }

  return permissions.every(elem => userData.permissions.includes(elem));
}

export function coalescePermissions(roleList) {
  let aggRoles = new Set();
  let aggPerms = new Set();

  roleList.forEach(role => {
    aggRoles.add(role.name);
    aggPerms = new Set([...aggPerms, ...role.permissions]);

    if (role.roles) {
      const { roles, permissions } = coalescePermissions(role.roles);
      aggRoles = new Set([...aggRoles, ...roles]);
      aggPerms = new Set([...aggPerms, ...permissions]);
    }
  });

  return { roles: aggRoles, permissions: aggPerms };
}

export function isValidPassword(password) {
  if (password.length < 8) {
    return { valid: false, message: "Password is too short" };
  }

  const ucaseFlag = /[A-Z]/.test(password);
  const lcaseFlag = /[a-z]/.test(password);
  const digits = /\d/.test(password);
  const nonWords = /\W/.test(password);

  if (ucaseFlag && lcaseFlag && digits && nonWords) {
    return { valid: true, message: "valid" };
  } else {
    return {
      valid: false,
      message:
        "Passwords must contain an upper & lowercase letter, a digit and a symbol",
    };
  }
}

export function toggleItemInArray(
  list,
  value,
  itemKey = null,
  formatter = null,
  valueKey = null,
) {
  const newList = [...list];
  const index = newList.findIndex(i => {
    const val = valueKey ? value[valueKey] : value;
    return itemKey ? i[itemKey] === val : i === val;
  });

  if (index !== -1) {
    newList.splice(index, 1);
  } else if (formatter) {
    newList.push(formatter(value));
  } else {
    newList.push(value);
  }
  return newList;
}

export const updateIfExists = (list, item) => {
  const index = list.findIndex(i => i.id === item.id);
  let newList = [...list];
  if (index !== -1) {
    newList[index] = item;
  }
  return newList;
};

export const removeIfExists = (list, id) => {
  const index = list.findIndex(i => i.id === id);
  let newList = [...list];
  if (index !== -1) {
    newList.splice(index, 1);
  }
  return newList;
};
