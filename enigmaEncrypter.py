from enigmaConstants import rotorSpecs, reflectorSpecs
import string

letters=string.ascii_uppercase

class rotor(object):
	def __init__(self,name,offset):
		if name not in rotorSpecs.keys():
			raise RuntimeError('Invalid rotor specification.')
		if offset not in letters:
			raise RuntimeError('Invalid rotor initialization.')
		self.name=name
		self.notches=rotorSpecs[name]['notches']
		self.position=letters[ord(offset)-65:]+letters[:ord(offset)-65]
		self.perm=rotorSpecs[name]['perm'][ord(offset)-65:]+rotorSpecs[name]['perm'][:ord(offset)-65]

	def forwardCrypt(self, letter):
		if letter not in letters:
			raise RuntimeError('Invalid letter provided to forwardCrypt.')
		return self.perm[ord(letter)-65]

	def reverseCrypt(self, letter):
		if letter not in letters:
			raise RuntimeError('Invalid letter provided to reverseCrypt.')
		return letters[self.perm.index(letter)]

	def increment(self):
		self.position=self.position[1:]+self.position[0]
		self.perm=self.perm[1:]+self.perm[0]

def checkPlugs(plugboardPairs):
	tempLetters=letters
	if len(plugboardPairs)!=10: return False
	for pair in plugboardPairs:
		if type(pair) is not tuple: return False
		if len(pair)!=2: return False
		if pair[0] not in letters: return False
		if pair[1] not in letters: return False
		tempLetters=tempLetters.replace(pair[0],'').replace(pair[1],'')
	if len(tempLetters)!=6: return False
	return True

class enigmaMachine(object):
	def __init__(self,nameList,offsetList,reflectorName,plugboardPairs):
		if not all(map(lambda x: x in rotorSpecs.keys(), nameList)) or len(nameList)!=3:
			raise RuntimeError('Invalid rotor specifications.')
		if not all(map(lambda x: x in letters, offsetList)) or len(offsetList)!=3:
			raise RuntimeError('Invalid rotor initializations.')
		if not checkPlugs(plugboardPairs):
			raise RuntimeError('Invalid plugboard specification.')
		if not reflectorName in reflectorSpecs.keys():
			raise RuntimeError('Invalid reflector specification.')
		self.rotors={}
		self.plugboardMap={}
		self.reflector={}
		self.doubleIncrementNextRound=False
		for i in range(3):
			self.rotors[i]=rotor(nameList[i],offsetList[i])
		for pair in plugboardPairs:
			self.plugboardMap[pair[0]]=pair[1]
			self.plugboardMap[pair[1]]=pair[0]
		for letter, reflection in zip(letters,reflectorSpecs[reflectorName]):
			self.reflector[letter]=reflection			
		print "Enigma machine succesfully initialized.  Ready for encryption."

	def crypt(self,letter):
		if letter not in letters: raise RuntimeError('Invalid letter provided to crypt.')
		if letter in self.plugboardMap.keys(): letter=self.plugboardMap[letter]
		for i in range(3):
			letter=self.rotors[i].forwardCrypt(letter)
		letter=self.reflector[letter]
		for j in range(2,-1,-1):
			letter=self.rotors[j].reverseCrypt(letter)
		if letter in self.plugboardMap.keys(): letter=self.plugboardMap[letter]
		self.increment()
		return letter
	
	def increment(self):
		self.rotors[0].increment()
		#Generally, Enigma rotors increment like an odometer - as soon as one
		#rotor passes its notch, the next rotor increments by one
		#But Enigma machines had an odd bug (feature?) where, when the second rotor
		#passed its notch and incremented the third, this would cause the second rotor
		#to increment a second time on the next incrementation of the first rotor
		#This would be like your odometer counting "199", "200", "211", "212"...
		#We've got some hacky logic in here to address that.
		if self.doubleIncrementNextRound==True:
			self.rotors[1].increment()
		self.doubleIncrementNextRound=False
		if self.rotors[0].position[0] in self.rotors[0].notches:
			self.rotors[1].increment()
			if self.rotors[1].position[0] in self.rotors[1].notches:
				self.rotors[2].increment()
				self.doubleIncrementNextRound=True

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
		settings = (['I','II','III'],['A','A','A'],'Reflector A',pairs)
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
	print 'Finally, we must specify the plugboard pairing.'
	print 'Please enter ten pairs of letters, using no letter twice: '
	plugboardPairs=[]	
	for i in range(10):
		pair=raw_input('Enter pair #{}:'.format(str(i+1)))
		while type(pair) is not tuple or type(pair[0]) is not str or type(pair[1]) is not str:
			pair=raw_input('Invalid entry.  Please enter a tuple of letters.')
		plugboardPairs.append(pair)
	print 'Initializing your Enigma machine...'
	settings = (userRotors.values(),offsets,reflectorName,plugboardPairs)
	machine = enigmaMachine(*settings)
	return machine, settings

def encrypt(machine,text):
	if not isinstance(machine,enigmaMachine): raise RuntimeError('Invalid machine passed to encrypt.')
	if type(text) is not str: raise RuntimeError('Invalid plaintext passed to encrypt.')
	ciphertext=''
	for x in text:
		ciphertext+=machine.crypt(x)
	return ciphertext

print 'Welcome to the Enigma encryption system.'
nextStep='2'
while nextStep!='1':
	if nextStep=='2':
		machine, settings = userSetup()
	elif nextStep=='3':
		print 'Restoring machine setttings...'
		machine = enigmaMachine(*settings)
	plaintext = raw_input('Enter the plaintext message you would like to encrypt: ')
	plaintext=plaintext.translate(None, string.punctuation).upper().replace(' ','')
	ciphertext = encrypt(machine,plaintext)
	print 'Encrypted text: '+ciphertext
	print '1 to exit, 2 to return to machine setup, 3 to reset rotors, or 4 to continue:'
	nextStep=raw_input('$: ')
