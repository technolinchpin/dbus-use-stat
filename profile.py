#!/usr/bin/env python

import sys
import argparse
import dbus
import datetime
import time

def get_cmdline(pid):
  cmdline = ''
  if pid > 0:
    try:
      procpath = '/proc/' + str(pid) + '/cmdline'
      with open(procpath, 'r') as f:
        cmdline = " ".join(f.readline().split('\0'))
    except:
      pass
  return cmdline

# Parsing parameters

parser = argparse.ArgumentParser(description='Getting some D-Bus memory infos')
parser.add_argument('--session', help='session bus', action="store_true")
parser.add_argument('--system', help='system bus', action="store_true")
args = parser.parse_args()

if args.system and args.session:
  parser.print_help()
  sys.exit(1)

# Fetch data from the bus driver

if args.system:
  bus = dbus.SystemBus()
else:
  bus = dbus.SessionBus()

remote_object = bus.get_object("org.freedesktop.DBus",
                               "/org/freedesktop/DBus")
bus_iface = dbus.Interface(remote_object, "org.freedesktop.DBus")
stats_iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Debug.Stats")

names = bus_iface.ListNames()
unique_names = [ a for a in names if a.startswith(":") ]
pids = dict((name, bus_iface.GetConnectionUnixProcessID(name)) for name in unique_names)
cmds = dict((name, get_cmdline(pids[name])) for name in unique_names)
well_known_names = [ a for a in names if a not in unique_names ]
owners = dict((wkn, bus_iface.GetNameOwner(wkn)) for wkn in well_known_names)

def get_stats(conn):
  stats = None
  try:
    stats = stats_iface.GetConnectionStats(conn)
  except:
    # failed: did you enable the Stats interface? (compilation option: --enable-stats)
    # https://bugs.freedesktop.org/show_bug.cgi?id=80759 would be nice too
    pass
  return stats

while True:

	stats = dict((name,
	              dict({
	                'wkn': [k for k, v in owners.items() if v == name],
	                'pid': pids[name],
	                'cmd': cmds[name] or "",
	                'stats': get_stats(name),
	              })
	               ) for name in unique_names)


	for name in stats:
  #print("Connection %s with pid %d '%s' (%s):"
  #      % (name, stats[name]['pid'], stats[name]['cmd'],
  #         ' '.join(stats[name]['wkn'])))

	   if stats[name]['stats'] is not None:
	   	  print("%s\t %s \t %d (%s) \t InB:%s \t InBP:%s \t OutB:%s \t OutBP:%s"
		        % (datetime.datetime.now().strftime("%H:%M:%S.%f") ,name,stats[name]['pid'],' '.join(stats[name]['wkn']),(stats[name]['stats']['IncomingBytes']),
			(stats[name]['stats']['PeakIncomingBytes']),(stats[name]['stats']['OutgoingBytes']),(stats[name]['stats']['PeakOutgoingBytes'])))
	   
	   print("")
        
	time.sleep(5)

