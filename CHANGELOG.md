# Beer Garden Changelog

All notable changes should be documented in this file.

## [2.3.0]
Date: 1/26/18
#### Added Features
- Bartender can now be configured to skip server certificate verification when making HTTPS requests (#326)
- Added Bartender custom CA certificate configuration option (#326)
- Timestamps now have true millisecond precision on platforms that support it (#325)
- Plugins can now specify `max_instances` as a keyword parameter without needing to define a System (#324)
- Command Index page now supports pagination, cosmetic changes (#306)
- Added ability to specify a textarea be used as the input for a Parameter (#294)
- System Admin page now has links to the individual System pages (#283)
- Requests that incorrectly fail frontend validation can now be modified and sent manually (#264)
- Reworked fronted sidebar to be clearer when multiple verions of a System are registered (#256)
- Dark theme for frontend (#236)
- New Parameter types: date and datetime (#232)
- Searching Request index by 'created' field now uses datepickers (#231)
- REST API can now be served with a URL prefix (#60)
- Notifications are now published to RabbitMQ and/or a specified URL when significant events occur(#21)

#### Bug Fixes
- Multi Parameters that are type 'Dictionary' now work correctly (#303)
- Corrected RabbitMQ users - the 'normal' user is now only used by plugins and only needs read permission (#277)
- 'Any' Parameters that are also multi no longer disappear when transitioning from valid to invalid (#274)
- Fixed possible temporary error when deleting a system (#253)
- Better support for large number of concurrent plugin startups (#245)
- Corrected the validation icon and close button overlap for string parameters inside an array (#135)

#### Other Changes
- Systems can no longer be registered with the same display name and version as an existing System (#308)
- The attempt to update a Request after its processed now has a maximum retry count (#258, #297)
- Better data integrity by only allowing certain Request status transitions (#214)

## [2.1.1]
11/21/17
#### Bug Fixes
- Modified System deletion procedure so it works correctly on Systems with no Instances (#299)
- Fixed bug where validation error during first-time System registration resulted in an empty System (#298)

## [2.1.0]
10/23/17
#### Added Features
- Added popover icon with an explanation for a Request's status to the Request View page (#254)
- 'Make it Happen!' buttons are now middle-clickable (#242)
- Added sorting to Queue Management table (#240)
- ACTION-type requests can now be aged off similar to INFO-type requests (#226)
- Command descriptions can now be changed without updating the System version (#225)
- Added `updated_at` field to `Request` model (#182)
- Added `admin`, `queues`, and `config` endpoints to Swagger (#181)
- Brewtils: `SystemClient` now allows specifying a `client_cert` (#178)
- Brewtils: `RestClient` now reuses the same session for subsequent connections (#174)
- Typeaheads immediately display choices when focused (#170)
- Standardized Remote Plugin logging configuration (#168)
- Choices providers can now return a simple list (#155)
- PATCH requests no longer need to be wrapped in an `operations` envelope (#141)
- UI will display a warning banner when attempting to make a request on a non-RUNNING instance (#132)
- Request creation endpoint now includes a header with the instance status in the response (#132)
- Available choices for one parameter can now depend on the current value of another parameter (#130)
- Brewtils: Added domain-specific language for dynamic choices configuration (#130)
- Brewtils: `SystemClient` can now make non-blocking requests (#121)
- Search functionality on the Command Index page (#69)
- Added `metadata` field to Instance model
- Brewtils: `RestClient` and `EasyClient` now support PATCHing a `System`

#### Bug Fixes
- Link to RabbitMQ Admin page now works correctly with non-default virtual host (#276)
- Large (>4MB) output no longer causes a Request to fail to complete (#259)
- Better handling of timeout failures during Request creation (#241)
- Number types no longer need be be selected in a Typeahead (#238)
- Removed default model values that could cause serialization inconsistencies (#237)
- System descriptors (description, display name, icon name, metadata) now always updated during startup (#213, #228)
- Corrected display for a multi string Parameter with choices (#222)
- Stricter type validation when making a request with string, integer, or boolean parameters (#219, #220, #221)
- Added TTL to Admin messages so they don't persist forever (#212)
- Better handling of null values in the frontend (#62, #186, #194, #205)
- Validating instance_name during request creation (#189)
- Reworked message processing to remove the possibility of a failed request being stuck in 'IN_PROGRESS' (#183, #210)
- Correctly handle custom form definitions with a top-level array (#177)
- Increased startup reliability for Systems with many (>15) Instances (#173)
- Bartender helper threads can no longer hang shutdown (#172)
- POST and PATCH requests without a `content-type` header now return status code 400 (#171)
- Better select control placeholder text (#169)
- Requests with output type 'JSON' will now have JSON error messages (#92)
- Smarter reconnect logic when the RabbitMQ connection fails (#83)
- Attempting to remove 'orphaned' commands if any are found during a query (#78)

#### Deprecations / Removals
- The following API endpoints are deprecated (#181):
  - POST `/api/v1/admin/system`
  - GET `/api/v1/admin/queues`
  - DELETE `/api/v1/admin/queues`
  - DELETE `/api/v1/admin/queues/{queue_name}`
- Brewtils: `multithreaded` argument to `PluginBase` has been superseded by `max_concurrent`
- Brewtils: These decorators are now deprecated (#164):
  - `@command_registrar`, instead use `@system`
  - `@plugin_param`, instead use `@parameter`
  - `@register`, instead use `@command`
- These classes are now deprecated (#165):
  - `BrewmasterSchemaParser`, instead use `SchemaParser`
  - `BrewmasterRestClient`, instead use `RestClient`
  - `BrewmasterEasyClient`, instead use `EasyClient`
  - `BrewmasterSystemClient`, instead use `SystemClient`

#### Other Changes
- Searching on Request Index page no longer searches request output (#259)
- Reset button on the Command View page ignore 'Pour it Again' values and always reset to defaults (#248)
- Brewtils: Request processing now occurs inside of a `ThreadPoolExecutor` thread (#183)
- Using Webpack to bundle frontend resources (#175)
- Removed dependencies on compiled Python packages (#196) and Flask (#161)
- Using the `subprocess32` module to run Local Plugins (#188)
- Local plugins no longer run in their own separate process groups (#187)
- Local and Remote plugins are now functionally identical (#109, #179)
- Improved concurrency by making all Thrift calls asynchronous (#153)

## [2.0.4]
8/04/17
#### Bug Fixes
- Corrected typo in request index page that prevented filtering for IN_PROGRESS requests from working (#190)

## [2.0.3]
8/01/17
#### Bug Fixes
- Reworked request index query to address performance bottleneck (#193)

## [2.0.2]
7/26/17
#### Bug Fixes
- Fixed frontend validation problem for a nullable boolean parameter with a null default (#185)

## [2.0.1]
7/14/17
#### Bug Fixes
- Added Object.assign shim for compatability with older browsers (#176)

## 2.0.0
7/5/17
#### Added Features
- Support for remote plugins
- Support for custom HTML templates on request pages
- Support for Dynamic choices
- Support for starting/stopping individual Instances (#26)
- Support for display names of a plugin (#137)
- Support for metadata for a plugin (#136)
- Support for Python 3 (#41)

#### Bug Fixes
- Optional model with default values (#73)
- Bug where nested parameters would not get checked in system validation (#79)
- GUI bug where timestamps for child request didnt look right (#105)
- Bug with optional list arguments (#123)
- Bug where nested request output type didnt look right (#139)

#### Other Changes
- Added better exception handling to API (#106)
- Better error reporting for serialization failures (#142)
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

##[1.0.4
2016-07-19
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
2015-12-30
#### Bug Fixes
- Bug where Plugins would not work with non-ssl enabled versions of brew-view

##[1.0.2
2015-12-03
#### Security
- Added SSL Support

## 1.0.1
2015-11-10
#### Other Changes
- Bumped bg-utils version

## 1.0.0
2015-10-02
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


[unreleased]: https://github.com/beer-garden/bartender/compare/master...develop
[2.3.0]: https://github.com/beer-garden/beer-garden/compare/2.1.1...2.3.0
[2.1.1]: https://github.com/beer-garden/beer-garden/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/beer-garden/beer-garden/compare/2.0.4...2.1.0
[2.0.4]: https://github.com/beer-garden/beer-garden/compare/2.0.3...2.0.4
[2.0.3]: https://github.com/beer-garden/beer-garden/compare/2.0.2...2.0.3
[2.0.2]: https://github.com/beer-garden/beer-garden/compare/2.0.1...2.0.2
[2.0.1]: https://github.com/beer-garden/beer-garden/compare/2.0.0...2.0.1
