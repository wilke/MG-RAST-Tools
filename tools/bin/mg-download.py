#!/usr/bin/env python

import sys
from operator import itemgetter
from optparse import OptionParser
from mglib import *

prehelp = """
NAME
    mg-download

VERSION
    %s

SYNOPSIS
    mg-download [ --help, --user <user>, --passwd <password>, --token <oAuth token>, --project <project id>, --metagenome <metagenome id>, --file <file id> --dir <directory name> --list <list files for given id>]

DESCRIPTION
    Retrieve metadata for a metagenome.
"""

posthelp = """
Output
    List available files (name and size) for given project or metagenome id.
      OR
    Download of file(s) for given project, metagenome, or file id.

EXAMPLES
    mg-download --metagenome mgm4441680.3 --list

SEE ALSO
    -

AUTHORS
    %s
"""

# download a file
def file_download(auth, info, dirpath="."):
    fhandle = open(os.path.join(dirpath, file_name(info)), 'w')
    sys.stdout.write("Downloading %s for %s ... "%(file_name(info), info['id']))
    file_from_url(info['url'], fhandle, auth=auth)
    fhandle.close()
    sys.stdout.write("Done\n")

# get correct name - deal with subset files
def file_name(info):
    if (info['data_type'] == "passed") or (info['data_type'] == "removed"):
        return info['stage_id']+'.'+info['stage_name']+'.fna'
    elif info['stage_name'] == "upload":
        return info['stage_id']+'.'+info['stage_name']+'.'+info['file_format']
    else:
        return info['file_name']

def main(args):
    OptionParser.format_description = lambda self, formatter: self.description
    OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = OptionParser(usage='', description=prehelp%VERSION, epilog=posthelp%AUTH_LIST)
    parser.add_option("", "--url", dest="url", default=API_URL, help="communities API url")
    parser.add_option("", "--user", dest="user", default=None, help="OAuth username")
    parser.add_option("", "--passwd", dest="passwd", default=None, help="OAuth password")
    parser.add_option("", "--token", dest="token", default=None, help="OAuth token")
    parser.add_option("", "--project", dest="project", default=None, help="project ID")
    parser.add_option("", "--metagenome", dest="metagenome", default=None, help="metagenome ID")
    parser.add_option("", "--file", dest="file", default=None, help="file ID for given project or metagenome")
    parser.add_option("", "--dir", dest="dir", default=".", help="directory to do downloads")
    parser.add_option("", "--list", dest="list", action="store_true", default=False, help="list files and their info for given ID")
    
    # get inputs
    (opts, args) = parser.parse_args()
    if not (opts.project or opts.metagenome):
        sys.stderr.write("ERROR: a project or metagenome id is required\n")
        return 1
    if not os.path.isdir(opts.dir):
        sys.stderr.write("ERROR: dir '%s' does not exist\n"%opts.dir)
        return 1
    downdir = opts.dir
    
    # get auth
    token = get_auth_token(opts)
    
    # get metagenome list
    mgs = []
    if opts.project:
        url  = opts.url+'/project/'+opts.project+'?verbosity=full'
        data = obj_from_url(url, auth=token)
        for mg in data['metagenomes']:
            mgs.append(mg[0])
    elif opts.metagenome:
        mgs.append(opts.metagenome)
    
    # get file lists
    all_files = {}
    for mg in mgs:
        url  = opts.url+'/download/'+mg
        data = obj_from_url(url, auth=token)
        all_files[mg] = data['data']
    
    # just list
    if opts.list:
        safe_print("Metagenome\tFile Name\tFile ID\tChecksum\tByte Size\n")
        for mg, files in all_files.iteritems():
            for f in files:
                fsize = f['file_size'] if f['file_size'] else 0
                safe_print("%s\t%s\t%s\t%s\t%d\n"%(mg, file_name(f), f['file_id'], f['file_md5'], fsize))
        sys.stdout.close()
        return 0
    
    # download all in dirs by ID
    if opts.project:
        downdir = os.path.join(downdir, opts.project)
        if not os.path.isdir(downdir):
            os.mkdir(downdir)
    for mg, files in all_files.iteritems():
        mgdir = os.path.join(downdir, mg)
        if not os.path.isdir(mgdir):
            os.mkdir(mgdir)
        for f in files:
            if opts.file:
                if f['file_id'] == opts.file:
                    file_download(token, f, dirpath=mgdir)
            else:
                file_download(token, f, dirpath=mgdir)
    
    return 0


if __name__ == "__main__":
    sys.exit( main(sys.argv) )
