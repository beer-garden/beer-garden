# Beer Garden Changelog

## 3.0.0
11/10/20

Note: This is a major release. Please check out the [site](https://beer-garden.io/) for
more in-depth documentation.

#### Added Features
- Scheduler now supports triggering from file events (#647)
- jquery and lodash objects are now available when creating custom templates (#589)
- Table page length selections in UI are persisted in browser storage (#560)
- Local plugins can now use an alternate python interpreter (#492)
- Request output with a size greater than 16MB is now supported (#407)
- Button added to Request View page for downloading output (#361)
- Additional REST endpoint for Request output (#361)
- Systems can now be grouped by namespace (#284)
- Can now mark commands as hidden (#269)
- The UI Output and Parameters displays can now be expanded (#170)
- Separate gardens can now communicate via REST API
- Actions can be initiated with STOMP messages in addition to the REST API
- Plugin logs can now be retrieved and displayed on the UI System Admin page
- All plugins automatically request a logging configuration from Beer-garden

#### Other Changes
- UI Queue Admin functionality has been moved into System Admin page (#533)
- Drop official support for CentOS 6 (#225)
- Logging config files are now yaml by default (#89)
- Brew-view & Bartender have been merged into a single Beer-garden application (#87)
- UI has been pulled out into a separate application
- Default `max_instances` value for plugins is -1 (no maximum)
- User interface has been streamlined
- Python version bundled with rpm is now 3.7 instead of 3.6
- Commands no longer have an ID field

#### Removed
- Publishing events to RabbitMQ and Mongo has been removed (#681)
- Authentication / Authorization functionality: Users, Roles, Login, etc.

## 2.4.8
6/27/19
Brew-view 2.4.12, Bartender 2.4.4, BG-utils 2.4.8

#### Bug Fixes
- Semicolon in request index page filters no longer breaks (#302)
- Granfana link descriptions on about page respect application name (#301)
- Frontend websocket connection now handles non-default base path (#298)

#### Added Features
- Support for Pika v1 (#305)
- Scheduled jobs can now specify a max number of concurrent executions (#209)
- Interval jobs can now reschedule based on prior run completion (#209)

## 2.4.7
4/24/19
Brew-view 2.4.11, Bartender 2.4.3, BG-utils 2.4.7

#### Bug Fixes
- Fixed configuration generation regression caused by #224 (#254)
- Child requests cannot be created after the parent is completed (#252)
- When mongo pruner removes a request the children are also removed (#246)
- Fixed issue that could cause mongo pruner to not run (#245)
- Mongo pruner will only directly remove top-level requests (#244)

#### Added Features
- Toggle for displaying child requests on the index page (#248)
- Added button for refreshing request index without reloading the page (#236)
- Show a notification on request index page when changes occur (#180)

## 2.4.6
2/22/19
Brew-view 2.4.10, Bartender 2.4.2, BG-utils 2.4.6

#### Bug Fixes
- Request index page overall search no longer specifies a hint (#235)
- Bartender errors correctly propagate back through thrift interface (#229)
- Removed unique index with potential to cause system registration issues (#222)
- Dynamic choices URL source works correctly with a list of strings (#218)
- All files correctly removed when upgrading using the rpm (#215)

#### Added Features
- Config file upgrades can now be converted between json and yaml (#72)
- Centos 7 rpm install now uses real systemd unit files (#17)

#### Other Changes
- Config file extensions for rpm install are now .yaml, not .yml (#226)
- Config files no longer contain bootstrap entries (#224)

## 2.4.5
1/11/19
Brew-view 2.4.7, Bartender 2.4.1, BG-utils 2.4.2

#### Bug Fixes
- Bartender avoids extra network call if shut down while still starting (#214)
- Correct Brew-view startup failure when authentication is enabled (#207)
- No longer hanging if Rabbit broker runs out of resources (#203)
- Errors loading a local plugin will no longer affect subsequent plugins (#202)
- Fixed UI bug where more than one plugin version was considered 'latest' (#200)
- Better error handling for simultaneous index creation (#198)
- Initializing Prometheus counts correctly on startup (#197)
- Accounted for magic comment when building local rpm (#196)
- Styling fix for Systems Management page (#174)
- Changing choices configuration no longer requires removing System (#58)

#### Added Features
- Request view page will show spinner while request is in progress (#204)

#### Other Changes
- Increased default Bartender timeout to 13 seconds (#182)
- Added additional indexes to increase Request Index page performance (#105)

## 2.4.4
10/9/18
Brew-view 2.4.6, Bartender 2.4.0 BG-utils 2.4.0

#### Bug Fixes
- Fixed a race that could cause request creation to wait forever (#195)

#### Added Features
- Added Instance deletion endpoint to REST API


## 2.4.3
9/25/18
Brew-view 2.4.5, Bartender 2.4.0, BG-utils 2.4.0

#### Bug Fixes
- Corrected problem with brew-view escalating CPU usage (#187)
- Select boxes in the UI now have a maximum height (#169)


## 2.4.2
9/25/18
Brew-view 2.4.4, Bartender 2.4.0, BG-utils 2.4.0

#### Bug Fixes
- Request create timeout is now -1 by default to match pre-2.4 behavior (#183)
- The landing page now links newly-created systems correctly (#181)

#### Other Changes
- Changed use of newly-reserved 'async' keyword to support Python 3.7 (#175)


## 2.4.1
9/5/18
Brew-view 2.4.1, Bartender 2.4.0, BG-utils 2.4.0

#### Bug Fixes
- Fixed issue with spinner always being shown on some pages (#172)


## 2.4.0
9/5/18
Brew-view 2.4.0, Bartender 2.4.0, BG-utils 2.4.0

#### Added Features
- 'Created' filtering in request index view now supports second precision (#153)
- Browser window title now reflects current page (#145)
- Brew-view responses now have a header specifying the beer-garden version (#85)
- Webapp no longer relies on IDs in the URL (#98)
- Configuration file will be updated on application startup (#79)
- Connections to RabbitMQ can now be TLS (#74)
- System list endpoint can now return only certain system fields (#70)
- Prometheus metrics and Grafana dashboards (#68, #69)
- Actions on the system management page are more responsive (#67)
- Configuration files can now be yaml (#66)
- Dynamic choices can now use the instance name as an input (#45)
- User / authentication support (#35)
- Request creation can now wait for completion without polling (brew-view #16)
- Periodic request scheduler (#10)

#### Bug Fixes
- Bartender checks for connection to Brew-view before Mongo to fix a race (#160)
- Corrected condition that could cause 'Error: ' to flash on request view (#151)
- Request view will continue to refresh even if a child has errored (#122)
- Fixed issue where /var/run/beer-garden was removed after rpm install (#113)
- Setting queue-level TTL for admin queue messages (#101)
- Data persisted in the webapp using local storage instead of cookies (#92)
- Bartender will error if SSL error occurs during Brew-view check (#65)
- Local plugins are better about logging stacktraces (#57)
- Date on request index page is always UTC (brew-view #56)
- Fixing support for Unicode string values when using Python 2 (#54)
- Nested request display looks better when using slate theme (#41)

#### Other Changes
- Request index spinner icon looks better on slate theme (#155)
- Split system and instance columns on request index page (#103)


## 2.3.9
6/14/18
Brew-view 2.3.10, Bartender 2.3.7, BG-utils 2.3.6

#### Bug Fixes
- Re-added Request indexes that were removed in 2.3.7


## 2.3.8
6/12/18
Brew-view 2.3.9, Bartender 2.3.6, BG-utils 2.3.4

#### Bug Fixes
- Fixed problem with new versions of Marshmallow causing empty requests to be returned from the request list endpoint


## 2.3.7
6/7/18
Brew-view 2.3.8, Bartender 2.3.6, BG-utils 2.3.4

This release addresses two critical problems with database performance. To support the fix an additional field was added to the Request model and the indexes for the Request collection were updated.

**When updating to this version the Request collection will be updated to reflect these changes.** This will happen automatically and requires no action on the part of administrator. Status messages will be logged at the WARNING level as the upgrade occurs.

See issue #84 for a detailed explanation.

#### Bug Fixes
- Database operations sometimes timed out on slow networks due to configuration error (#84)

#### Other Changes
- Reworked database indexes so Request queries are more efficient (#84)


## 2.3.6
4/6/18
Brew-view 2.3.6, Bartender 2.3.5, BG-utils 2.3.3

#### Added Features
- Using RabbitMQ publisher confirms when publishing requests (#37)
- Brew-view accepts ca_cert, ca_path, and client_cert_verify configuration options (beer-garden/brew-view#43)
- Bartender now explictly checks for connectivity to Mongo and RabbitMQ admin interface on startup (#38, #48)

#### Bug Fixes
- Status monitor no longer continuously restarts when RabbitMQ connectivity is lost
- Clearing queues now works with Rabbit 3.7
- Child rows in nested request display now show correct created time
- Command-based dynamic choices now work without a 'default' instance (#47)

#### Other Changes
- Adding explict support for Python 3.4
- Using non-Brewmaster exceptions from Brewtils
- Using pytest instead of nose to run tests


## 2.3.5
4/3/18
Brew-view 2.3.5, Bartender 2.3.4, BG-utils 2.3.3

#### Added Features
- Attempting to update a completed request without actually modifiying data is no longer an error (beer-garden/brew-view#49)

#### Bug Fixes
- Configuration file generation fix for Python 2


## 2.3.3
2/21/18
Brew-view 2.3.3, Bartender 2.3.3, BG-utils 2.3.2

#### Bug Fixes
- Bartender shutdown will now be clean even before making Brew-view and RabbitMQ connections

#### Other Changes
- Using [Yapconf] for configuration loading
- Running Flake8 linting on source and tests


## 2.3.1
2/5/18
Brew-view 2.3.1, Bartender 2.3.0, BG-utils 2.3.0

#### Bug Fixes
- Fixing issue with manual request creation targeting incorrect system


## 2.3.0
1/26/18

#### Added Features
- Bartender can now be configured to skip server certificate verification when making HTTPS requests
- Added Bartender custom CA certificate configuration option
- Timestamps now have true millisecond precision on platforms that support it
- Plugins can now specify `max_instances` as a keyword parameter without needing to define a System
- Command Index page now supports pagination, cosmetic changes
- Added ability to specify a textarea be used as the input for a Parameter
- System Admin page now has links to the individual System pages
- Requests that incorrectly fail frontend validation can now be modified and sent manually
- Reworked fronted sidebar to be clearer when multiple verions of a System are registered
- Dark theme for frontend
- New Parameter types: date and datetime
- Searching Request index by 'created' field now uses datepickers
- REST API can now be served with a URL prefix
- Notifications are now published to RabbitMQ and/or a specified URL when significant events occur

#### Bug Fixes
- Multi Parameters that are type 'Dictionary' now work correctly
- Corrected RabbitMQ users - the 'normal' user is now only used by plugins and only needs read permission
- 'Any' Parameters that are also multi no longer disappear when transitioning from valid to invalid
- Fixed possible temporary error when deleting a system
- Better support for large number of concurrent plugin startups
- Corrected the validation icon and close button overlap for string parameters inside an array

#### Other Changes
- Systems can no longer be registered with the same display name and version as an existing System
- The attempt to update a Request after its processed now has a maximum retry count
- Better data integrity by only allowing certain Request status transitions


## 2.1.1
11/21/17
#### Bug Fixes
- Modified System deletion procedure so it works correctly on Systems with no Instances
- Fixed bug where validation error during first-time System registration resulted in an empty System


## 2.1.0
10/23/17
#### Added Features
- Added popover icon with an explanation for a Request's status to the Request View page
- 'Make it Happen!' buttons are now middle-clickable
- Added sorting to Queue Management table
- ACTION-type requests can now be aged off similar to INFO-type requests
- Command descriptions can now be changed without updating the System version
- Added `updated_at` field to `Request` model
- Added `admin`, `queues`, and `config` endpoints to Swagger
- Brewtils: `SystemClient` now allows specifying a `client_cert`
- Brewtils: `RestClient` now reuses the same session for subsequent connections
- Typeaheads immediately display choices when focused
- Standardized Remote Plugin logging configuration
- Choices providers can now return a simple list
- PATCH requests no longer need to be wrapped in an `operations` envelope
- UI will display a warning banner when attempting to make a request on a non-RUNNING instance
- Request creation endpoint now includes a header with the instance status in the response
- Available choices for one parameter can now depend on the current value of another parameter
- Brewtils: Added domain-specific language for dynamic choices configuration
- Brewtils: `SystemClient` can now make non-blocking requests
- Search functionality on the Command Index page
- Added `metadata` field to Instance model
- Brewtils: `RestClient` and `EasyClient` now support PATCHing a `System`

#### Bug Fixes
- Link to RabbitMQ Admin page now works correctly with non-default virtual host
- Large (>4MB) output no longer causes a Request to fail to complete
- Better handling of timeout failures during Request creation
- Number types no longer need be be selected in a Typeahead
- Removed default model values that could cause serialization inconsistencies
- System descriptors (description, display name, icon name, metadata) now always updated during startup
- Corrected display for a multi string Parameter with choices
- Stricter type validation when making a request with string, integer, or boolean parameters
- Added TTL to Admin messages so they don't persist forever
- Better handling of null values in the frontend
- Validating instance_name during request creation
- Reworked message processing to remove the possibility of a failed request being stuck in 'IN_PROGRESS'
- Correctly handle custom form definitions with a top-level array
- Increased startup reliability for Systems with many (>15) Instances
- Bartender helper threads can no longer hang shutdown
- POST and PATCH requests without a `content-type` header now return status code 400
- Better select control placeholder text
- Requests with output type 'JSON' will now have JSON error messages
- Smarter reconnect logic when the RabbitMQ connection fails
- Attempting to remove 'orphaned' commands if any are found during a query

#### Deprecations / Removals
- The following API endpoints are deprecated:
  - POST `/api/v1/admin/system`
  - GET `/api/v1/admin/queues`
  - DELETE `/api/v1/admin/queues`
  - DELETE `/api/v1/admin/queues/{queue_name}`
- Brewtils: `multithreaded` argument to `PluginBase` has been superseded by `max_concurrent`
- Brewtils: These decorators are now deprecated:
  - `@command_registrar`, instead use `@system`
  - `@plugin_param`, instead use `@parameter`
  - `@register`, instead use `@command`
- These classes are now deprecated:
  - `BrewmasterSchemaParser`, instead use `SchemaParser`
  - `BrewmasterRestClient`, instead use `RestClient`
  - `BrewmasterEasyClient`, instead use `EasyClient`
  - `BrewmasterSystemClient`, instead use `SystemClient`

#### Other Changes
- Searching on Request Index page no longer searches request output
- Reset button on the Command View page ignore 'Pour it Again' values and always reset to defaults
- Brewtils: Request processing now occurs inside of a `ThreadPoolExecutor` thread
- Using Webpack to bundle frontend resources
- Removed dependencies on compiled Python packages (#196) and Flask
- Using the `subprocess32` module to run Local Plugins
- Local plugins no longer run in their own separate process groups
- Local and Remote plugins are now functionally identical
- Improved concurrency by making all Thrift calls asynchronous


## 2.0.4
8/04/17
#### Bug Fixes
- Corrected typo in request index page that prevented filtering for IN_PROGRESS requests from working


## 2.0.3
8/01/17
#### Bug Fixes
- Reworked request index query to address performance bottleneck


## 2.0.2
7/26/17
#### Bug Fixes
- Fixed frontend validation problem for a nullable boolean parameter with a null default


## 2.0.1
7/14/17
#### Bug Fixes
- Added Object.assign shim for compatability with older browsers


## 2.0.0
7/5/17
#### Added Features
- Support for remote plugins
- Support for custom HTML templates on request pages
- Support for Dynamic choices
- Support for starting/stopping individual Instances
- Support for display names of a plugin
- Support for metadata for a plugin
- Support for Python 3

#### Bug Fixes
- Optional model with default values
- Bug where nested parameters would not get checked in system validation
- GUI bug where timestamps for child request didnt look right
- Bug with optional list arguments
- Bug where nested request output type didnt look right

#### Other Changes
- Added better exception handling to API
- Better error reporting for serialization failures
- The system model has changed
- The command model has changed
- RabbitMQ now uses a topic instead of an exchange

#### Security
- All Docker images have been upgraded
- We now build CentOS 6 and CentOS7 RPMs


## 1.1.0
#### Added Features
- Support for auto-reconnect to brew-view if it is down on startup
- Support for stopping, starting and reloading plugins
- Support for dynamically deploying new plugins
- Support for output_type for Requests
- This changelog


## 1.0.4
7/19/2016
#### Added Features
- Support for Multi-threaded, single instance plugins
- Support for nested requests
- Support for INFO Command Types
- Support for comments on requests
- Support for purging INFO commands

#### Bug Fixes
- Bug where RPMs would not get correctly updated

#### Other Changes
- Join times for threads to be non-zero. This greatly reduces CPU utilization


## 1.0.3
12/30/2015
#### Bug Fixes
- Bug where Plugins would not work with non-ssl enabled versions of brew-view


## 1.0.2
12/3/15
#### Security
- Added SSL Support


## 1.0.1
11/10/15
#### Other Changes
- Bumped bg-utils version


## 1.0.0
10/2/15
#### Added Features
- Support for Local Plugins
- Initial Build of the Backend Threads
- Support for Validating Requests
- Support for Processing Requests
- Support for clearing a queue
- Support for getting a System state
- Support for Stopping a System
- Support for Starting a System
- Support for Restarting a System
- Support for killing a System
- Support for Stopping All Systems
- Support for Starting All Systems
- Support for Killing All Systems
- Support for getting Bartender version
- Support for ping
- Support for building/deploying as an RPM
- Support for easily generating logging and configuration files


[Yapconf]: https://github.com/loganasherjones/yapconf
