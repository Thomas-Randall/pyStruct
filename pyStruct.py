import os

pyStructEditorVersion = "v0.1.1"

# Used in editing/creation of pyStructs
valid_pyStruct_commands = ['declare', 'define']
valid_targets = { 'primary': ['blueprint'],
  'secondary': ['field', 'list', 'dict'] }
valid_dataTypes = ['int', 'integer', 'long', 'float', 'str', 'string']
new_dataTypes = []
pyStructs = {}
recordedTypes = {}

# Exception classes for better debugging
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
        if command not in valid_pyStruct_commands:
          raise pyStructError("Invalid command", command)
        if command == "declare":
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
        # This a non-declare command
        else:
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
            raise pyStructError("Invalid name", "Cannot redefine '"+name+"' in '"+ \
                                primary_target+"' blueprint")
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
              except ValueError as e:
                raise pyStructError("Type disagreement", e.args[0])
            elif dataType == 'long':
              try:
                pyStructs[primary_target][name] = long(initial_value)
              except ValueError as e:
                raise pyStructError("Type disagreement", e.args[0])
            elif dataType == 'float':
              try:
                pyStructs[primary_target][name] = float(initial_value)
              except ValueError as e:
                raise pyStructError("Type disagreement", e.args[0])
            elif dataType == 'str' or dataType == 'string':
              try:
                pyStructs[primary_target][name] = str(initial_value)
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
                  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
              elif dataType == 'long':
                initial_list = initial_value[1:len(initial_value)-1].split(',')
                for value in initial_list:
                  try:
                    pyStructs[primary_target][name].append(long(value))
                  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
              elif dataType == 'float':
                initial_list = initial_value[1:len(initial_value)-1].split(',')
                for value in initial_list:
                  try:
                    pyStructs[primary_target][name].append(float(value))
                  except ValueError as e:
                    raise pyStructError("Type disagreement", e.args[0])
              elif dataType == 'str' or dataType == 'string':
                initial_list = initial_value[1:len(initial_value)-1].split(',')
                for value in initial_list:
                  try:
                    pyStructs[primary_target][name].append(str(value))
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
                    except ValueError as e:
                      raise pyStructError("Type disagreement", e.args[0])
                if dataType == 'long':
                  initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
                  for key, value in initial_dictionary.split(':'):
                    try:
                      pyStructs[primary_target][name][key] = long(value)
                    except ValueError as e:
                      raise pyStructError("Type disagreement", e.args[0])
                if dataType == 'float':
                  initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
                  for key, value in initial_dictionary.split(':'):
                    try:
                      pyStructs[primary_target][name][key] = float(value)
                    except ValueError as e:
                      raise pyStructError("Type disagreement", e.args[0])
                if dataType == 'str' or dataType == 'string':
                  initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
                  for key, value in initial_dictionary.split(':'):
                    try:
                      pyStructs[primary_target][name][key] = str(value)
                    except ValueError as e:
                      raise pyStructError("Type disagreement", e.args[0])
        '''
        print("Structs:")
        print(pyStructs)
        print("Recorded Types:")
        print(recordedTypes)
        '''
  except IOError:
    raise IOError("File '"+fileName+"' does not exist")

'''
  Reverse engineers the pyStruct into a replicable series of commands that allow
  for future re-loading/regeneration. An alternative would be to pickle the structure,
  but this format of data persistence is more resilent to the editable nature of
  pyStructs.
  Theoretically, pyStruct files should be small, and compression can be used if
  that is no longer the case.
'''
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
    for declarable_object in pyStructs.keys():
      output.writelines("declare blueprint "+declarable_object+"\n")
      for definable_element in pyStructs[declarable_object].keys():
        fieldString = str(type(pyStructs[declarable_object][definable_element]))
        fieldString = fieldString[fieldString.find("'")+1:fieldString.rfind("'")]
        if fieldString != "list" and fieldString != "dict":
          fieldString = "field"
        output.writelines("define "+declarable_object+"..."+fieldString+" "+ \
                          definable_element+"..."+ \
                          recordedTypes[declarable_object][definable_element]+"("+ \
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
    command = user_input.split(' ')[0]
    arguments = user_input[len(command)+1:].split(' ')
    if command == "quit":
      print("Shutting down...")
      break
    
    os.system("clear")
    if command == "load":
      try:
        pyStruct_load(arguments)
        print("Successfully loaded")
      except argumentError as e:
        # Recoverable, do not sysexit
        print("ERROR:")
        print(e)
      except IOError as e:
        # File corrupted or otherwise unable to open, allow user to attempt to recover
        print("ERROR:")
        print(e)
      except pyStructError as e:
        # Generally irrecoverable without file modification, sysexit
        raise pyStructError("Potentially irrecoverable issue", e.args[0], e.args[1])
    elif command == "create":
      print("Yup this is a command")
    elif command == "export":
      try:
        pyStruct_export(arguments)
        print("Successfully exported")
      except argumentError as e:
        # Recoverable, do not sysexit
        print("ERROR:")
        print(e)
    else:
      print("Command not recognized")
