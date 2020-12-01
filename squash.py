import sys
import os
import argparse
import subprocess
from gitplumbing import get_cur_branch, p_branch_exists, create_squash_branch, checkout_branch, \
                        get_parent_commit, get_commits_since_last_fork, get_local_branch_list, \
                        reset_soft_to, reset_hard, stash_create, stash_apply, print_git_log_graph

encoding = 'utf8'



def run(args):

    argsdict = parseargs(args)

    repopath = vars(argsdict)['PATH']
    branch = vars(argsdict)['BRANCH']
    commit = vars(argsdict)['COMMIT']

    repopath, branch, commit = validate_and_format_args(repopath, branch, commit)
    print_processed_args(repopath, branch, commit)

    # Save to restore at exit
    stashid = stash_create()
    reset_hard()
    originalbranch = get_cur_branch().replace('refs/heads/','')
    checkout_branch(branch)

    try:
        if p_branch_exists(f'refs/heads/{branch}squash'):

            print(f'Squash branch for {branch} exists locally.')

            if p_branch_exists(f'refs/remotes/origin/{branch}squash'):
                print(f'Squash branch for {branch} exists on remote.')
                # 11: Pull, Figure out new base commit, Rebase.   Conflicts? Think through...
                raise NotImplementedError("11: Pull, Figure out new base commit, Rebase.   Conflicts? Think through...")
                
            else:
                print(f'Squash branch for {branch} doesn\'t exist on remote.')
                # 10: Figure out new base commit, Rebase.
                raise NotImplementedError("10: Figure out new base commit, Rebase.")

        else:

            print(f'Squash branch for {branch} doesn\'t exist locally.')

            if p_branch_exists(f'refs/remotes/origin/{branch}squash'):
                print(f'Squash branch for {branch} exists on remote.')
                
                # 01: Pull, Figure out new base commit, Rebase.
                raise NotImplementedError("01: Pull, Figure out new base commit, Rebase.")

            else:
                print(f'Squash branch for {branch} doesn\'t exist on remote.')
                # 00: Create branch, soft reset to parent of first commit in range, commit.   Easy case, start with this.

                commit_list = get_commits_since_last_fork(f'refs/heads/{branch}') # you assume commit was not given
                squashed_commits = commit_list[:commit_list.index(commit)+1] # base commit cannot be in this list.

                squashbranch = create_squash_branch(branch)
                checkout_branch(squashbranch)
                reset_soft_to(commit, squashed_commits)
                
    except Exception as e:
        # Reset local repo to original state
        print(f'ERROR: {e}')
        print('Manually ensure the repo has not been damaged. Not yet implemented programmatically.')
        pass
    finally:
        # Restore workspace state
        checkout_branch(originalbranch)
        stash_apply(stashid)

    print_git_log_graph(squashbranch)

    print(f'NB: Recent commits at the bottom in above graph.\n')



def validate_and_format_args(repopath, branch, commit):
    if repopath is 'DEFAULT':
        repopath = os.getcwd()

    try:
        os.chdir(repopath)
    except FileNotFoundError:
        print(f'{repopath} is not a valid path. Exiting.')
        exit(0)
    
    if '.git' not in os.listdir():
        print(f'{os.getcwd()} is not a Git repository. Exiting.')
        exit(0)
    
    if branch is 'DEFAULT':
        branch = get_cur_branch().replace(f'refs/heads/', '')
        print(f'Branch flag omitted, default branch (currently checked out): {branch}.')
        while(True):
            ans = input(f'Do you wish to squash {branch}? (y/n): ')
            if ans.lower().strip() == 'y':
                break
            elif ans.lower().strip() == 'n':
                print('Exiting.')
                exit(0)
            else:
                print('Invalid input.')

    # arg to script can be "-b refs/heads/feature" or just "-b feature"
    branch = branch.replace(f'refs/heads/', '')

    if str(branch).endswith("squash"):
        print(f'Selected branch is a squash branch: {branch}. Exiting.')
        exit(0)

    localbranches = get_local_branch_list()
    if branch not in localbranches:
        print(f'{branch} is not a local branch. Exiting.')
        exit(0)

    branchcommits = get_commits_since_last_fork(f'refs/heads/{branch}')
    if len(branchcommits) < 2:
        print(f'Fewer than two commits selected for squash. Commit list:')
        print(f'{branchcommits}')
        print(f'Exiting.')
        exit(0)

    if commit is 'DEFAULT':
        commit = get_parent_commit(branchcommits[-1]) # "Fork" commit ("base" of branch)
        if commit is None: # Initial commit has no parent
            commit = branchcommits[-1]
    
    # if commit not in branchcommits:
    #     print(f'{commit} is either not a commit or is not unique to branch {branch}. \nBranchcommits: {branchcommits}\nExiting.')
    #     exit(-1)
    
    return (repopath, branch, commit)


def print_processed_args(repo, branch, commit):
    print(f'\nREPO:\t{repo}')
    print(f'BRANCH:\t{branch}')
    print(f'COMMIT:\t{commit}\n')


def parseargs(args):
    # Git repo's README.md description
    parser = argparse.ArgumentParser(description='Squashes a range of commits on a Git branch (source) into a new, single commit. \
                                                  The new commit is placed on a complementary (target) review branch (source is unaffected by the operation). \
                                                  This script enables you to view all changes made on the source branch in several commits on a single GitHub commit page, which is handy for reviewing code.') 
    
    parser.add_argument('-p', type=str, dest='PATH', default='DEFAULT', help='Path to the repo.\nDefault: Current working directory (place and run squash.py in the repo).')
    parser.add_argument('-b', type=str, dest='BRANCH', default='DEFAULT', help='The branch for which a complementary squash branch will be created (if one doesn\'t exist), and from which commits will be squashed. Default: currently checked out branch.')
    parser.add_argument('-c', type=str, dest='COMMIT', default='DEFAULT', help='Commitish of the parent of the first commit to be included in squash. Last commit before any changes to be reviewed were introduced. Default: The most recent commit reachable from [BRANCH] that has two or more children (most recent "fork").')

    return parser.parse_args()




if __name__ == '__main__':
    run(sys.argv)