import sys
import os
import argparse
import subprocess
from util import format_subprocess_stdout

# DOCUMENTATION:
# https://schacon.github.io/git/git.html#_low_level_commands_plumbing

CLIencoding = 'utf8'


def stash_all():
    subprocess.Popen(['git', 'stash', '--all']).communicate()

def stash_pop():
    subprocess.Popen(['git', 'stash', 'pop']).communicate()


def reset_soft_to(base_commit, squashed_commits):
    subprocess.Popen(['git', 'reset', '--soft', f'{base_commit}']).communicate()
    subprocess.Popen(['git', 'commit', '-m', f'{construct_commit_message(squashed_commits)}']).communicate()


def construct_commit_message(squashed_commits):
    retstr = f'squash.py: Auto combined {len(squashed_commits)} commits: \r\n\r\n'
    for i in range(len(squashed_commits) - 1):
        retstr += f'{i+1}: {squashed_commits[i]} {get_commit_message(squashed_commits[i])}\r\n'
    return retstr


def get_commit_message(commitish):
    out, err = subprocess.Popen(['git', 'rev-list', '--format=%B', '--max-count=1', f'{commitish}^'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out).splitlines() 
    if type(out) is list:
        return out[-1]


def get_parent_commit(commitish):
    out, err = subprocess.Popen(['git', 'rev-parse', '--short', f'{commitish}^'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    if len(out) > 7: # Normal
        return out
    return commitish # Initial commit has no parent
    

def checkout_branch(branch):
    out, err = subprocess.Popen(['git', 'checkout', f'{branch}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if format_subprocess_stdout(out).startswith('error'):
        print(format_subprocess_stdout(out))
        print('Exiting.')
        exit(-1)


def create_squash_branch(branch):
    subprocess.Popen(['git', 'branch', f'{branch}squash']).communicate()
    return f'{branch}squash'


def print_git_log_graph(head_in_focus=None):
    print()
    out, err = subprocess.Popen(['git', '--no-pager', 'log', '--graph', '--abbrev-commit', '--decorate', "--format=format:%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%<(25,trunc)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)", '--all'], stdout=subprocess.PIPE, stderr=None, shell=True).communicate()
    out = format_subprocess_stdout(str(out, encoding=CLIencoding) + '\n')

    graph = out.splitlines()
    graph.reverse()
    
    # If head to focus graph display around given, truncate lines around it and emphasize head's line ( <<<<< ).
    # Else, focus graph on last line.
    maxlines = 16

    focusindex = len(graph)-1
    for i in range(len(graph)):
        graph[i] = graph[i].replace('\\\\', '\\').replace('\\', '¤').replace('/', '\\').replace('¤', '/')

        if type(head_in_focus) is str and head_in_focus in graph[i]: # Line with the new squash commit
            focusindex = i
            graph[i] += f'       <<<<< Squashed commit(s) to {head_in_focus}' # Emphasize the line
    
    graph = graph[(0 if focusindex<(maxlines/2) else int(focusindex-(maxlines/2))) : (int(len(graph)) if abs(len(graph)-focusindex) < (maxlines/2) else int(focusindex+(maxlines/2)))]

    if not focusindex<(maxlines/2): # Start was truncated
        print(f'GIT LOG GRAPH:\n...')
    for line in graph:
        print(line)
    if not abs(len(graph)-focusindex) < (maxlines/2): # End was truncated
        print(f'...')

    print()


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


def get_branch_name_from_ref(sha):
    out, err = subprocess.Popen(['git', 'name-rev', f'{sha}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return format_subprocess_stdout(out)


def p_branch_exists(branch):
    out, err = subprocess.Popen(['git', 'show-ref', '--verify', f'{branch}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)

    if out.endswith('squash'):
        return True
    return False



if __name__ == '__main__': # If you want to test something, place calls here.
    import os
    os.chdir('C:\\Users\\AXNCYB\\source\\repos\\cbxConverter')
    print_git_log_graph('issue25squash')
