#!/usr/bin/env python

# author: cmccoy <cmccoy@wayfair.com>
# version: 1.0
# tool for printing out compiled puppet catalogs based on current site.pp or given class
import os
import sys
import shlex
import subprocess
import json
import time
from optparse import OptionParser

parser = OptionParser(version="%prog .5")
parser.add_option("-V", "--vardir", dest="vardir", default="/var/puppet/",
        help="Set the VARDIR for puppet to use")
parser.add_option("-H", "--host", dest="host", default=False,
        help="Class to apply changes to")
parser.add_option("-s", "--store", dest="storedir", default=False,
        help="Where to store compiled catalog")
parser.add_option("--modules", dest="moddir", default=False,
        help="Where are your modules [defaults to puppet master settings]")
parser.add_option("--manifests", dest="mandir", default=False,
        help="Where are your manifests [defaults to puppet master settings]")
parser.add_option("--class", dest="node_class", default=False,
        help="A single class you would like to apply [if not specified will use site.pp or classfile")
parser.add_option("--classfile", dest="classfile", default=False,
        help="A file with a list of classes [if not specified will use site.pp or given --class]")
parser.add_option("--diff", dest="difffile", default=False,
        help="Output the changes between two two catalogs")

(options, args) = parser.parse_args()

def main(options, args):
    valid = is_valid(options)
    if valid > 0:
        sys.exit(valid)

    # base command 
    command_line = "puppet master --color off --compile %s" % options.host
    if options.vardir:
        command_line = build_command([command_line, '--vardir', options.vardir])
    if options.moddir:
        command_line = build_command([command_line, '--modulespath', options.moddir])
    if options.mandir:
        command_line = build_command([command_line, '--manifestdir', options.mandir])

    # setup manifest to be used
    site_file = False
    if not site_file and options.node_class:
        site_file = make_site_file(options.host, otpions.node_class)
        command_line = build_command([command_line, '--manifestdir', '/tmp'])
    if not site_file and options.classfile:
        site_file = options.classfile
        command_line = build_command([command_line, '--manifestdir', os.path.dirname(options.classfile)])

    if site_file:
        command_line = build_command([command_line, '--manifest', site_file])

    # prepare the command to be used
    cmd = shlex.split(command_line)

    
    # prepping the execution
    store_file = None
    pretty_path = None
    json_path = None

    result = 0
    if options.storedir:
        json_path = os.path.join(options.storedir, 'json')
        pretty_path = os.path.join(options.storedir, 'pretty')
        if not os.path.isdir(json_path):
            os.mkdir(json_path) # this is recursive
        if not os.path.isdir(pretty_path):
            os.mkdir(pretty_path) # nor is this (recursive)

        store_file = os.path.join(json_path, '%s.json.tmp' % options.host)
        store_file_h = open(store_file, 'w')
        pretty_file = os.path.join(pretty_path, '%s.txt.%s' % (options.host, str(time.time())))

    result = subprocess.call(cmd, stdout=store_file_h, stderr=None)
    make_pretty(store_file, pretty_file)


    if options.storedir:
        json_path = os.path.join(options.storedir, 'json')
        orig =  os.path.join(json_path, '%s.json' % options.host)
        tmp =  os.path.join(json_path, '%s.json.tmp' % options.host)
        show_diff(orig, tmp)
        try:
            os.rename(tmp, orig)
        except:
            pass

    print command_line
    return result

def make_site_file(node, node_class):
    site_file = '/tmp/site.pp.%s' os.getpid()
    site_file_h = open(site_file, 'w')
    data = "node %s {\n\tinclude %s\n}" % (node, node_class)
    site_file_h.write(data)
    site_file_h.close()
    return site_file

def build_command(*args):
    command = ' '.join(args)
    return command

def make_pretty(data, output):
    f = open(data)
    out = open(output, 'w')
    f_json = json.loads(f.readlines()[-1])
    f.close()
    out.write(json.dumps(f_json, sort_keys=True, indent=2))
    out.close()

def show_diff(orig, new):
    if not os.path.isfile(orig):
        return 0
    orig_h = open(orig, 'r')
    if not os.path.isfile(new):
        return 0
    new_h = open(new, 'r')

    # we only care about the last line
    orig_json = json.loads(orig_h.readlines()[-1])
    new_json = json.loads(new_h.readlines()[-1])




# determines the validity of the options given
def is_valid(options):
    result = 0
    #determine if options are valid
    if not os.path.isdir(options.vardir):
        print "var dir doesn't exist"
        result += 1 # var dir does not exist

    if not options.host:
        print "you must specify a host"
        result += 1

    if options.storedir and not os.path.isdir(options.storedir):
        print "storage directory must exist"
        result += 1

    if options.moddir and not os.path.isdir(options.moddir):
        print "modules directory must exist"
        result += 1

    if options.mandir and not os.path.isdir(options.mandir):
        print "manifests directory must exist"
        result += 1

    if options.classfile and not os.path.isfile(options.classfile):
        print "classfile must exist"
        result += 1

    if not options.node_class and not options.classfile and not options.mandir:
        print "must specify one of --class --classfile or --manifests"
        result += 1

    return result


if __name__ == '__main__':
    main(options, args)
