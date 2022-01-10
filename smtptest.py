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


### ------------------------------------------------------------- Parser --- ###

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
parser.set_defaults(chunks='ifavailable')
parser.set_defaults(chunksize=32)
parser.set_defaults(returnpath="")

parser.add_option("-t", "--usetls", action="store_true", dest="usetls", default=False, help="Connect using TLS, default is false")
parser.add_option("-s", "--usessl", action="store_true", dest="usessl", default=False, help="Connect using SSL, default is false")
parser.add_option("-n", "--port", action="store", type="int", dest="serverport", help="SMTP server port", metavar="nnn")
parser.add_option("-u", "--username", action="store", type="string", dest="SMTP_USER", help="SMTP server auth username", metavar="username")
parser.add_option("-p", "--password", action="store", type="string", dest="SMTP_PASS", help="SMTP server auth password", metavar="password")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Verbose message printing")
parser.add_option("-d", "--debuglevel", type="int", dest="debuglevel", help="Set to 1 to print smtplib.send messages", metavar="n")
parser.add_option("-m", "--max-mails", type="int", dest="maxmails", help="The number of mails we should send", metavar="nnn")
parser.add_option("-c", "--chunks", type="choice", dest="chunks", choices=[ 'always', 'never', 'ifavailable' ], help="when to use use chunks (always, never, ifavailable)")
parser.add_option("-C", "--chunk-size", type="int", dest="chunksize", help="Chunk size in bytes", metavar="SIZE")
parser.add_option("-r", "--return-path", action="store", type="string", dest="returnpath", help="You can override the envelope sender address", metavar="someone@example.com")

(options, args) = parser.parse_args()
if len(args) != 3:
	parser.print_help()
	parser.error("incorrect number of arguments")
	sys.exit(-1)

fromaddr = args[0]
toaddr = args[1]
serveraddr = args[2]


### ------------------------------------------------------- Mail content --- ###

now = strftime("%Y-%m-%d %H:%M:%S")

msg = "From: %s\r\nTo: ###TOADDR###\r\nSubject: Test Message from smtptest at %s\r\n\r\nTest message from the smtptest tool sent at %s" % (fromaddr, now, now)


### ------------------------------------------------------ Debug summary --- ###

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
	print('chunks:', options.chunks)
	print('chunk size (if enabled):', options.chunksize)
	print('return path override:', options.returnpath)


### ----------------------------------------------------- Server connect --- ###

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

### ----------------------------------------------------- Authentication --- ###


if options.SMTP_USER != "": server.login(options.SMTP_USER, options.SMTP_PASS)
if options.returnpath != "":
	thisorig = options.returnpath
else:
	thisorig = fromaddr


### ------------------------------------------------------- Mail helpers --- ###

def run_command(server,command,expected_response = 250, raw=False):
	if options.verbose:
		print("sending command: %s" % command.strip())
	if raw:
		server.send(command)
	else:
		response = server.docmd(command)
		if response[0] != expected_response:
			print("server returned %i, expected %i" % ([0],expected_response))
			print("server error: %s" % response[1].decode())


def do_send_mail(server,sender,receiver,msg):
	chunking_supported = server.has_extn('CHUNKING')
	chunking_requested = (options.chunks == 'always' or options.chunks == 'ifenabled')
	chunking_forced    = (options.chunks == 'always')

	if chunking_forced:
		use_chunking = True
	elif chunking_supported and chunking_requested:
		use_chunking = True
	else:
		use_chunking = False

	if use_chunking:
		# Chunking isn't supported yet in libsmtp,
		# so we're sending the commands manually
		if options.verbose:
			print('sending in chunks of size %i' % options.chunksize)

		run_command(server, "MAIL FROM: %s" % sender)
		run_command(server, "RCPT TO: %s" % receiver)

		msg_as_bytes = bytes(msg, 'ascii')
		msg_size = len(msg_as_bytes)
		chunk_size = options.chunksize
		bytes_sent = 0

		while bytes_sent < msg_size:
			this_chunk_size = chunk_size
			if bytes_sent + this_chunk_size > msg_size:
				this_chunk_size = msg_size - bytes_sent

			this_chunk = msg_as_bytes[bytes_sent:bytes_sent+this_chunk_size]
			run_command(server, "BDAT %s\n" % this_chunk_size, raw=True)
			run_command(server, this_chunk, raw=True)
			bytes_sent += this_chunk_size
		run_command(server, "BDAT 0 LAST")
	else:
		server.sendmail(sender,receiver,msg)


### ------------------------------------------------------------ Send loop --- #

if options.maxmails > 0:
	for mailcount in range (1, options.maxmails + 1):
		thisrcpt = toaddr.replace('000', str(mailcount))
		thismsg = msg.replace('###TOADDR###', thisrcpt, 1)
		print("-- Message body ---------------------")
		print(thismsg)
		print("-------------------------------------")
		do_send_mail(server,thisorig,thisrcpt,thismsg)
		#server.sendmail(thisorig, thisrcpt, thismsg)
else:
	thismsg = msg.replace('###TOADDR###', toaddr, 1)
	print("-- Message body ---------------------")
	print(thismsg)
	print("-------------------------------------")
	do_send_mail(server,thisorig,toaddr,thismsg)
	#server.sendmail(thisorig, toaddr, thismsg)


### ------------------------------------------------------------ Cleanup --- ###

server.quit()
