Python-rein version v0.3.2-beta is now available from:

  <https://reinproject.org/bin/python-rein-v0.3.2-beta/>

This is a new minor version release, including user search,
trust scoring, basic user profile pages, and test coverage metrics.

Please report bugs using the issue tracker at github:

  <https://github.com/ReinProject/python-rein/issues>

To receive security and update notifications, please follow:

  <https://twitter.com/ReinProject>


v0.3.2-beta Change log
======================

Detailed release notes follow. This overview includes changes that affect behavior,
not code moves, refactors and string updates. For convenience in locating code 
changes and accompanying discussion, both the pull request and git merge commit are
mentioned.


### Search
- #129 `208c1be` User search, ratings from local db (FreakJoe)

### Reputation
- #114 `259c8ac` Trust scores (FreakJoe)

### Usability
- #127 `b69685c` Fix #125 by using jquery''s trim (weex)
- #128 `30c3f50` Config and UX improvements (weex)

### Maintenance
- #113 `387248d` Fix blanks and newlines in document field (weex)
- #121 `eb78533` Adding Coveralls to build (mtlynch)
- #122 `4ef9020` Fixing BIP32 tests (mtlynch)
- #123 `221ab14` Avoid zero-divisor error (FreakJoe)


Credits
=======

Thanks to everyone who directly contributed to this release:

- David Sterry
- FreakJoe
- Michael Lynch
