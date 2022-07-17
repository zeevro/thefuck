from subprocess import Popen, PIPE
import ctypes
import os
from ..utils import DEVNULL, memoize
from .generic import Generic, ShellConfiguration

ctypes.windll.shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)

def win_CommandLineToArgvW(cmd):
    nargs = ctypes.c_int()
    lpargs = ctypes.windll.shell32.CommandLineToArgvW(cmd, ctypes.byref(nargs))
    args = [lpargs[i] for i in range(nargs.value)]
    if ctypes.windll.kernel32.LocalFree(lpargs):
        raise AssertionError
    return args


class CMD(Generic):
    friendly_name = 'CMD'

    @memoize
    def get_aliases(self):
        proc = Popen(['doskey.exe', '/macros'], stdout=PIPE, stderr=DEVNULL)
        return {k.lower(): v
                for line in proc.stdout.read().decode('utf-8').splitlines()
                for k, v in line.split('=', 1)}

    def _expand_aliases(self, command_script):
        # TODO: Should this be recursive?

        cmd_argv = self.split_command(command_script)
        alias_cmd = self.get_aliases().get(cmd_argv[0].lower(), None)
        if alias_cmd is None:
            return command_script

        alias_argv = self.split_command(alias_cmd)

        ret_argv = []
        for arg in alias_argv:
            if len(arg) == 2 and arg[0] == '$':
                if arg[1] == 'T':
                    ret_argv.append('&')
                elif arg[1] in '123456789':
                    ret_argv.append(self.quote(cmd_argv[int(arg[1])]))
                elif arg[1] == '*':
                    ret_argv.extend(map(self.quote, cmd_argv[1:]))
            else:
                ret_argv.append(self.quote(arg))

        return ' '.join(ret_argv)

    def to_shell(self, command_script):
        """Prepares command for running in shell."""
        # TODO: Maybe escape some things with '^' ?

    def app_alias(self, alias_name):
        return '''
            set TF_SHELL=cmd
            set TF_ALIAS={name}
            set PYTHONIOENCODING=utf-8
            
        '''

    def _get_history_lines(self):
        """Returns list of history entries."""
        if self._get_history_file_name():
            return super()._get_history_lines()

        proc = Popen(['doskey.exe', '/history'], stdout=PIPE, stderr=DEVNULL)
        return proc.stdout.read().decode('utf-8').splitlines()

    def how_to_configure(self):
        return ShellConfiguration(
            content='Not known yet',
            path='Not known yet',
            reload='Not known yet',
            can_configure_automatically=False)

    def _get_version(self):
        """Returns the version of the current shell"""
        proc = Popen(['cmd.exe', '/c', 'ver'], stdout=PIPE, stderr=DEVNULL)
        return proc.stdout.read().decode('utf-8').split()[-1][:-1]

    def split_command(self, command):
        return win_CommandLineToArgvW(command)

    def quote(self, s):
        if not s:
            return '""'

        if set(' \t\n\v"').isdisjoint(s):
            return s

        ret = '"'
        it = iter(list(s) + [None])
        for c in it:
            backslashes = 0
            while c == '\\':
                c = next(it)
                backslashes += 1

            if c is None:
                ret += '\\' * (2*backslashes)
            elif c == '"':
                ret += '\\' * (2*backslashes+1)
                ret += '"'
            else:
                ret += '\\' * backslashes
                ret += c

        return ret + '"'

    def get_builtin_commands(self):
        """Returns shells builtin commands."""
        return ['assoc', 'attrib', 'break', 'bcdedit', 'cacls', 'call', 'cd',
                'chcp', 'chdir', 'chkdsk', 'chkntfs', 'cls', 'cmd', 'color',
                'comp', 'compact', 'convert', 'copy', 'date', 'del', 'dir',
                'diskpart', 'doskey', 'driverquery', 'echo', 'endlocal',
                'erase', 'exit', 'fc', 'find', 'findstr', 'for', 'format',
                'fsutil', 'ftype', 'goto', 'gpresult', 'graftabl', 'help',
                'icacls', 'if', 'label', 'md', 'mkdir', 'mklink', 'mode',
                'more', 'move', 'openfiles', 'path', 'pause', 'popd', 'print',
                'prompt', 'pushd', 'rd', 'recover', 'rem', 'ren', 'rename',
                'replace', 'rmdir', 'robocopy', 'set', 'setlocal', 'sc',
                'schtasks', 'shift', 'shutdown', 'sort', 'start', 'subst',
                'systeminfo', 'tasklist', 'taskkill', 'time', 'title', 'tree',
                'type', 'ver', 'verify', 'vol', 'xcopy', 'wmic']


class Clink(CMD):
    def _get_history_file_name(self):
        return os.path.join(os.environ.get('LOCALAPPDATA'), 'clink', '.history')

    def put_to_history(self, command):
        # TODO: Implement
        pass
