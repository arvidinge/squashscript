import sys
import os
import argparse
import subprocess
from gitplumbing import get_cur_branch, p_branch_exists, create_squash_branch, checkout_branch, \
                        get_parent_commit, get_commits_since_last_fork, get_local_branch_list, \
                        reset_soft_to, reset_hard_to, stash_create, stash_apply, print_git_log_graph, \
                        get_commits_in_range, pull, diff_tree, commit, construct_commit_message, \
                        get_ref_sha, fetch


encoding = 'utf8'



def run(args):

    argsdict = parseargs(args)

    repopath = vars(argsdict)['PATH']
    branch = vars(argsdict)['BRANCH']
    base_commit = vars(argsdict)['COMMIT']

    repopath, branch, base_commit = validate_and_format_args(repopath, branch, base_commit)
    print_processed_args(repopath, branch, base_commit)

    fetch() # needed?

    # Save to restore at exit
    stashid = stash_create()
    if stashid is not None:
        reset_hard_to()
    originalbranch = get_cur_branch().replace('refs/heads/','')

    

    try:
        print(f'Checking out \'{branch}\'...')
        if branch != get_cur_branch().replace('refs/heads/',''):
            checkout_branch(branch)
        else:
            print(f'Already on branch \'{branch}\'.')

        if p_branch_exists(f'refs/heads/{branch}squash'):
            print(f'Squash branch for {branch} exists locally.')

            # (local,remote)
            # (1,1)
            if p_branch_exists(f'refs/remotes/origin/{branch}squash'):  
                print(f'Squash branch for {branch} exists on remote.')

                if diff_tree(f'refs/heads/{branch}squash', f'refs/remotes/origin/{branch}squash') is not None:  # User should pull squash branch themselves.
                    raise NotImplementedError(f'Branch \"{branch}\" differs from it\'s remote counterpart.')

                # same as case (1,0) at this point.
                commit_list = get_commits_in_range(f'refs/heads/{branch}', base_commit) 
                squashed_commits = commit_list[:commit_list.index(base_commit)] # base commit omitted

                squashbranch = f'{branch}squash'
                checkout_branch(squashbranch)

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(base_commit)
                reset_soft_to(squash_original_tip)
                commit('Diff baseline for following commit.')

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(branch)
                reset_soft_to(squash_original_tip)
                commit(construct_commit_message(squashed_commits))

                print_git_log_graph(squashbranch)
                print(f'NB: Recent commits at the bottom in above graph.\n')

            # (1,0)
            else:  
                print(f'Squash branch for {branch} doesn\'t exist on remote.')

                commit_list = get_commits_in_range(f'refs/heads/{branch}', base_commit) 
                squashed_commits = commit_list[:commit_list.index(base_commit)] # base commit omitted

                squashbranch = f'{branch}squash'
                checkout_branch(squashbranch)

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(base_commit)
                reset_soft_to(squash_original_tip)
                commit('Diff baseline for following commit.')

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(branch)
                reset_soft_to(squash_original_tip)
                commit(construct_commit_message(squashed_commits))

                print_git_log_graph(squashbranch)
                print(f'NB: Recent commits at the bottom in above graph.\n')

        else:
            print(f'Squash branch for {branch} doesn\'t exist locally.')
            
            # (0,1)
            if p_branch_exists(f'refs/remotes/origin/{branch}squash'):  
                
                print(f'Squash branch for {branch} exists on remote.')
                
                squashbranch = f'{branch}squash'
                checkout_branch(squashbranch)

                commit_list = get_commits_in_range(f'refs/heads/{branch}', base_commit) 
                squashed_commits = commit_list[:commit_list.index(base_commit)] # base commit omitted

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(base_commit)
                reset_soft_to(squash_original_tip)
                commit('Diff baseline for following commit.')

                squash_original_tip = get_ref_sha(f'refs/heads/{squashbranch}')
                reset_hard_to(branch)
                reset_soft_to(squash_original_tip)
                commit(construct_commit_message(squashed_commits))

                print_git_log_graph(squashbranch)
                print(f'NB: Recent commits at the bottom in above graph.\n')
            
            # (0,0)
            else:  
                print(f'Squash branch for {branch} doesn\'t exist on remote.')

                commit_list = get_commits_in_range(f'refs/heads/{branch}', base_commit) 
                squashed_commits = commit_list[:commit_list.index(base_commit)] # base commit omitted

                squashbranch = create_squash_branch(branch)
                checkout_branch(squashbranch)
                reset_soft_to(base_commit)
                commit(construct_commit_message(squashed_commits))

                print_git_log_graph(squashbranch)
                print(f'NB: Recent commits at the bottom in above graph.\n')
                
    except Exception as e:
        # Reset local repo to original state
        print(f'ERROR: {e}')
        print('Manually ensure your workspace has not been damaged. Not yet implemented programmatically.')
        pass
    finally:
        # Restore workspace state
        checkout_branch(originalbranch)
        if stashid is not None:
            stash_apply(stashid)



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