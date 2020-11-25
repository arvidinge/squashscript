import sys
import os
import argparse
import subprocess

# https://schacon.github.io/git/git.html#_low_level_commands_plumbing
CLIencoding = 'utf16'

def nyi(thing):
    print(f'{thing} not yet implemented. Exiting.')
    exit(0)


def run(args):

    argsdict = parseargs(args)

    repopath = vars(argsdict)['PATH']
    branch = vars(argsdict)['BRANCH']
    commit = vars(argsdict)['COMMIT']

    repopath, branch, commit = validate_and_format_args(repopath, branch, commit)

    print_processed_args(repopath, branch, commit)

    oldbranch = get_cur_branch()

    if p_branch_exists(f'refs/heads/{branch}squash'):

        print(f'Squash branch for {branch} exists locally.')

        if p_branch_exists(f'refs/remotes/origin/{branch}squash'):
            print(f'Squash branch for {branch} exists on remote.')
            # Pull, Figure out new base commit, Rebase.   Conflicts? Think through...
            nyi('')
            
        else:
            print(f'Squash branch for {branch} doesn\'t exist on remote.')
            # Figure out new base commit, Rebase.
            nyi('')

    else:

        print(f'Squash branch for {branch} doesn\'t exist locally.')

        if p_branch_exists(f'refs/remotes/origin/{branch}squash'):
            print(f'Squash branch for {branch} exists on remote.')
            # Pull, Figure out new base commit, Rebase.
            nyi('')

        else:
            print(f'Squash branch for {branch} doesn\'t exist on remote.')
            # Create, Rebase.   Easy case, start with this.
            # squashbranch = create_squash_branch(branch)
            # checkout_branch(squashbranch)

            base_commit = get_parent_commit(commit)
            commit_list = get_unique_commits(branch, get_local_branch_list())
            squashed_commits = commit_list[:commit_list.index(commit)]
            print(squashed_commits)
            # head_offset = commit_list.index(base_commit)
            
            # squash_to(base_commit, squashed_commits)


    #print_git_log_graph()


def squash_to(base_commit):
    subprocess.Popen(['git', 'reset', '--soft', f'{base_commit}']).communicate()
    subprocess.Popen(['git', 'reset', '--soft', f'{base_commit}']).communicate()


def get_parent_commit(commitish):
    out, err = subprocess.Popen(['git', 'rev-parse', '--short', f'{commitish}^'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return format_subprocess_stdout(out)


def checkout_branch(branch):
    out, err = subprocess.Popen(['git', 'checkout', f'{branch}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if format_subprocess_stdout(out).startswith('error'):
        print(format_subprocess_stdout(out))
        print('Exiting.')
        exit(-1)


def create_squash_branch(branch):
    subprocess.Popen(['git', 'branch', f'{branch}squash']).communicate()
    return f'{branch}squash'


def print_git_log_graph():
    proc = subprocess.Popen(['git', '--no-pager', 'log', '--graph', '--abbrev-commit', '--decorate', "--format=format:%C(bold blue)%h%C(reset) - %C(bold cyan)%aD%C(reset) %C(bold green)(%ar)%C(reset)%C(bold yellow)%d%C(reset)%n          %C(white)%<(85,trunc)%s%C(reset) %C(dim white)- %an%C(reset)", '--all'], stdout=subprocess.PIPE, stderr=None, shell=True)
    out = proc.communicate()[0] # input=bytes('q\n', encoding=CLIencoding) doesn't seem to cancel git log's prompt...
    out = format_subprocess_stdout(out)
    graph = out.splitlines()
    graph.reverse()
    for i in range(len(graph)):
        pass
        graph[i] = graph[i].replace('\\\\', '\\').replace('\\', '¤').replace('/', '\\').replace('¤', '/')

    for line in graph:
        print(line)


def validate_and_format_args(repopath, branch, commit):
    if repopath is 'DEFAULT':
        repopath = os.getcwd()

    try:
        os.chdir(repopath)
    except FileNotFoundError:
        print(f'{repopath} is not a valid path. Exiting.')
        exit(-1)
    
    if '.git' not in os.listdir():
        print(f'{os.getcwd()} is not a Git repository. Exiting.')
        exit(-1)
    
    if branch is 'DEFAULT':
        branch = get_cur_branch()

    # if not branch.startswith('refs/heads/'): # arg to script can be "-b refs/heads/feature" or just "-b feature"
    branch = branch.replace(f'refs/heads/', '')

    localbranches = get_local_branch_list()
    
    if branch not in localbranches:
        print(f'{branch} is not a local branch. Exiting.')
        exit(-1)

    branchcommits = get_unique_commits(branch, localbranches)

    if commit is 'DEFAULT':
        commit = branchcommits[-1] # Oldest unique commit ("bottom" of branch)
    
    if commit not in branchcommits:
        print(f'{commit} is not a commit, or is not unique to branch {branch}. Exiting.')
        exit(-1)
    

    return (repopath, branch, commit)


def get_unique_commits(branch, branchlist):
    locallist = branchlist.copy()
    locallist.remove(branch)

    command = ['git', 'rev-list', '--abbrev-commit', f'{branch}']

    for branch_to_omit in locallist:
        if branch_to_omit != f'{branch}squash':
            command.append(f'^{branch_to_omit}') # Result: git rev-list branch_to_include ^branch_to_omit

    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    
    return out.splitlines()


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
    parser.add_argument('-c', type=str, dest='COMMIT', default='DEFAULT', help='Commitish of the first commit to be included in squash. Default: The child of the most recent commit that is not unique to the branch specified by -b.')

    return parser.parse_args()


def get_cur_branch():
    '''Get the currently checked out Git branch in cwd.
    
    pre: cwd is a Git repository.
    '''
    out, err = subprocess.Popen(['git', 'symbolic-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return format_subprocess_stdout(out)


def get_local_branch_list():
    '''Get a list of local Git branches in cwd.
    
    pre: cwd is a Git repository.
    '''
    out, err = subprocess.Popen(['git', 'show-ref', '--heads'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)

    branches = []
    for sha_rev in out.splitlines():
        sha, rev = sha_rev.split(' ')
        branches.append(rev.replace(f'refs/heads/', ''))

    return branches


def p_branch_exists(branch):
    out, err = subprocess.Popen(['git', 'show-ref', '--verify', f'{branch}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)

    if out.endswith('squash'):
        return True
    return False


def format_subprocess_stdout(stdout):
    retstr = ''
    for c in str(stdout).replace('\\n', '\n'):
        retstr += c
    retstr = retstr.split('b\'', 1)[-1]
    retstr = retstr.rsplit('\'', 1)[0]
    retstr = retstr.rsplit('\n', 1)[0]

    return retstr


def get_branch_name_from_ref(sha):
    out, err = subprocess.Popen(['git', 'name-rev', f'{sha}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return format_subprocess_stdout(out)


if __name__ == '__main__':
    run(sys.argv)