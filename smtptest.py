#!/usr/bin/python
"""smtptest.py: command-line smtp test mail sender
https://github.com/turbodog/python-smtp-mail-sending-tester

Usage: python smtptest.py [options] fromaddress toaddress serveraddress 

Examples:
	python smtptest.py bob@example.com mary@example.com mail.example.com
	python smtptest.py --debuglevel 1 --usetls -u bob -p xyzzy "Bob <bob@example.com>" mary@example.com mail.example.com
	python smtptest.py --debuglevel 1 --usetls -u bob -p xyzzy -m 100 "Bob <bob@example.com>" test000@mailinator.com mail.example.com

At verbose == False and debuglevel == 0, smtptest will either succeed silently or print an error. Setting verbose or a debuglevel to 1 will generate intermediate output.

Using the max-mails feature will make the script sending mails in a loop up until hitting the max-mails number, replacing the digit in front of the @-sign with the iterator from every loop (test1@mailinator.com, test2@mailinator.com, test3@mailinator.com... test#maxmails#@mailinator.com)

See also http://docs.python.org/library/smtplib.html

"""

__version__ = "1.0"
__author__ = "Lindsey Smith (lindsey.smith@gmail.com)"
__copyright__ = "(C) 2010 Lindsey Smith. GNU GPL 2 or 3."

import smtplib
from time import strftime
import sys
from optparse import OptionParser

fromaddr = ""
toaddr = ""
serveraddr = ""

usage = "Usage: %prog [options] fromaddress toaddress serveraddress"
parser = OptionParser(usage=usage)

parser.set_defaults(usetls=False)
parser.set_defaults(usessl=False)
parser.set_defaults(serverport=25)
parser.set_defaults(SMTP_USER="")
parser.set_defaults(SMTP_PASS="")
parser.set_defaults(debuglevel=0)
parser.set_defaults(verbose=False)
parser.set_defaults(maxmails=0)
parser.set_defaults(returnpath="")

parser.add_option("-t", "--usetls", action="store_true", dest="usetls", default=False, help="Connect using TLS, default is false")
parser.add_option("-s", "--usessl", action="store_true", dest="usessl", default=False, help="Connect using SSL, default is false")
parser.add_option("-n", "--port", action="store", type="int", dest="serverport", help="SMTP server port", metavar="nnn")
parser.add_option("-u", "--username", action="store", type="string", dest="SMTP_USER", help="SMTP server auth username", metavar="username")
parser.add_option("-p", "--password", action="store", type="string", dest="SMTP_PASS", help="SMTP server auth password", metavar="password")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Verbose message printing")
parser.add_option("-d", "--debuglevel", type="int", dest="debuglevel", help="Set to 1 to print smtplib.send messages", metavar="n")
parser.add_option("-m", "--max-mails", type="int", dest="maxmails", help="The number of mails we should send", metavar="nnn")
parser.add_option("-r", "--return-path", action="store", type="string", dest="returnpath", help="You can override the envelope sender address", metavar="someone@example.com")

(options, args) = parser.parse_args()
if len(args) != 3:
	parser.print_help()
	parser.error("incorrect number of arguments")
	sys.exit(-1)

fromaddr = args[0]
toaddr = args[1]
serveraddr = args[2]	
	
now = strftime("%Y-%m-%d %H:%M:%S")

msg = "From: %s\r\nTo: ###TOADDR###\r\nSubject: Test Message from smtptest at %s\r\n\r\nTest message from the smtptest tool sent at %s" % (fromaddr, now, now)

if options.verbose:
	print('usetls:', options.usetls)
	print('usessl:', options.usessl)
	print('from address:', fromaddr)
	print('to address:', toaddr)
	print('server address:', serveraddr)
	print('server port:', options.serverport)
	print('smtp username:', options.SMTP_USER)
	print('smtp password: *****')
	print('smtplib debuglevel:', options.debuglevel)
	print('max mails iterator:', options.maxmails)
	print('return path override:', options.returnpath)

server = None
if options.usessl:
	server = smtplib.SMTP_SSL()
else:
	server = smtplib.SMTP()

server.set_debuglevel(options.debuglevel)
server.connect(serveraddr, options.serverport)
server.ehlo()
if options.usetls: server.starttls()
server.ehlo()
if options.SMTP_USER != "": server.login(options.SMTP_USER, options.SMTP_PASS)
if options.returnpath != "":
	thisorig = options.returnpath
else:
	thisorig = fromaddr
if options.maxmails > 0:
	for mailcount in range (1, options.maxmails + 1):
		thisrcpt = toaddr.replace('000', str(mailcount))
		thismsg = msg.replace('###TOADDR###', thisrcpt, 1)
		print("-- Message body ---------------------")
		print(thismsg)
		print("-------------------------------------")
		server.sendmail(thisorig, thisrcpt, thismsg)
else:
	thismsg = msg.replace('###TOADDR###', toaddr, 1)
	print("-- Message body ---------------------")
	print(thismsg)
	print("-------------------------------------")
	server.sendmail(thisorig, toaddr, thismsg)
server.quit()
