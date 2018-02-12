# Bartender Changelog

Note: We no longer keep this changelog up-to-date. Instead we put all changes into the [beer-garden changelog](https://github.com/beer-garden/beer-garden/tree/master/CHANGELOG.md)
Please check that changelog for all relevant changes.

## 1.1.0
### Added
- Support for auto-reconnect to brew-view if it is down on startup
- Support for stopping, starting and reloading plugins
- Support for dynamically deploying new plugins
- Support for output_type for Requests
- This changelog

## 1.0.4 - 2016-07-19
### Added
- Support for Multi-threaded, single instance plugins
- Support for nested requests
- Support for INFO Command Types
- Support for comments on requests
- Support for purging INFO commands

### Fixed
- Bug where RPMs would not get correctly updated

### Changed
- Join times for threads to be non-zero. This greatly reduces CPU utilization

## 1.0.3 - 2015-12-30
### Fixed
- Bug where Plugins would not work with non-ssl enabled versions of brew-view

## 1.0.2 - 2015-12-03
### Security
- Added SSL Support

## 1.0.1 - 2015-11-10
### Changed
- Bumped bg-utils version

## 1.0.0 - 2015-10-02
### Added
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

