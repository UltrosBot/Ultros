import re

__author__ = 'rakiru'

def lowercase_nickname(nick):
	return nick.lower().replace(u'{', u'[').replace(u'}', u']')

def compare_nicknames(nickOne, nickTwo):
	nickOne = lowercase_nickname(nickOne)
	nickTwo = lowercase_nickname(nickTwo)
	return nickOne == nickTwo

def split_hostmask(hostmask):
	posEx = hostmask.find(u'!')
	posAt = hostmask.find(u'@')
	if posEx <= 0 or posAt < 3 or posEx + 1 == posAt or posAt + 1 == len(hostmask): # All parts must be > 0 in length
		raise Exception("Hostmask must be in the form '*!*@*'")
	return [hostmask[0:posEx], hostmask[posEx + 1: posAt], hostmask[posAt + 1:]]

def match_hostmask_part(user, mask):
	# IRC hostmasks can contain two kinds of wildcard:
	#   * - match any character, 0 or more times
	#   ? - match any character, exactly once
	# Here, we convert the mask into its regex counterpart and use that to compare
	mask = re.escape(mask.lower()).replace(r'\*', '.*').replace(r'\?', '.')
	return re.match(mask, user) is not None

def match_hostmask(user, mask):
	userSplit = split_hostmask(user)
	maskSplit = split_hostmask(mask)
	# Case-insensitive match for nickname
	# match_hostmask_part() does a regular lower() too which is fine for the other parts
	userSplit[0] = lowercase_nickname(userSplit[0])
	maskSplit[0] = lowercase_nickname(maskSplit[0])
	for x in xrange(3):
		if not match_hostmask_part(userSplit[x], maskSplit[x]):
			return False
	return True