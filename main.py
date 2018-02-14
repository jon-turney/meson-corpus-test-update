#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import collections
import re
import sys
import yaml
import urllib.request

Project = collections.namedtuple('Project', ['name', 'repo', 'builddep'])

builddep = {
    'AQEMU': ['qtbase5-dev', 'libvncserver-dev'],
    'Budgie Desktop': ['valac', 'libgtk-3-dev'],
    'casync': ['libzstd-dev'],
    'cinnamon-desktop': ['libgtk-3-dev', 'libxkbfile-dev', 'libpulse-dev', 'gobject-introspection', 'libgirepository1.0-dev'],
    'dbus-broker': ['python-docutils'],
    'Geary': ['valac'],
    'GLib': ['libmount-dev'],
    'Gnome Builder': ['libdazzle-1.0-dev'],
    'Gnome MPV': ['libgtk-3-dev'],
    'Gnome Recipes': ['libsoup2.4-dev', 'libgoa-1.0-dev'],
    'Gnome Software': ['libappstream-glib-dev'],
    'Gnome Twitch': ['libgtk-3-dev'],
    'GtkDApp': ['gdc', 'libgtkd-3-dev'],
    'Hardcode-Tray': ['libgirepository1.0-dev', 'libgtk-3-dev'],
    'HexChat': ['libproxy-dev', 'libcanberra-dev', 'libdbus-glib-1-dev'],
    'Libdrm': ['libpciaccess-dev'],
    'outlier': ['libxml2-dev'],
    'orc' : [],
}

url_remap = {
    'http://dpdk.org/ml/archives/dev/2018-January/089724.html': 'git://dpdk.org/dpdk',
    'https://www.frida.re/': 'https://github.com/frida/frida.git',
    'https://wiki.gnome.org/Apps/Geary': 'https://git.gnome.org/browse/geary',
    'https://ebassi.github.io/graphene/': 'git://github.com/ebassi/graphene',
    'https://mail.gnome.org/archives/grilo-list/2017-February/msg00000.html': 'https://git.gnome.org/browse/grilo',
    'https://github.com/grindhold/libhttpseverywhere': 'https://git.gnome.org/browse/libhttpseverywhere',  # moved
}

blacklist = [
    'Arduino sample project',  # work out how to setup cross-env
    'Budgie Desktop',  # needs a later glib than in trusty
    'casync',  # zstd not in trusty?
    'DXVK',  # work out how to install vulcan devkit
    'Emeus', # needs a later glib than in trusty
    'Frida', # No meson.build in top-level directory ?!?
    'fwupd', # needs a later gio than in trusty
    'Geary', # needs a later glib than in trusty
    'GLib',  # needs a later libmount than in trusty
    'Gnome Builder', # needs libdazzle, not in trusty
    'Gnome MPV', # needs a later glib than in trusty
    'Gnome Software', # need libappstream-glib, not in trusty
    'Gnome Twitch', # needs a later glib than in trusty
    'Grilo', # needs a later gio than in trusty
    'GTK+', # fallsback to building glib, then fails to use it...
    'GtkDApp', # needs libgtkd-3-dev, not in trusty
    'IGT', # needs a later libdrm than in trusty
    'Json-glib', # needs later gobject than in trusty
    'Libgit2-glib', # needs a later glib than in trusty
]

# broken by PR #3035
blacklist += [
    'dbus-broker',
    'Gnome Recipes',
]

# fetch project list, extract projects
project_list_url = "https://raw.githubusercontent.com/mesonbuild/meson/master/docs/markdown/Users.md"
content = urllib.request.urlopen(project_list_url).read().decode()

projects = []
for l in content.splitlines():
    m = re.search(r'\[(.*?)\]\((.*?)\)', l)
    if m:
        name = m.group(1)
        url = m.group(2)

        if name in blacklist:
            continue

        url = url_remap.get(url, url)

        # workaround freedesktop.org CA not in trusty (?)
        url = url.replace('https://cgit.freedesktop.org/', 'git://anongit.freedesktop.org/')

        projects.append(Project(name = name.lower().replace(' ','_'),
                                repo = url,
                                builddep = builddep.get(name, [])))

# XXX: truncate
projects = projects[:18]

# read template.yaml and insert project list into build matrix
with open("template.yaml", 'r') as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME="%s"' % p.name, 'REPO=%s' % p.repo],
           'addons': { 'apt': {'packages': p.builddep + ['ninja-build'] }}} for p in projects]

output['matrix'] = {'include': matrix}

print(yaml.dump(output, default_flow_style=False))
