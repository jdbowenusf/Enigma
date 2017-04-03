from enigmaConstants import rotorSpecs, reflectorSpecs
import string
import sys

letters=string.ascii_uppercase

class rotor(object):
	"""An Enigma rotor is simply a gear valued A-Z around the perimeter, which has internal
	wires that permute incoming signals.  An Enigma machine is composed of three such
	rotors, which increment somewhat like an odometer as each successive key is encrypted.
	To specify a rotor, it is necessary to describe how it permutes incoming signals,
	on which position it will increment the next rotor, and what position we're starting with."""
	def __init__(self,name,offset,ring):
		if name not in rotorSpecs.keys():
			raise RuntimeError('Invalid rotor specification.')
		if offset not in letters:
			raise RuntimeError('Invalid rotor initialization.')
		self.name=name
		self.notches=rotorSpecs[name]['notches']
		self.position=letters[ord(offset)+ord(ring)-130:]+letters[:ord(offset)+ord(ring)-130]
		self.perm=rotorSpecs[name]['perm'][ord(offset)-65:]+rotorSpecs[name]['perm'][:ord(offset)-65]
	#These next two functions give the action of the rotor on a letter, for both directions
	def forwardCrypt(self, letter):
		if letter not in letters:
			raise RuntimeError('Invalid letter provided to forwardCrypt.')
		return self.perm[ord(letter)-65]
	def reverseCrypt(self, letter):
		if letter not in letters:
			raise RuntimeError('Invalid letter provided to reverseCrypt.')
		return letters[self.perm.index(letter)]
	#Final two methods display and increment the rotor, respectively
	def getCurrentPosition(self):
		return self.position[0]
	def increment(self):
		self.position=self.position[1:]+self.position[0]
		self.perm=self.perm[1:]+self.perm[0]


"""The only reason we define this function is because there's so much to check to verify
#validity of a plugboard configuration, and it was hard to read in the if statement
in the enigmaMachine class."""
def checkPlugs(plugboardPairs):
	tempLetters=letters
	if len(plugboardPairs)>10: return False
	for pair in plugboardPairs:
		if type(pair) is not tuple: return False
		if len(pair)!=2: return False
		if pair[0] not in letters: return False
		if pair[1] not in letters: return False
		tempLetters=tempLetters.replace(pair[0],'').replace(pair[1],'')
	if len(tempLetters)!=26-2*len(plugboardPairs): return False
	return True


"""An Enigma machine consisted of a keyboard, a battery, three Enigma rotors, a reflector,
and a plugboard. To encrypt or decrypt a character, the machine would be initialized with
that days rotors, starting positions, and plugboard configuration.  The user would then key
a character in using the keyboard, which would be routed first through the plugboard to possibly
swap it with one other letter.  The new swapped letter would be sent through rotors A, B, and C
in sequence, each of which maps it to a new letter according to the permutation hardwired into
the rotor and where in it's rotation the rotor is.  The output of rotor C would be sent to the
reflector, which peforms another 1-1 permutation of the alphabet and so outputs some other letter;
this new letter from the reflector then passes through rotors C, B, and A backwards, and the
output of rotor A is sent back through the plugboard and to the lightboard, where the bulb under
the ciphertext character would light. At this point, rotor A would increment by 1, ie, rotate by
1/26th and hence have a new permutation ready for the next plaintext character.  When rotor A
increments past a notch point, it increments rotor B by 1; when rotor B increments past a notch
point, it will both increment rotor C and increment itself again on the next keyed character
(even though rotor A will not be passing a notch) - eg, if all notches were on A, the flows would
go: 'CZY' -> 'CZZ' -> 'DAA' -> 'DBB'* -> 'DBC' -> 'DBD' -> ... with the double increment occuring
at the asterisk."""

class enigmaMachine(object):
	def __init__(self,nameList,offsetList,reflectorName,plugboardPairs,ringSettings):
		#Verify the validity of the initialization
		if not all(map(lambda x: x in rotorSpecs.keys(), nameList)) or len(nameList)!=3:
			raise RuntimeError('Invalid rotor specifications.')
		if not all(map(lambda x: x in letters, offsetList)) or len(offsetList)!=3:
			raise RuntimeError('Invalid rotor initializations.')
		if not all(map(lambda x: x in letters, ringSettings)) or len(ringSettings)!=3:
			raise RuntimeError('Invalid ring initializations.')
		if not checkPlugs(plugboardPairs):
			raise RuntimeError('Invalid plugboard specification.')
		if not reflectorName in reflectorSpecs.keys():
			raise RuntimeError('Invalid reflector specification.')
		#Set the rotor variables, plugboard, and reflector
		self.rotors={}
		self.plugboardMap={}
		self.reflector={}
		self.doubleIncrementNextRound=False
		for i in range(3):
			self.rotors[i]=rotor(nameList[i],offsetList[i],ringSettings[i])
		for pair in plugboardPairs:
			self.plugboardMap[pair[0]]=pair[1]
			self.plugboardMap[pair[1]]=pair[0]
		for letter, reflection in zip(letters,reflectorSpecs[reflectorName]):
			self.reflector[letter]=reflection
	def getCurrentPositions(self):
		currentPositions=''
		for i in range(3):
			currentPositions+=self.rotors[i].getCurrentPosition()
		return currentPositions	
	def crypt(self,letter,debug=False):
		#Verify that letter is an encryptable letter
		if letter not in letters: raise RuntimeError('Invalid letter provided to crypt.')
		#Increment the rotors
		if debug==True:
			print 'DEBUG - Rotor positions before incrementation: '+self.getCurrentPositions()
		self.increment()
		if debug==True:
			print 'DEBUG - Rotor positions after incrementation: '+self.getCurrentPositions()
		#If the letter is on the plugboard, swap, else leave it as is
		if letter in self.plugboardMap.keys():
			letter=self.plugboardMap[letter]
			if debug==True: print 'DEBUG - Plugboard updated letter to \'{}\''.format(letter)
		#Push the letter through each rotor (A,B,C) going forward
		for i in range(3):
			letter=self.rotors[i].forwardCrypt(letter)
			if debug==True: print 'DEBUG - Rotor {0} updated letter to \'{1}\''.format(i,letter)
		#Pass through the reflector and pass through each rotor (C,B,A) going backwards
		letter=self.reflector[letter]
		if debug==True: print 'DEBUG - Reflector updated letter to \'{}\''.format(letter)
		for j in range(2,-1,-1):
			letter=self.rotors[j].reverseCrypt(letter)
			if debug==True: print 'DEBUG - Rotor {0} updated letter to \'{1}\''.format(j,letter)
		#Again, perform plugboard swap if our letter is on the plugboard, and return ciphertext
		if letter in self.plugboardMap.keys():
			letter=self.plugboardMap[letter]
			if debug==True: print 'DEBUG - Plugboard updated letter to \'{}\''.format(letter)
		if debug==True: print 'DEBUG - Final cipherletter was \'{}\''.format(letter)		
		return letter
	def increment(self):
		self.rotors[0].increment()
		"""Generally, Enigma rotors increment like an odometer - as soon as one
		rotor passes its notch, the next rotor increments by one
		But Enigma machines had an odd bug (feature?) where, when the second rotor
		passed its notch and incremented the third, this would cause the second rotor
		to increment a second time on the next incrementation of the first rotor
		This would be like your odometer counting "199", "200", "211", "212"...
		We've got some hacky logic in here to address that."""
		if self.doubleIncrementNextRound==True:
			self.rotors[1].increment()
		self.doubleIncrementNextRound=False
		if self.rotors[0].position[0] in self.rotors[0].notches:
			self.rotors[1].increment()
			if self.rotors[1].position[0] in self.rotors[1].notches:
				self.rotors[2].increment()
				self.doubleIncrementNextRound=True


#We put the user input stuff into a function so we can write a readable loop later.
def userSetup():
	print 'A number of selections must be made to set up an Enigma machine'
	print 'A default initialization is available, using rotors I-III initialized to AAA,'
	print 'reflector A, and with (A,B); (C,D); ... (S,T) as the plugboard.'
	isDefault=raw_input('Enter 1 to use the defaults, or 0 to set up your own: ')
	if isDefault=='1':
		"""If they select default, we initialize the rotors as A=I, B=II, C=III,
		Reflector A, starting rotor positions 'AAA', ring settings 'AAA', and a 
		plugboard config that pairs A with B, C with D, etc. through S & T."""
		pairs=[]
		for i in range(10):
			pairs.append((chr(65+2*i),chr(66+2*i)))			
		print 'Initializing your Enigma machine...'
		#We save and return our settings, to make it easy to jump the rotors back
		settings = (['I','II','III'],['A','A','A'],'Reflector A',pairs,['A','A','A'])
		machine = enigmaMachine(*settings)
		return machine, settings
	#If they choose to manually configure the settings, there's a whole lotta crap to do:
	print 'We begin setup by selecting our rotors (choices are I-VIII).'
	userRotors={}
	for x in ['A','B','C']:
		userRotors[x]=raw_input('Enter rotor {}: '.format(x))
		while userRotors[x] not in rotorSpecs.keys():
			userRotors[x]=raw_input('Invalid selection, please try again: ')
	print 'Next we specify our reflector.'
	print 'Choices are Beta, Gamma, A, B, C, B Thin, C Thin, or ETW.'
	print 'Note that ETW is for debugging purposes, as this reflector'
	print 'contains no permutation and hence doesn\'t encrypt anything.'
	reflectorName=raw_input('Enter reflector choice: ')
	while reflectorName not in ['Beta','Gamma','A','B','C','B Thin','C Thin','ETW']:
		reflectorName=raw_input('Invalid selection, please try again: ')
	for x in ['A','B','C']:
		if x in reflectorName and 'hin' not in reflectorName:
			reflectorName='Reflector {}'.format(x)
		if x in reflectorName and 'hin' in reflectorName:
			refelctorName='Reflector {} Thin'.format(x)
	offsets=[]
	for x in ['A','B','C']:
		y=raw_input('Specify initial position of rotor {}: '.format(x))
		offsets.append(y)
	print 'Almost done! Now we must specify the plugboard pairing.'
	print 'Please enter up to ten pairs of letters, using no letter twice, or 0 to finish.'
	plugboardPairs=[]	
	for i in range(10):
		pair=raw_input('Enter pair #{}:'.format(str(i+1)))
		if pair=='0': break
		pair=tuple(pair.split(','))
		while pair[0] not in letters or pair[1] not in letters:
			pair=raw_input('Invalid entry.  Please enter a tuple of letters.')
		plugboardPairs.append(pair)
	print 'And finally we must specify the ring settings.  Enter three letters for ring settings.'
	ringString=raw_input('Ring settings: ')
	while len(ringString!=3):
		ringString=raw_input('Invalid ring settings.  Enter three letters for ring settings: ')
	print 'Initializing your Enigma machine...'
	settings = (userRotors.values(),offsets,reflectorName,plugboardPairs,[r for r in ringString])
	machine = enigmaMachine(*settings)
	return machine, settings


#This function is called encrypt but Enigma is symmetric - running this function on a ciphertext
#with the original rotor settings should return the plaintext
def encrypt(machine,text,debug=False):
	if not isinstance(machine,enigmaMachine): raise RuntimeError('Invalid machine passed to encrypt.')
	if type(text) is not str: raise RuntimeError('Invalid plaintext passed to encrypt.')
	ciphertext=''
	for idx,x in enumerate(text):
		if debug==True: print 'DEBUG - Passing \'{0}\', letter {1} of {2}, to crypt...'.format(x,idx+1,len(text))
		ciphertext+=machine.crypt(x,debug)
		if debug==True: print 'DEBUG - -----------------------------------------------'
	return ciphertext


def verifyEnigma():
	"""On the Wikipedia article linked in enigmaConstants.py, we're given two Enigma encryptions:
	Rotors (III,II,I), starting at AAA with the B reflector, no plugboard, and AAA ring settings
	--> Should map 'AAAAA'->'BDZGO' 
	Rotors (III,II,I), starting at AAA with the B reflector, no plugboard, and BBB ring settings
	--> Should map 'AAAAA'->'EWTYX'"""
	partialTestSettings=[['III','II','I'],['A','A','A'],'Reflector B',[]]
	test={}
	result={'A':'BDZGO','B':'EWTYX'}
	for l in ['A','B']:
		test[l]={}
		test[l]['Settings']=partialTestSettings+[[l,l,l]]
		test[l]['Machine']=enigmaMachine(*test[l]['Settings'])
		test[l]['Cipher']=encrypt(test[l]['Machine'],'AAAAA')
		try:
			assert test[l]['Cipher']==result[l]
			print '{} test completed successfully.'.format(l)
		except AssertionError:
			print 'Enigma validation test {} failed. Re-running with diagnostics...'.format(l)
			test[l]['Machine']=enigmaMachine(*test[l]['Settings'])
			test[l]['Cipher']=encrypt(test[l]['Machine'],'AAAAA',True)
			return False, 'Ending program: expected {0}, received {1}'.format(result[l],test[l]['Cipher'])
		return True, ''
		

############################################################


print 'Welcome to the Enigma encryption system. Validating build...'
valid,failStr=verifyEnigma()
if not valid:
	print 'DEBUG - Debugging complete.'
	print failStr
	sys.exit()

"""nextStep determines how we update the machine.
1 will exit, 2 will allow us to describe a new rotor configuration,
3 will set the rotors back to their most recent starting position,
or 4 will continue with the rotors in their current position (ie, 
incremented after encrypting a plaintext."""
nextStep='2'
while nextStep!='1':
	if nextStep=='2':
		machine, settings = userSetup()
		print "Enigma machine succesfully initialized.  Ready for encryption."
	elif nextStep=='3':
		print 'Restoring machine setttings...'
		machine = enigmaMachine(*settings)
		print "Enigma rotors returned to starting positions.  Ready for encryption."
	plaintext = raw_input('Enter the plaintext message you would like to encrypt: ')
	#Enigma can only handle upper case letters, no lowercase, spaces, or punctuation
	plaintext=plaintext.translate(None, string.punctuation).upper().replace(' ','')
	ciphertext = encrypt(machine,plaintext)
	print 'Encrypted text: '+ciphertext
	print '1 to exit, 2 to return to machine setup, 3 to reset rotors, or 4 to continue:'
	nextStep=raw_input('$: ')
