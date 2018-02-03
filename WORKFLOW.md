# Beergarden Workflow

Beergarden uses the Git Workflow model of deployment. This means we have several
"special" branches which we maintain.  Long lived branches are:

* `master`
* `develop`

There are also short-lived branches that follow a naming convention. They are:

* `hotfix/*`
* `release/*`
* `feature/*`

Each of these branches has their own separate build processes and rules for
pushing or merging. In this document, we will go over the process for creating,
contributing, merging, and pushing to beergarden repositories.

## Master Branch

The `master` branch represents the latest stable version of beergarden. It
should _always_ be pristine. There should also only be merge commits in
`master`. A  developer should never be committing/pushing directly to `master`.
Instead all merges to `master` should be coming from `hotfix/*` or `release/*`.
More on these special branches later.

### Master build process

When a branch is merged to `master` the build process will kick off. The
`master` build process includes creating a tag of the version that is being
created. If an artifact is associated with this product, then it will get
automatically deployed, any documentation that is linked with the project will
also get generated with the appropriate version number and deployed to the
documentation servers.

1. Check that version number matches semantic versioning (commit pre-hook)
2. Tag with version number
3. Deploy artifact(s)
4. Deploy documentation

## Develop Branch

The `develop` branch represents the latest version of beergarden. It should be
mostly stable as a `release/*` branch always spawns from the `develop` branch.
It is okay to push or merge to `develop`. In general, developers should be
creating `feature/*` branches off of `develop` and creating merge requests.
Pushing to `develop` should be saved for small changes that do not add new
features or fix major bugs. These types of changes should _always_ be in a
`feature/*` branch. The `develop` branch can contain a version that includes
a `SNAPSHOT` or `dev` suffix. (e.g. `1.0.0-SNAPSHOT`, `1.0.0.dev0`, etc)

### Develop Build Process

When a push or a merge occurrs on `develop` a build kicks off. The build process
for `develop` is not very involved. It should run unit & integration tests and
that is all. It is worth noting what we mean when we say integration tests.
Integration tests in this context means that the project in question will work
on a given platform, with a given DB, etc. Another note here is that if your
integration tests are up to your team's discretion. If integration tests slow
down the development cycle meaningfully, then they may be thrown out during this
step. This is up to the particular project's discretion. In general, we advise
runing integration tests during this step.

1. Run the Unit tests
2. Run the integration tests

## Feature Branches

`feature/*` branches represent features or bug fixes that improve the project
in some meaningful way. All `feature/*` branches will branch `develop`. All
`feature/*` branches must start with `feature/` (e.g. if I'm fixing a bug
I would call the branch: `feature/my_bug_fix`). Feature branches are not meant
to be long-lived branches. They exist until they are merged into `develop` at
which time they will be deleted. All `feature/*` branches should be tested
before a merge request is created. `feature/*` branches can optionally be tied
to a tracking system of the project's choice.

### Feature Branch Workflow

When creating a feature, these are the basic steps a developer will follow to
contribute their feature to the beergarden project.

1. Checkout `develop` (`git checkout develop`)
2. Pull the latest changes from `develop` (`git pull develop`)
3. Create your feature branch (`git checkout -b feature/my_new_feature`)
4. Develop the new feature
5. Develop unit tests for the new feature
6. Develop integration tests for the new feature if required

You may repeat steps 4-6 as many times as necessary to get your feature correct.
Once you are confident that your feature branch is ready, you can do the
following:

1. Ensure you have the latest changes from `develop` (`git pull develop`)
  * Fix any merge conflicts that result from this pull
  * If there were any merge conflicts, test your results
2. Create a merge request with `develop`
3. If the team implements code review, do that
4. Make changes as a result of the merge request feedback
5. Merge the branch into `develop`
  * You may not be able to do this step if you do not have permissions

## Release Branches

`release/*` branches represent release candidates for the project. All
`release/*` branches must start with the `release/` prefix. Release branches
are not meant to be long-lived branches. They exist until they are merged into
`master` and `develop`. Once merged into both of these branches, it can safely
be deleted. The `release/*` branch is where a team should do all of it's
hardening. This should be gone over by QA teams and should include end-to-end
testing. Release branches always come from the `develop` branch. `release/*`
branches also undergo a build process.

### Release Branch Build Process

Pushing and merging are equivalent for the build process of `release/*`
branches. Release branches should not contain a dev version. All versions in
a `release/*` branch should either be release candidates (`1.0.0-rc1`) or
finalized versions (`1.0.0`). The release process will do the following:

1. Check that version number matches what was described above (commit pre-hook)
2. Run Unit/Integration Tests
3. Build all Artifacts
4. Deploy all Artifacts
5. Deploy to integration environment
6. Run end-to-end automated tests
7. Deploy documentation

Once a `release/*` branch is solid, it should follow these steps:

1. Change version to a finalized version (`X.X.X`)
2. Merge to `master`
3. Merge to `develop`

## Hotfix Branches

`hotfix/*` branches represent critical bugs that need to be fixed in the
currently deployed `master` branch. These should be used only when necessary.
All `hotfix/*` branches must start with the `hotfix/` prefix. Hotfix branches
are not meant to be long-lived branches. They exist until they are merged into
`master` and `develop`. Once merged into these branches, it can be saefly
deleted. The `hotfix/*` branch requires that the developer do as much testing
as possible. All `hotfix/*` branches should really be as narrowly focused and
easily testable as possible. The process for creating and contributing a
`hotfix/*` branch is as follows:

1. Checkout master (`git checkout master`)
2. Create hotfix branch (`git checkout hotfix/hotfix_1`)
3. Fix the bug in software
4. Write Unit/Integration Tests for bugs
5. Quick end-to-end manual verification that bug no longer exists
6. Bump the version (`X.X.X`)
7. Merge to `master`
8. Merge to `develop` if not already fixed in that branch