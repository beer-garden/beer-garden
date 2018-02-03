# Brew View Changelog

Brew View is the GUI and ReST service that powers beer-garden.
All notable changes should be documented in this file.


## [unreleased]
### Added
- Features go here as they get added
- Added ability to specify default icon in config file

### Fixed
- Bug fixes go here as they get added

### Changed
- Changes go here as they get added

### Security
- Relevant security changes go here

## [1.2.0]

### Added 
### Changed
- The name

## [1.1.0]
### Added
- Start, stop, and reload plugins
- Error type display to request view page
- A collapsible JSON view for JSON request output
- Syntax highlighting display for command preview and request parameters
- Sorting (by command name) to command listings
- Support for changing the default-icon
- This changelog

### Changed
- The look-and-feel of the About page

## [1.0.8] - 2016-07-19
### Added
- Support for Nested Requests
- Version endpoint to REST API

### Fixed
- Bug where deletion of a queue would leave a Thrift transport open
- Bug where requesting information about a queue would leave a thrift transport open
- Various bugs when installing/updating RPMs
- Bug where requests would still take a long time to load

## [1.0.7] - 2016-06-21
### Added
- Support for Regular Expression Validation in GUI
- Support for Server-side Paging of Requests
- Support for Server-side filtering of Requests


## [1.0.6] - 2016-06-06
### Added
- Maximum and Minimum Constraints to Front-end parameters

## [1.0.5] - 2016-05-24
### Changed
- Bumped bg-utils version

## [1.0.4] - 2016-05-20
### Added
- Support for creating comments on each Request
- Displaying Comment Field in the GUI

### Changed
- Display Length for Requests to be 10 by default

### Fixed
- Bug where the first "{" in the request would be indented.

## [1.0.3] - 2015-12-30
### Changed
- Bumped bg-utils version

## [1.0.2] - 2015-12-03
### Security
- Enabled SSL Communications by default

### Fixed
- Bug where after install scripts of RPMs would not get executed correctly

## [1.0.1] - 2015-11-12
### Changed
- Bumped bg-utils version

## 1.0.0 - 2015-10-02
### Added
- Capability to Handle Thrift Errors
- Interaction with Bartender Backend
- Support for BREWMASTER Interface [/system, /command, /request]
- Added basic GUI functionality


[unreleased]: https://github.com/beer-garden/brew-view/compare/master...develop
[1.1.0]: https://github.com/beer-garden/brew-view/compare/v1.1.0...v1.1.0
[1.0.8]: https://github.com/beer-garden/brew-view/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/beer-garden/brew-view/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/beer-garden/brew-view/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/beer-garden/brew-view/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/beer-garden/brew-view/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/beer-garden/brew-view/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/beer-garden/brew-view/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/beer-garden/brew-view/compare/v1.0.0...v1.0.1
