import os

pyStructEditorVersion = "v0.1"

# Used in editing/creation of pyStructs
valid_commands = ['declare', 'define']
valid_targets = { 'primary': ['blueprint'],
                  'secondary': ['field', 'list', 'dict'] }
valid_dataTypes = ['int', 'integer', 'long', 'float', 'str', 'string']
new_dataTypes = []
pyStructs = {}
recordedTypes = {}

class argumentError(Exception):
  ''' Raise when invalid number of arguments are supplied to a function '''
  def __init__(self, message, *extra):
    # Prevent DeprecationWarning on direct access to message
    self.message = message
    # Additional information available in .extra
    self.extra = extra
    '''
    Call the base class constructor with the parameters it needs
    Allows users to initialize miscellaneous arguments as with any other
    builtin error
    '''
    super(argumentError, self).__init__(message, *extra)
  # Print all extra information in a nice way
  def __str__(self):
    full_message = self.message
    for item in self.extra:
      full_message += ": "+str(item)
    return full_message

class pyStructError(Exception):
  ''' Raise when a pyStruct Error occurs '''
  def __init__(self, message, *extra):
    # Prevent DeprecationWarning on direct access to message
    self.message = message
    # Additional information available in .extra
    self.extra = extra
    '''
    Call the base class constructor with the parameters it needs
    Allows users to initialize miscellaneous arguments as with any other
    builtin error
    '''
    super(pyStructError, self).__init__(message, *extra)
  # Print all extra information in a nice way
  def __str__(self):
    full_message = self.message
    for item in self.extra:
      full_message += ": "+str(item)
    return full_message



'''
Requires one argument: filename to open to create pyStruct from
Uses variadic argument to elegantly handle user failure during runtime

For now, instructions in pyStruct Files work as follows:
* One instruction can be written per line
* Space and triple-period delimiters must be observed where indicated
* It is invalid to include the substring '...' as part of an initial value (because I am not smart enough to make that work at the moment)
* The initial value field is optional for strings ONLY

  1) Declare a blueprint:
     declare blueprint name
       * name: indicates the name of the new blueprint
  2) Define an element in a blueprint:
     define [namespace]...[element] name...type(initial_value)
       * namespace: a blueprint namespace (must be previously declared)
       * element: must be one of the following: [field, list, dict]
       * name: indicates the name of the new element
       * type: indicates the type of the new element (does not support list or dict)
       * initial_value: indicates the default value for the element
  Ex:
    declare blueprint car
    define car...field make...str()
    define car...field year...int(1990)
    define car...list previous_owners...str([])
'''
def pyStruct_load(*fileName):
  if len(fileName[0]) != 1:
    raise argumentError("Requires one argument", "File to be opened")
  fileName = fileName[0][0]
  try:
    with open(fileName, 'r') as pyStructFile:
      for instruction in pyStructFile:
        instruction = instruction.rstrip('\n')
        if instruction == '':
          continue
	# Valid pyStruct instructions must have 3 parts
        instruction = instruction.split(' ')
	if len(instruction) != 3:
          raise pyStructError("Improperly formatted instruction", instruction[0])
        # Verify all three parts of pyStruct instruction
	command, target, data = instruction
	if command not in valid_commands:
	  raise pyStructError("Invalid command", command)
	if command != "declare":
          primary_target = target.split('...')[0]                              
          if primary_target not in valid_targets['primary']:                 
 	    raise pyStructError("Invalid namespace", primary_target)         
	  if len(target.split('...')) == 2:
	    secondary_target = target.split('...')[1]
	    if secondary_target not in valid_targets['secondary']:
	      raise pyStructError("Invalid element", secondary_target)
	  if len(data.split('...')) != 2:
	    raise pyStructError("Invalid data", data)
	  name, metadata = data.split('...')
	  if name in dir(__builtins__):
	    raise pyStructError("Invalid name", "Cannot redefine native Python types")
	  if name in pyStructs[primary_target]:
	    raise pyStructError("Invalid name", "Cannot redefine '"+name+"' in '"+primary_target+"' blueprint")
	  dataType = metadata[:metadata.find("(")]
	  initial_value = metadata[metadata.find("(")+1:metadata.rfind(")")]
	  if dataType not in valid_dataTypes and dataType not in new_dataTypes:
	    raise pyStructError("Invalid data type", dataType)
	  # At this point, the non-declare command is successful
	  recordedTypes[primary_target][name] = dataType
	  if secondary_target in new_dataTypes:
	    pyStructs[primary_target][name] = initial_value
	  if secondary_target == 'field':
	    if dataType == 'int' or dataType == 'integer':
	      try:
	        pyStructs[primary_target][name] = int(initial_value)
		recordedTypes[primary_target][name] = 'int'
              except ValueError as e:
	        raise pyStructError("Type disagreement", e.args[0])
	    elif dataType == 'long':
	      try:
	        pyStructs[primary_target][name] = long(initial_value)
		recordedTypes[primary_target][name] = 'long'
	      except ValueError as e:
	        raise pyStructError("Type disagreement", e.args[0])
	    elif dataType == 'float':
	      try:
	        pyStructs[primary_target][name] = float(initial_value)
		recordedTypes[primary_target][name] = 'float'
	      except ValueError as e:
	        raise pyStructError("Type disagreement", e.args[0])
	    elif dataType == 'str' or dataType == 'string':
	      try:
	        pyStructs[primary_target][name] = str(initial_value)
		recordedTypes[primary_target][name] = 'str'
	      except ValueError as e:
	        raise pyStructError("Type disagreement", e.args[0])
	  elif secondary_target == 'list':
	    pyStructs[primary_target][name] = []
	    # Shortcut empty list by omission
	    if initial_value != "[]":
	      if dataType == 'int' or dataType == 'integer':
	        initial_list = initial_value[1:len(initial_value)-1].split(',')
	        for value in initial_list:
		  try:
		    pyStructs[primary_target][name].append(int(value))
		    recordedTypes[primary_target][name] = 'int'
	          except ValueError as e:
		    raise pyStructError("Type disagreement", e.args[0])
              elif dataType == 'long':
	        initial_list = initial_value[1:len(initial_value)-1].split(',')
	        for value in initial_list:
	          try:
	            pyStructs[primary_target][name].append(long(value))
		    recordedTypes[primary_target][name] = 'long'
	          except ValueError as e:
	            raise pyStructError("Type disagreement", e.args[0])
	      elif dataType == 'float':
	        initial_list = initial_value[1:len(initial_value)-1].split(',')
                for value in initial_list:
	          try:
	            pyStructs[primary_target][name].append(float(value))
		    recordedTypes[primary_target][name] = 'float'
                  except ValueError as e:
	            raise pyStructError("Type disagreement", e.args[0])
	      elif dataType == 'str' or dataType == 'string':
	        initial_list = initial_value[1:len(initial_value)-1].split(',')
	        for value in initial_list:
                  try:
	            pyStructs[primary_target][name].append(str(value))
		    recordedTypes[primary_target][name] = 'str'
	          except ValueError as e:
	            raise pyStructError("Type disagreement", e.args[0])
	  elif secondary_target == 'dict' or secondary_target == 'dictionary':
	    pyStructs[primary_target][name] = {}
	    # Shortcut empty dictionary by omission
	    if initial_value != "{}":
	      if dataType == 'int' or dataType == 'integer':
		initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
		for key, value in initial_dictionary.split(':'):
		  try:
		    pyStructs[primary_target][name][key] = int(value)
		    recordedTypes[primary_target][name] = 'int'
		  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
	      if dataType == 'long':
		initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
		for key, value in initial_dictionary.split(':'):
		  try:
		    pyStructs[primary_target][name][key] = long(value)
		    recordedTypes[primary_target][name] = 'long'
		  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
	      if dataType == 'float':
		initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
		for key, value in initial_dictionary.split(':'):
		  try:
		    pyStructs[primary_target][name][key] = float(value)
		    recordedTypes[primary_target][name] = 'float'
		  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
	      if dataType == 'str' or dataType == 'string':
		initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
		for key, value in initial_dictionary.split(':'):
		  try:
		    pyStructs[primary_target][name][key] = str(value)
		    recordedTypes[primary_target][name] = 'str'
		  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
	else:
          if len(target.split('...')) != 1:
	    raise pyStructError("Invalid declaration", "No target subdivision for declarations")
	  primary_target = target
	  name = data
	  if name in dir(__builtins__):
	    raise pyStructError("Invalid name", "Cannot redefine native Python types")
	  # At this point, the declare command is successful
          valid_targets['primary'].append(name)
          new_dataTypes.append(name)
	  pyStructs[name] = {}
          recordedTypes[name] = {}

	print("Successfully read instruction")
	'''
	print("Command: "+command+"\nPrimary Target: "+primary_target)
	if len(target.split('...')) == 2:
	  print("Secondary Target: "+secondary_target)
	print("Name: "+name)
	if command != "declare":
	  print("Data Type: "+dataType+"\nInitial Value: "+initial_value)
        '''
	print(pyStructs)
  except IOError:
    raise IOError("File '"+fileName+"' does not exist")

def pyStruct_export(*args):
  if len(args[0]) != 1 and len(args[0]) != 2:
    raise argumentError("Requires one or two arguments", "(1) File to be opened (2) Force overwrite")
  fileName = args[0][0]
  forceOverwrite = False
  if len(args[0]) == 2:
    forceOverwrite = args[0][1].lower() == 'true'
  if not forceOverwrite and os.path.exists(fileName):
    raise argumentError("File already exists!", "Can force overwrite with argument 'True'")
  with open(fileName, 'w') as output:
    '''
    Cleverly reverse engineer the pyStruct into a replicable series of commands to clone it later
    Possible to pickle it, but this format makes editing cleaner and these things, at least
    theoretically, should not get so large as to take up noticeable disk space (and in such cases,
    compression can be used)
    '''
    for declarable_object in pyStructs.keys():
      output.writelines("declare blueprint "+declarable_object+"\n")
      for definable_element in pyStructs[declarable_object].keys():
        typeString = str(type(pyStructs[declarable_object][definable_element]))
        typeString = typeString[typeString.find("'")+1:typeString.rfind("'")]
        if typeString == "list" or typeString == "dict":
          fieldString = typeString
        else:
          fieldString = "field"
        output.writelines("define "+declarable_object+"..."+fieldString+ \
        " "+definable_element+"..."+recordedTypes[declarable_object][definable_element]+"("+ \
        str(pyStructs[declarable_object][definable_element]).replace(' ','')+")\n")
      output.writelines('\n')

if __name__ == "__main__":
  print("Welcome to pyStruct Editor "+pyStructEditorVersion+"!")
  prompt = "COMMANDS:\n" \
	   "load [file] : Read pyStruct file\n" \
	   "create [file] : Create a new pyStruct file\n" \
	   "export [file] : Export current pyStruct to file\n" \
	   "quit : Exit the editor\n" \
	   "more to come soon!\n"
  while True:
    user_input = raw_input(prompt).lower()
    os.system("clear")
    command = user_input.split(' ')[0]
    arguments = user_input[len(command)+1:].split(' ')
    if command == "quit":
      break
    elif command == "load":
      try:
        pyStruct_load(arguments)
      except argumentError as e:
        # Recoverable, do not sysexit
	print("ERROR:")
	print(e)
	raw_input("Press ENTER to continue")
      except IOError as e:
        # File corrupted or otherwise unable to open,
	# allow user to attempt to recover
	print("ERROR:")
	print(e.message)
	raw_input("Press ENTER to continue")
      except pyStructError as e:
        # Generally irrecoverable without file modification, sysexit
        raise pyStructError("Potentially irrecoverable issue", e.args[0], e.args[1])
    elif command == "create":
      print("Yup this is a command")
    elif command == "export":
      try:
        pyStruct_export(arguments)
      except argumentError as e:
        # Recoverable, do not sysexit
	print("ERROR:")
	print(e)
	raw_input("PRess ENTER to continue")
    else:
      print("Command not recognized")

