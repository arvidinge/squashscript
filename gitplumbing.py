import sys
import os
import argparse
import subprocess
from util import format_subprocess_stdout
import re

from time import sleep

# DOCUMENTATION:
# https://schacon.github.io/git/git.html#_low_level_commands_plumbing

encoding = 'utf8'


def stash_all():
    subprocess.Popen(['git', 'stash', '--all'], encoding=encoding).communicate()

def stash_pop():
    subprocess.Popen(['git', 'stash', 'pop'], encoding=encoding).communicate()


def reset_soft_to(base_commit, squashed_commits):
    subprocess.Popen(['git', 'reset', '--soft', f'{base_commit}'], encoding=encoding).communicate()
    subprocess.Popen(['git', 'commit', '-m', f'{construct_commit_message(squashed_commits)}'], encoding=encoding).communicate()


def construct_commit_message(squashed_commits):
    retstr = f'squash.py: Auto combined {len(squashed_commits)} commits: \r\n\r\n'
    for i in range(len(squashed_commits) - 1):
        retstr += f'{i+1}: {squashed_commits[i]} {get_commit_message(squashed_commits[i])}\r\n'
    return retstr


def get_commit_message(commitish):
    out, err = subprocess.Popen(['git', 'rev-list', '--format=%B', '--max-count=1', f'{commitish}^'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out).splitlines() 
    if type(out) is list:
        return out[-1]


def get_parent_commit(commitish):
    out, err = subprocess.Popen(['git', 'rev-parse', f'{commitish}^'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    if len(out) >= 7: # Normal
        return out
    return None # Initial commit has no parent
    

def checkout_branch(branch):
    out, err = subprocess.Popen(['git', 'checkout', f'{branch}'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if format_subprocess_stdout(out).startswith('error'):
        print(format_subprocess_stdout(out))
        print('Exiting.')
        exit(-1)


def create_squash_branch(branch):
    print(f'Creating squash branch \"{branch}squash\"...')
    subprocess.Popen(['git', 'branch', f'{branch}squash'], encoding=encoding).communicate()
    return f'{branch}squash'


def print_git_log_graph(head_in_focus=None):
    print()
    out, err = subprocess.Popen(['git', '--no-pager', 'log', '--graph', '--abbrev-commit', '--decorate', "--format=format:%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%<(25,trunc)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)", '--all'], encoding=encoding, stdout=subprocess.PIPE, stderr=None, shell=True).communicate()
    out = format_subprocess_stdout(out + '\n')

    graph = out.splitlines()
    graph.reverse()

    # If head to focus graph display around given, truncate lines around it and emphasize head's line ( <<<<< ).
    # Else, focus graph on last line.
    maxlines = 16

    head_short_sha = None
    if head_in_focus is not None:
        head_short_sha = get_ref_shortsha(f'refs/heads/{head_in_focus}')

    focusindex = len(graph)-1
    for i in range(len(graph)):
        graph[i] = graph[i].replace('\\\\', '\\').replace('\\', '¤').replace('/', '\\').replace('¤', '/') # Flip slashes after reverse

        # if head_in_focus != '' and re.match(rf'.*(?:HEAD\s-\>\s|\,\s|\(){head_in_focus}(?:\,\s|\)).*', graph[i]): # Line with the new squash commit
        if (head_short_sha is not None) and (head_short_sha in graph[i]): # Line with the new squash commit
        # if head_in_focus != '' and re.match(rf'.*HEAD.*', graph[i]): # Line with the new squash commit
            focusindex = i
            graph[i] += f'       <<<<< Squashed commit(s) to {head_in_focus}' # Emphasize the line

    endprintindex = (int(len(graph)) if abs(len(graph)-focusindex) < (maxlines/2) else int(focusindex+(maxlines/2)))
    startprintindex = (0 if focusindex<(maxlines/2) else int(focusindex-abs(maxlines-abs(endprintindex-focusindex))))
    originalgraphlen = len(graph)

    graph = graph[startprintindex : endprintindex]

    if not focusindex<(maxlines/2): # Start was truncated
        print(f'GIT LOG GRAPH:\n...')
    for line in graph:
        print(line)
    # print(f'originalgraphlen = {originalgraphlen}')
    # print(f'focusindex = {focusindex}')
    # print(f'(maxlines/2) = {(maxlines/2)}')
    if not abs(originalgraphlen-focusindex) < (maxlines/2): # End was truncated
        print(f'...')

    print()


def get_commits_since_last_fork(branch):

    commitlist = []
    sha = get_ref_sha(branch)

    command = ['git', '--no-pager', 'log', '--format=%H %P', '--all']

    out, err = subprocess.Popen(command, encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    loglist = out.splitlines()

    # While parent is not a parent of two or more commits (a "fork" commit)
    parent = None
    while(True):
        for i in range(0, len(loglist)):
            m = re.match(rf'{sha}(?: )?(?P<parent>[0-9a-fA-F]+)?.*', loglist[i])

            if m is not None:
                if loglist[i].count(' ') > 1: # Multi parent (this is a merge commit), stop here.
                    parent = None
                    break

                parent = m.group('parent')

                if parent is not None:
                    commitlist.append(sha)

                sha = parent
                break

        if i == len(loglist)-1: # Initial commit.
            break
        
        children = 0
        for line in loglist:
            match = re.findall(rf'^.* {sha}(?:.*)?$', line)

            if match != []:
                children += 1

        if (children > 1) or parent is None:        
            break

    return commitlist


def get_cur_branch():
    '''Get the currently checked out Git branch in cwd.
    
    pre: cwd is a Git repository.
    '''
    out, err = subprocess.Popen(['git', 'symbolic-ref', 'HEAD'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return format_subprocess_stdout(out)


def get_local_branch_list():
    '''Get a list of local Git branches in cwd.
    
    pre: cwd is a Git repository.
    '''
    out, err = subprocess.Popen(['git', 'show-ref', '--heads'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)

    branches = []
    for sha_rev in out.splitlines():
        sha, rev = sha_rev.split(' ')
        branches.append(rev.replace(f'refs/heads/', ''))

    return branches


def get_branch_name_from_ref(sha):
    out, err = subprocess.Popen(['git', 'name-rev', f'{sha}'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    return format_subprocess_stdout(out)


def get_ref_shortsha(branch):
    out, err = subprocess.Popen(['git', 'show-ref', '--hash=7', f'{branch}'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    if len(out.splitlines()) > 1:
        raise NotImplementedError(f'Multiple entries for \"git show-ref {branch}\":\n{out}')

    if len(out) > 0:
        return out
    return None

def get_ref_sha(branch):
    out, err = subprocess.Popen(['git', 'show-ref', '--hash', f'{branch}'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)
    if len(out.splitlines()) > 1:
        raise NotImplementedError(f'Multiple entries for \"git show-ref {branch}\":\n{out}')

    if len(out) > 0:
        return out
    return None


def p_branch_exists(branch):
    out, err = subprocess.Popen(['git', 'show-ref', '--verify', f'{branch}'], encoding=encoding, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    out = format_subprocess_stdout(out)

    if out.endswith('squash'):
        return True
    return False





if __name__ == '__main__': # If you want to test something, place calls here.
    import os
    os.chdir('C:\\Users\\AXNCYB\\source\\repos\\cbxConverter')
    print_git_log_graph('issue25squash')

    #show_ref('refs/heads/main')
