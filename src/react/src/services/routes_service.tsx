export const externalRoutesList = [
  { path: "/", componentName: "Dashboard" },
  { path: "/dashboard", componentName: "Dashboard" },
  { path: "/request/:requestId", componentName: "Request_View" },
  { path: "/requests", componentName: "Requests" },
  { path: "/jobs", componentName: "Jobs" },
  { path: "/about", componentName: "About" },
  { path: "/roles", componentName: "Roles" },
  { path: "/topics", componentName: "Topics" },
  { path: "/users", componentName: "Users" },
  { path: "/swagger", componentName: "Swagger" },
  { path: "*", componentName: "Error" },
] as Record<"path" | "componentName", string>[];
