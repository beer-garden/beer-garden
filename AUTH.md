# Authentication and Authorization

Beer Garden supports some basic authentication and authorization features that
allow you to create users and roles for the purposes of access control. This
document will walk through how authentication and authorization work, as well as
the various configuration options.

These features are still in their infancy. As such, user fiendly methods of
configuring the various options do not yet exist in many cases.

## Authorization Basics

Each API endpoint in Beer Garden is protected by a specific permission. A user
attempting to access or modify data through an endpoint will first have to pass
an access check, verifying that they have the required permission for the data
that they are operating on. Details regarding the various permissions and how to
assign them will be provided further on, but this is the basic principal on
which the access control for Beer Garden operates. The Beer Garden UI works by
making appropriate API calls behind the scenes. So too does the brewtils Plugin
and EasyClient code. This means that access control for all aspects of Beer
Garden is done through this permission checking that happens in the API.

## Permissions

Permissions are currently defined around typical CRUD operations for various
entities. That is, for a given entity there is a "create", "read", "update", and
"delete" permission. The current entities that exist are:

- job
- garden
- queue
- request
- system

Permissions are defined as strings of the format "\<entity\>:\<operation\>". For
example: `garden:read`, `system:update`, `request:delete`.

There are also a limited number of special permissions that do not map to a
typical entity or operation. These currently include:

- `event:forward` - This permission is required for garden-to-garden
  communications. If your authorization is enabled on your remote gardens, this
  permission must be assigned to the user account that your local garden uses to
  communicate with those remote gardens. **NOTE:** Regular users should not have
  this permission, as it allows for the creation of requests against any garden
  or system.

## Authentication Basics

When authorization is enabled on your garden, users need a way to authenticate
in order to access the garden using their account. From a user's perspective,
this is done via the following:

### Web UI Access

When authorization is enabled, a "login" button will appear toward the top right
of the page. Clicking this brings up a login box for the user to enter their
credentials and sign in.

### API Access

For direct API access, a user would first send their credentials in a POST to
`/api/v1/token`. This results in an access and refresh token being provided back
in the response. The access token would then be provided by the user in
subsequent API calls via the `Authorization: Bearer` header.

This token retrieval and usage is handled for the user by the Web UI and
EasyClient, but both use this API login and access token workflow behind the
scenes.

## Auth Settings

Authorization and authentication settings are housed under a top level `auth`
section of the main application configuration yaml file. The available settings
are:

### authentication_handlers

This section allows you to configure the ways that users are able to
authenticate to the garden. The available handlers and their respective settings
are:

#### basic

Allows for username and password authentication. Available settings:

- **enabled:** Set to `true` to allow username and password authentication.

#### trusted_header

Allow for users to be authenticated via request headers that get set via a
trusted proxy. If your garden sits behind a proxy that will authenticate the
user and place their username in a header, enabling this will tell the garden to
use that provided username.

When logging in via the UI, the login dialog will always show the input fields
for username and password. If a user is authenticating by providing certificates
on all requests that go through a proxy, these fields can safely be left blank.
Since the trusted headers will be included on the login request, the user will
still be able to login.

**NOTE:** If you enable this, it is imperative that users are required to access
your garden through the proxy and do not have a means of accessing the garden
directly. Direct garden access could allow users to set what are supposed to be
trusted headers themselves. This would allow masquerading as whomever they wish.

Available settings:

- **create_users:** When `true` an account will be created automatically for a
  user upon first access. When `false` the user will be denied access unless an
  account already exists for them.
- **enabled:** Set to `true` to allow trusted header authentication.
- **user_groups_header:** The name of the header that will contain a comma
  separated list of the user's group memberships. Default: `bg-user-groups`
- **username_header:** The name of the header that will contain the username.
  Default: `bg-username`

### default_admin

Allows you to specify the username and password for the default admin account.
This account will be created the first time the garden is started and will be
assigned superuser access to the garden.

Available settings:

- **username:** The username of the admin account. Default: admin
- **password:** The password of the admin account. Default: password

### enabled

When `true`, users will be required to authenticate via one of the enabled
authentication handlers and will then have their permissions checked when
attempting to access data or perform actions against the garden. When `false`,
no login is required and no permissions checks are performed.

### group_definition_file

Path to a file mapping groups to beer garden role assignments. Currently groups
can only be assigned via the header defined in
`trusted_header.user_groups_header` and are therefore only applicable when using
that authentication handler. Details on how to configure the group definition
file can be found [below](#group-definition-file).

### role_definition_file

Path to a file that [defines roles](#defining-roles) and the permissions
associated with each role. These are the roles that will be assigned to users in
order to grant access to view data and perform actions on the garden or any
connected remote gardens.

### token_secret

A secret key to use when generating access and refresh tokens. This can be any
arbitrary string, but should be kept secret. Note that changing the value of
this setting will invalidate any previously assigned tokens, forcing all users
to login again.

## Defining Roles

Roles are simply groupings of permissions. Roles can contain whatever
permissions you'd like, though it is generally advisable to construct your roles
around the functionality that different types of users might need in order to
perform their work on the garden.

To define the roles that will be available in your garden, create a yaml file
and set the `auth.role_definition_file` setting to the location of that file.
The format of the file is simply a list of definitions containig a `name` and a
list of `permissions`. Here are some excepts from the example `roles.yaml` file
that you'll find in the [example_configs](src/app/example_configs):

```yaml
- name: "job_manager"
  permissions:
    - "job:create"
    - "job:read"
    - "job:update"
    - "job:delete"

- name: "operator"
  permissions:
    - "garden:read"
    - "request:create"
    - "request:read"
    - "system:read"

- name: "read_only"
  permissions:
    - "job:read"
    - "garden:read"
    - "queue:read"
    - "request:read"
    - "system:read"
```

The available permissions are discussed in the earlier
[Permissions](#permissions) section.

## Assigning Roles

Users are not granted permissions directly. Instead they are assigned roles in a
specific domain, granting them all of the role's permissions in that domain.

A domain is a set of gardens or systems (or the special "Global" domain scope,
which provides universal access). When permissions get checked they follow a
hierarchy, meaning access at the Global level confers access to all gardens and
systems, access for a garden confers access for all systems in that garden, etc.

There is currently no user accessible way to assign roles to users that are
authenticated via the basic (username and password) authentication handler. For
users authenticated via the trusted header handler, see the below section on
creating a group definition file.

## Group Definition File

When using the trusted header authentication handler, it is possible to have the
groups listed in the configured `user_groups_header` mapped to beer garden role
assignments. This is done via a group definition file, which looks like the
following:

```yaml
- group: GLOBAL_SUPERUSER
  role_assignments:
    - role_name: superuser
      domain:
        scope: Global

- group: DEFAULT_READ_ONLY
  role_assignments:
    - role_name: read_only
      domain:
        scope: Garden
        identifiers:
          name: default

- group: DEFAULT_ECHO_JOB_MANAGER
  role_assignments:
    - role_name: job_manager
      domain:
        scope: System
        identifiers:
          name: echo
          namespace: default
    - role_name: read_only
      domain:
        scope: Garden
        identifiers:
          name: default
```

### Group Definitions

The example above shows how to define groups and the role assignments that will
be mapped to them. The following is a brief description of each field.

#### group

The name of the assigned group that will be mapped. This is the name that will
appear in the comma separated list of the header defined by
`user_groups_header`.

#### role_assignments

A list of one or more role assignments to assign to users of the group. A role
assignment is defined as:

- **role_name:** The name of the role as defined in the role file that
  `role_definition_file` points to.
- **domain:** A domain is how we define the context in which the user has the
  assigned roles. A domain consists of a scope and some identifiers.
  - **scope:** Can be one of _Global_ (univeral access), _Garden_ (access
    gardens matching the identifiers), or _System_ (access to systems matching
    the identifiers).
  - **identifiers:** How to identify the items of the given scope that the user
    should have access to. For _Global_, no identifiers are needed. _Garden_
    requires a `name` identifier. _System_ requires at least a `name` or
    `namespace` and can optionally take a `version` as well. Providing fewer
    identifiers results in a broader level of access being granted. For example,
    for a domain with scope _System_, supplying just a `name` identifier would
    result in access to all versions of that system across **all gardens**
    (namespaces) being granted.

## Remote Gardens

One very important note about authorization in Beer Garden is that it is only
performed against the local garden. That is, the garden that the user is
directly interacting with. If your garden has a remote garden connected to it,
permissions for that remote garden should be assigned by a role assignment in an
appropriate domain on the local garden.

For instance, if you have a garden named "parent" and a remote garden connected
to it named "child", you could have the following in your group definition file
to assign access to the "child" garden:

```yaml
- group: CHILD_ECHO_OPERATOR
  role_assignments:
    - role_name: operator
      domain:
        scope: System
        identifiers:
          name: echo
          namespace: child

- group: CHILD_SUPERUSER
  role_assignments:
    - role_name: superuser
      domain:
        scope: Garden
        identifiers:
          name: child
```

It is important to note that no corresponding groups or users need to exist on
the "child" garden. The remote garden effectively assumes that the local garden
has already performed the necessary authorization checks and treats all
forwarded operations as trusted.
