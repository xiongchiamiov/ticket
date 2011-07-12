#!/usr/bin/env python

from argparse import ArgumentParser
from os import execlp, getcwd
from os.path import expanduser
from subprocess import PIPE, Popen, STDOUT
from sys import exit

def shell(command):
   r'''
   Run `command` through the shell and return a tuple of the return code
   and the output.

   >>> shell('uname -s')   
   (0, 'Linux\n')

   >>> shell('ld -f')
   (1, "ld: unrecognized option '-f'\nld: use the --help option for usage information\n")
   '''
   p = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT)
   output = p.communicate()[0]
   return (p.returncode, output)

def setup():
   ''' Backup ~/Code and create a new Code directory suitable for use with ticket. '''
   shell('''
   cd &&
   git svn clone file:///var/ifixit/CodeRepos/ -s &&
   mv Code Code.bak &&
   mv CodeRepos Code
   ''')

def list_(type):
   ''' List various types of tickets that ticket knows about. '''
   if not type or type == 'active':
      print "Active tickets:"
      print shell(r"screen -ls | grep 'tached' | sed 's/^.*\./   /' | grep -E '^   #[0-9]+'")[1]
      print ""
   if not type or type == 'open':
      print "Open tickets:"
      print "Not yet implemented."
      print ""
   if not type or type == 'blocked':
      print "Blocked tickets:"
      print "Not yet implemented."
      print ""

def start(ticket):
   ''' Start or resume work on a ticket. '''
   # I don't know why argparse is giving this in a list
   ticket = ticket[0]

   # Unfortunately, because of the way git works, changes are separate from
   # branches, which is normally good, but makes it hard for us to keep
   # changes in one branch separate from those in another.  So, we stash
   # things away and pop them off again when we come back.  The downside of
   # this is that you shouldn't use stash for anything else, since your
   # stashed changes could get popped off unexpectedly.  You also shouldn't
   # work on two things at the same time, because the working directory on
   # the first will be changed when you start the second.
   # An alternative approach would be to litter a directory with copies of
   # trunk and change around symlinks.
   # I'd think that `cd`ing would work, but it seems that screen won't start
   # with that directory.  So, we'll just tell people they need to be in
   # `~/Code`.
   #cd ~/Code &&
   if getcwd() != '/mnt/ebs'+expanduser('~/Code'):
      print 'You need to run this in ~/Code !'
      exit(1)

   stop()
   shell('git checkout -B #%s' % ticket)
   # Stashes aren't tied directly to branches, but `git stash list` displays
   # the branch they were created on.  So, get the most recent one of those.
   stash = shell("git stash list | grep 'WIP on #%s:' | head -1 | sed 's/}:.*/}/'" % ticket)[1]
   if stash:
      shell('git stash pop ' + stash + ' && git reset HEAD .')

   # We have to use one of the exec* functions because we aren't interested in
   # launching a subshell - we want to throw the user into screen!
   # The second parameter is the name that will show up in ps.
   execlp('screen', 'screen (ticket)', '-DRR', "#%s" % ticket)

def stop():
   ''' Stop working on a ticket. '''
   shell('git add .') # Make sure we stash new files
   shell('git stash')
   shell('git checkout master') # Make sure we start new tickets from master
   shell('git svn rebase') # Update from svn

if __name__=='__main__':
   import doctest
   doctest.testmod()

   parser = ArgumentParser(description='A workflow tool that uses GNU screen and git-svn to make multi-tasking in a Subversion checkout a bit cleaner.')
   subparsers = parser.add_subparsers()

   parser_setup = subparsers.add_parser('setup', description=setup.__doc__)
   parser_setup.set_defaults(func=setup)

   parser_list = subparsers.add_parser('list', description=list_.__doc__)
   parser_list.add_argument('type', nargs='?', choices=('active', 'open', 'blocked'))
   parser_list.set_defaults(func=list_)

   parser_start = subparsers.add_parser('start', description=start.__doc__)
   parser_start.add_argument('ticket', type=int, nargs=1)
   parser_start.set_defaults(func=start)

   parser_stop = subparsers.add_parser('stop', description=stop.__doc__)
   parser_stop.set_defaults(func=stop)

   # Because I didn't want to pass an argparse.Namespace to the functions and
   # have to access everything through args.foo, we pull out the values as a
   # dictionary and splat 'em in.
   # (Shallow-)Copying the dict is necessary, since we want to avoid passing
   # the going-to-be-called function in as a parameter to itself.
   args = parser.parse_args().__dict__
   function = args['func']
   del args['func']
   function(**args)
   #try:
   #   function(**args)
   #except (NoOptionError, NoSectionError), exception:
   #   print >> sys.stderr, message

