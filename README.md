## MESON CORPUS TEST

Tools for testing a corpus of meson builds

`update-workflow` writes a GitHub workflow .yml CI configuration

This script is intended to be used by `cronscript` to update the
`meson-corpus-test` repository.

`most-recent-tag-update` maintains the most-recent-tag database
used by that.

Use `./most-recent-tag-update -update PROJ` to manually update
the tag used for _PROJ_.

`run` runs the test in local docker containers

If project _PROJ_ fails in CI, you can try `./run PROJ --interactive` to
investigate locally.

### TODO:

- Since we're always providing all builddeps, we're not exercising fallbacks (use forcefallback?)
- Add 'test' to ninja targets built
- Use scheduled GitHub workflow to do the update, not a cronjob on a random machine

### PACKAGE CACHING

`run` transfers any `/etc/apt/apt.conf.d/01proxy` file to the container.  Set
this to point to a local apt-cacher instance to avoid repeatedly downloading the
same packages.

e.g.
1. `sudo apt-get install apt-cacher`
2. uncomment `allowed_hosts = *` in `/etc/apt-cacher/apt-cacher.conf`
3. `sudo service apt-cacher restart`
4. `echo Acquire::http::Proxy \"http://<IP of localhost>:3142\"\; > /etc/apt/apt.conf.d/01proxy`
