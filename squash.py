import sys
import os
import argparse
import subprocess


def run(args):

    argsdict = parseargs(args)

    repopath = vars(argsdict)['PATH']
    branch = vars(argsdict)['BRANCH']
    commit = vars(argsdict)['COMMIT']

    if repopath is "DEFAULT":
        repopath = os.getcwd()

    try:
        os.chdir(repopath)
    except FileNotFoundError:
        print(f'{repopath} is not a valid path.')
        exit(-1)

    subprocess.call(['git', 'mktree'])

    
def parseargs(args):
    # Git repo's README.md description
    parser = argparse.ArgumentParser(description='Squashes a range of commits on a Git branch (source) into a new, single commit. \
                                                  The new commit is placed on a complementary (target) review branch (source is unaffected by the operation). \
                                                  This script enables you to view all changes made on the source branch in several commits on a single GitHub commit page, which is handy for reviewing code.') 
    
    parser.add_argument('-p', type=str, dest='PATH', default='DEFAULT', help='Path to the repo.\nDefault: Current working directory (place and run squash.py in the repo).')
    parser.add_argument('-b', type=str, dest='BRANCH', default='DEFAULT', help='The branch for which a complementary squash branch will be created (if one doesn\'t exist), and from which commits will be squashed. Default: currently checked out branch.')
    parser.add_argument('-c', type=str, dest='COMMIT', default='DEFAULT', help='Commitish of the first commit to be included in squash. Default: The child of the most recent commit that is not unique to the branch specified by -b.')

    return parser.parse_args()


if __name__ == '__main__':
    run(sys.argv)