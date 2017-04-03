from enigmaConstants import rotorSpecs, reflectorSpecs
import string
import sys

letters=string.ascii_uppercase

def switch(x):
	if type(x) is int:
		return chr(x+65)
	elif type(x) is str:
		return ord(x)-65
	else:
		return None

class rotor(object):
	def __init__(self,name,position,ring):
		if name not in rotorSpecs.keys():
			raise RuntimeError('Invalid rotor specification.')
		if position not in letters:
			raise RuntimeError('Invalid rotor initialization.')
		self.ring=switch(ring)
		self.position=switch(position)
		self.permute={'forward':{},'reverse':{}}
		for inputContact, outputContact in zip(letters,rotorSpecs[name]['perm']):
			self.permute['forward'][switch(inputContact)]=switch(outputContact)
			self.permute['reverse'][switch(outputContact)]=switch(inputContact)
		self.notches=rotorSpecs[name]['notches'] #bugged???
	def encrypt(self, direction, letter):
		if letter not in letters:
			raise RuntimeError('Invalid letter provided to rotorCrypt.')
		if direction not in ['forward','reverse']:
			raise RuntimeError('Invalid encryption direction passed to rotorCrypt.')
		retVal=(self.permute[direction][(switch(letter)+self.position-self.ring)%26]-self.position+self.ring)%26
		return switch(retVal)
	def getPosition(self):
		return switch(self.position)
	def increment(self):
		self.position+=1

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

def checkSettings(nameList,offsetList,reflectorName,plugboardPairs,ringSettings):
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
	return None

class enigmaMachine(object):
	def __init__(self,nameList,offsetList,reflectorName,plugboardPairs,ringSettings):
		checkSettings(nameList,offsetList,reflectorName,plugboardPairs,ringSettings)
		self.rotors={}
		self.plugboardMap={}
		self.reflector={}
		self.doubleStep=False
		for i in range(3):
			self.rotors[i]=rotor(nameList[i],offsetList[i],ringSettings[i])
		for pair in plugboardPairs:
			self.plugboardMap[pair[0]]=pair[1]
			self.plugboardMap[pair[1]]=pair[0]
		for letter, reflection in zip(letters,reflectorSpecs[reflectorName]):
			self.reflector[letter]=reflection
	def getPositions(self):
		currentPositions=''
		for i in range(3):
			currentPositions+=self.rotors[i].getPosition()
		return currentPositions	
	def encrypt(self,letter,debug=False):
		if letter not in letters: raise RuntimeError('Invalid letter provided to crypt.')
		self.increment()
		if letter in self.plugboardMap.keys():
			letter=self.plugboardMap[letter]
		for i in range(3):
			letter=self.rotors[i].encrypt('forward',letter)
		letter=self.reflector[letter]
		for j in range(2,-1,-1):
			letter=self.rotors[j].encrypt('reverse',letter)
		if letter in self.plugboardMap.keys():
			letter=self.plugboardMap[letter]		
		return letter
	def increment(self):
		self.rotors[0].increment()
		if chr(ord(self.rotors[1].getPosition())+1) in self.rotors[1].notches or chr(ord(self.rotors[1].getPosition())-25) in self.rotors[1].notches:
			self.rotors[1].increment()
			self.rotors[2].increment()
		if self.rotors[0].getPosition() in self.rotors[0].notches:
			self.rotors[1].increment()

def userSetup():
	print 'A number of selections must be made to set up an Enigma machine'
	print 'A default initialization is available, using rotors I-III initialized to AAA,'
	print 'reflector A, and with (A,B); (C,D); ... (S,T) as the plugboard.'
	isDefault=raw_input('Enter 1 to use the defaults, or 0 to set up your own: ')
	if isDefault=='1':
		pairs=[]
		for i in range(10):
			pairs.append((chr(65+2*i),chr(66+2*i)))			
		print 'Initializing your Enigma machine...'
		settings = (['I','II','III'],['A','A','A'],'Reflector A',pairs,['A','A','A'])
		machine = enigmaMachine(*settings)
		return machine, settings
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

def encrypt(machine,text,debug=False):
	if not isinstance(machine,enigmaMachine): raise RuntimeError('Invalid machine passed to encrypt.')
	if type(text) is not str: raise RuntimeError('Invalid plaintext passed to encrypt.')
	ciphertext=''
	for idx,x in enumerate(text):
		ciphertext+=machine.encrypt(x,debug)
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
			print '\'{}\' test completed successfully.'.format(l)
		except AssertionError:
			dummy=raw_input('\'{0}\' test failed: expected {1}, received {2}. Press <ENTER> to run diagnostics.'.format(l,result[l],test[l]['Cipher']))
			test[l]['Machine']=enigmaMachine(*test[l]['Settings'])
			test[l]['Cipher']=encrypt(test[l]['Machine'],'AAAAA',True)
			return False
	return True
		
############################################################

print 'Welcome to the Enigma encryption system. Validating build...'
valid=verifyEnigma()
if not valid:
	print 'DEBUG - Debugging complete.'
	print 'Exiting program.'
	sys.exit()
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
	plaintext=plaintext.translate(None, string.punctuation).upper().replace(' ','')
	ciphertext = encrypt(machine,plaintext)
	print 'Encrypted text: '+ciphertext
	print '1 to exit, 2 to return to machine setup, 3 to reset rotors, or 4 to continue:'
	nextStep=raw_input('$: ')
