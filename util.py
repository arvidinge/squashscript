
def format_subprocess_stdout(stdout):
    retstr = ''
    for c in str(stdout).replace('\\n', '\n'):
        retstr += c
    retstr = retstr.split('b\'', 1)[-1]
    retstr = retstr.rsplit('\'', 1)[0]
    retstr = retstr.rsplit('\n', 1)[0]

    return retstr
