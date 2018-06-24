## MESON CORPUS TEST

A tool for testing a corpus of meson builds

`run` runs the test in local docker containers

`update` writes a .travis.yml CI configuration

`update` is intended to be used by `cronscript` to update the
`meson-corpus-test` repository.

If project _PROJ_ fails in CI, you can try `./run PROJ --interactive` to
investigate locally.

### TODO:
- Since we're always providing all builddeps, we're not exercising fallbacks (use forcefallback?)
- Pin to a specific git commit (not bleeding edge so bionic can satisify builddeps & to avoid false reports due to upstream breakage)
- Add 'test' to ninja targets built

### PACKAGE CACHING

`run` transfers any `/etc/apt/apt.conf.d/01proxy` file to the container.  Set
this to point to a local apt-cacher instance to avoid repeatedly downloading the
same packages.

e.g.
1. `sudo apt-get install apt-cacher`
2. uncomment `allowed_hosts = *` in `/etc/apt-cacher/apt-cacher.conf`
3. `sudo service apt-cacher restart`
4. `echo Acquire::http::Proxy \"http://<IP of localhost>:3142\"\; > /etc/apt/apt.conf.d/01proxy`
