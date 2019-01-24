Assistive Chess Robot Server
----------------------------

This is the server for the assistive chess robot created by Team -i^2 for the System Design Project 2019 at the University of Edinburgh.

Structure of repo
=========

The repository is laid out in the following structure:

```
|
\ server - Contains all code for the flask app
| \
| | __init__.py - To make server into an importable module
| | server.py - Contains the entry point for the Flask app
| | ...
|
\ test - All tests
| \
| | __init__.py - Allows server module to be imported
| | test_main.py - A test file
| | ...
|
| .gitignore - Files that shouldn't be committed by Git
| .travis.yml - Configuration for the CI
| README.md - This readme file
```

Contributing
===========

No commits are allowed directly to master. All PRs to master need to pass status checks and be reviewed by at least one other contributor. Ideally, all pull requests should come with tests for the code within.

**Branch naming** - The convention `<username>/<descriptive word or phrase>` should be used.
