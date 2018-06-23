#
# common code for corpus test tools
#

import collections
import os
import re
import shlex
import sys
import urllib.request
import yaml

def fetch_project_list(skip_blacklisted=True):
    #
    # read configuration file
    #

    scriptdir = os.path.dirname(os.path.realpath(sys.argv[0]))
    with open(os.path.join(scriptdir, "config.yaml")) as f:
        conf = yaml.load(f)

    #
    # fetch project list, extract projects
    #

    Project = collections.namedtuple('Project', ['name', 'repo', 'branch', 'commit', 'builddep', 'alsoinstall', 'sourcedir', 'hacks', 'config'])

    project_list_url = "https://raw.githubusercontent.com/mesonbuild/meson/master/docs/markdown/Users.md"
    content = urllib.request.urlopen(project_list_url).read().decode()

    urls = {}
    for l in content.splitlines():
        if l.startswith(' - '):
            matches = re.finditer(r'\[(.*?)\]\((.*?)\)', l)
            for m in matches:
                name = m.group(1)
                url = m.group(2)

                # convert name to a form which is more likely to be a package name
                name = name.lower().replace(' ','-')

                # workaround freedesktop.org CA not in trusty (?)
                url = re.sub(r'http(s|)://cgit.freedesktop.org/', r'git://anongit.freedesktop.org/', url)

                urls[name] = url

    #
    # build list of Project namedtuples
    # (each project might only be in either Users.md or config.yaml)
    #

    projects = []
    for name in sorted(set(urls) | set(conf)):
            c = conf.get(name, None)
            if not c:
                c = {}

            if 'blacklisted' in c and skip_blacklisted:
                continue

            bd = c.get('builddep', True)
            if type(bd) is bool:
                if bd:
                    # if builddep is absent or True, just use the package name
                    bd = name
                else:
                    # if builddep is False, it's omitted
                    bd = None
            # otherwise it's an explicit package name

            commit = c.get('commit', None)
            if commit:
                if re.match(r'^[0-9a-fA-F]*$', commit):
                    # looks like a hash
                    reference = None
                else:
                    # looks like a branch or tag reference
                    reference = commit
                    commit = None
            else:
                # otherwise omitted, and script will default to master
                reference = None
                commit = None

            projects.append(Project(name = name,
                                    repo = c.get('repo-url', urls.get(name, 'unknown-url')),
                                    builddep = bd,
                                    alsoinstall = c.get('install', []),
                                    branch = reference,
                                    commit = commit,
                                    sourcedir = c.get('sourcedir', None),
                                    hacks = c.get('extra-commands', None),
                                    config = c.get('config', None),
            ))

    return projects

def shell_protect(s):
    # multiple commands in a subshell is too hard
    if s.startswith('('):
        return '"' + s + '"';

    return shlex.quote(s)
