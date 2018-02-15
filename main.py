#!/usr/bin/env python3

#
# Construct a .travis.yml to run the git master of meson on the list of projects
#

import collections
import re
import sys
import yaml
import urllib.request

Project = collections.namedtuple('Project', ['name', 'repo', 'branch', 'builddep', 'sourcedir', 'hacks'])

builddep = {
    'aqemu': ['qtbase5-dev', 'libvncserver-dev'],
    'budgie_desktop': ['valac', 'libgtk-3-dev'],
    'casync': ['libzstd-dev'],
    'cinnamon-desktop': ['libgtk-3-dev', 'libxkbfile-dev', 'libpulse-dev', 'gobject-introspection', 'libgirepository1.0-dev'],
    'dbus-broker': ['python-docutils'],
    'geary': ['valac'],
    'glib': ['libmount-dev'],
    'gnome_builder': ['libdazzle-1.0-dev'],
    'gnome_mpv': ['libgtk-3-dev'],
    'gnome_recipes': ['libsoup2.4-dev', 'libgoa-1.0-dev'],
    'gnome_software': ['libappstream-glib-dev'],
    'gnome_twitch': ['libgtk-3-dev'],
    'grilo_plugins': ['libgrilo-0.3-dev'],
    'gtkdapp': ['gdc', 'libgtkd-3-dev'],
    'hardcode-tray': ['libgirepository1.0-dev', 'libgtk-3-dev'],
    'hexchat': ['libproxy-dev', 'libcanberra-dev', 'libdbus-glib-1-dev', 'libgtk2.0-dev', 'libnotify-dev', 'libluajit-5.1-dev', 'libperl-dev'],
    'kiwix_libraries': ['libzim-dev'],
    'libdrm': ['libpciaccess-dev'],
    'libhttpseverywhere': ['valac', 'libjson-glib-dev', 'libsoup2.4-dev', 'libgee-0.8-dev', 'libarchive-dev', 'gobject-introspection'],
    'lightdm-webkit2-greeter': ['libdbus-glib-1-dev', 'liblightdm-gobject-1-dev', 'libgtk-3-dev'],
    'miraclecast': ['libudev-dev'],
    'nemo': ['libgtk-3-dev', 'libgirepository1.0-dev', 'libnotify-dev', 'libcinnamon-desktop-dev'],
    'outlier': ['libxml2-dev'],
    'pango': ['libfribidi-dev'],
    'pipewire': ['libdbus-1-dev', 'libasound2-dev', 'libv4l-dev', 'libudev-dev'],
    'pitivi': ['intltool', 'itstool','libgstreamer1.0-dev'],
    'polari': ['gjs'],
    'sshfs': ['libfuse-dev'],
    'systemd': ['gperf', 'libcap-dev','libmount-dev'],
    'taisei_project': ['libsdl2-dev'],
    'valum': ['valac', 'libsoup2.4-dev'],
    'wayland_and_weston': ['libudev-dev', 'libmtdev-dev', 'libevdev-dev', 'libwacom-dev'],
    'wlroots': ['libwayland-dev', 'libegl1-mesa-dev', 'wayland-protocols'],
    'xi-gtk': ['valac', 'libgtk-3-dev'],
}

url_remap = {
    'http://dpdk.org/ml/archives/dev/2018-January/089724.html': 'git://dpdk.org/dpdk',
    'https://www.frida.re/': 'https://github.com/frida/frida.git',
    'https://wiki.gnome.org/Apps/Geary': 'https://git.gnome.org/browse/geary',
    'https://ebassi.github.io/graphene/': 'git://github.com/ebassi/graphene',
    'https://mail.gnome.org/archives/grilo-list/2017-February/msg00000.html': 'https://git.gnome.org/browse/grilo',
    'https://git.gnome.org/browse/grilo-plugins/commit/?id=ea047c4fb63e90268eb795ed91a09a2be5068a4c': 'https://git.gnome.org/browse/grilo-plugins',
    'https://github.com/grindhold/libhttpseverywhere': 'https://git.gnome.org/browse/libhttpseverywhere',  # moved
    'https://www.mesa3d.org/': 'git://anongit.freedesktop.org/mesa/mesa',
    'https://git.gnome.org/browse/nautilus/commit/?id=ed5652c89ac0654df2e82b54b00b27d51c825465': 'https://gitlab.gnome.org/GNOME/nautilus.git',
    'https://pipewire.org/': 'https://github.com/PipeWire/pipewire.git',
    'http://pitivi.org/': 'https://git.gnome.org/browse/pitivi',
    'https://wiki.gnome.org/Apps/Sysprof': 'git://git.gnome.org/sysprof',
    'https://taisei-project.org/': 'https://github.com/taisei-project/taisei.git',
    'https://lists.freedesktop.org/archives/wayland-devel/2016-November/031984.html': 'git://anongit.freedesktop.org/wayland/libinput', # not merged yet...
    'https://github.com/facebook/zstd/commit/4dca56ed832c6a88108a2484a8f8ff63d8d76d91': 'https://github.com/facebook/zstd.git'
}

blacklist = [
    'arduino_sample_project',  # work out how to setup cross-env
    'budgie_desktop',  # needs a later glib than in trusty
    'casync',  # zstd not in trusty?
    'dxvk',  # work out how to install vulcan devkit
    'emeus', # needs a later glib than in trusty
    'frida', # no meson.build in top-level directory ?!?
    'fwupd', # needs a later gio than in trusty
    'geary', # needs a later glib than in trusty
    'glib',  # needs a later libmount than in trusty
    'gnome_builder', # needs libdazzle, not in trusty
    'gnome_mpv', # needs a later glib than in trusty
    'gnome_software', # need libappstream-glib, not in trusty
    'gnome_twitch', # needs a later glib than in trusty
    'grilo', # needs a later gio than in trusty
    'grilo_plugins', # needs libgrilo-0.3-dev, not in trusty
    'gtk+', # fallsback to building glib, then fails to use it...
    'gtkdapp', # needs libgtkd-3-dev, not in trusty
    'igt', # needs a later libdrm than in trusty
    'json-glib', # needs later gobject than in trusty
    'kiwix_libraries', # libzim-dev in trusty is too old to have a .pc file
    'libgit2-glib', # needs a later glib than in trusty
    'lightdm-webkit2-greeter', # needs later gtk+-3.0 than in trusty
    'mesa', # needs later libdrm than in trusty
    'miraclecast', # needs later systemd than in trusty
    'nemo', # needs cinnamon-desktop, not in trusty
    'pango', # needs later fribidi than in trusty
    'pipewire', # udev fails to install (due to https://github.com/travis-ci/packer-templates/issues/584?)
    'pitivi', # needs a later gstreamer than in trusty
    'polari', # needs a later gio than in trusty
    'radare2', # needs libcapstone, not in trusty (?)
    'sshfs', # needs fuse3, not in trusty
    'sysprof', # needs later gcc than in trusty
    'systemd', # needs a later libmount than in trusty
    'taisei_project', # needs a later sdl2 than in trusty
    'wayland_and_weston', # needs a later libwacom than in trusty
    'wlroots', # needs wayland-protocols, not in trusty
    'xi-gtk', # needs later gtk+-3.0 than in trusty
    'xorg', # needs a later xproto than in trusty
]

# broken by PR #3035
blacklist += [
    'dbus-broker',
    'gnome_recipes',
    'nautilus',
]

# if we don't want to checkout master, use a branch, tag or hash
branch_overrides = {
    'lightdm-webkit2-greeter': 'stable',
}

# if meson.build is not in the root of the source checkout
sourcedir = {
    'zstandard': 'contrib/meson',
}

hacks = {
    'szl': 'git submodule update --init',  # uses submodules, but not as subprojects
}

# fetch project list, extract projects
project_list_url = "https://raw.githubusercontent.com/mesonbuild/meson/master/docs/markdown/Users.md"
content = urllib.request.urlopen(project_list_url).read().decode()

projects = []
for l in content.splitlines():
    if l.startswith(' - '):
        matches = re.finditer(r'\[(.*?)\]\((.*?)\)', l)
        for m in matches:
            name = m.group(1)
            url = m.group(2)

            name = name.lower().replace(' ','_')

            if name in blacklist:
                continue

            url = url_remap.get(url, url)

            # workaround freedesktop.org CA not in trusty (?)
            url = re.sub(r'http(s|)://cgit.freedesktop.org/', r'git://anongit.freedesktop.org/', url)

            projects.append(Project(name = name,
                                    repo = url,
                                    builddep = builddep.get(name, []),
                                    branch = branch_overrides.get(name, 'master'),
                                    sourcedir = sourcedir.get(name, '.'),
                                    hacks = hacks.get(name, 'true')))

# read template.yaml and insert project list into build matrix
with open("template.yaml", 'r') as f:
    output = yaml.load(f)

matrix = [{'env': ['NAME=%s' % p.name, 'REPO=%s' % p.repo, 'BRANCH=%s' % p.branch, 'SOURCEDIR=%s' % p.sourcedir, 'HACKS="%s"' % p.hacks],
           'addons': { 'apt': {'packages': p.builddep + ['ninja-build'] }}} for p in projects]

output['matrix'] = {'include': matrix}

print(yaml.dump(output, default_flow_style=False))
