import os

pyStructEditorVersion = "v0.2.2"

# Used in editing/creation of pyStructs
valid_pyStruct_commands = ['declare', 'define', 'rename']
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

# Helper function: Renames target dictionary key to replace (works in nested dicts)
def recursive_replace_key(dictionary, target, replace):
  for key, value in dictionary.iteritems():
    if key == target:
      dictionary[replace] = dictionary.pop(target)
    if isinstance(value, dict):
      recursive_replace_key(value, target, replace)

# Helper function: Renames target dictionary values to replace (works in nested dicts)
def recursive_replace_value(dictionary, target, replace):
  for key, value in dictionary.iteritems():
    if value == target:
      dictionary[key] = replace
    if isinstance(value, dict):
      recursive_replace_value(value, target, replace)

# Helper function: True if key exists in dictionary (works in nested dicts)
def recursive_find_key(dictionary, target):
  for key, value in dictionary.iteritems():
    if key == target:
      return True
    if isinstance(value, dict):
      if recursive_find_key(value, target):
        return True
  return False

# Helper function: True if value exists in dictionary (works in nested dicts)
def recursive_find_value(dictionary, target):
  for key, value in dictionary.iteritems():
    if value == target:
      return True
    if isinstance(value, dict):
      if recursive_find_value(value, target):
        return True
  return False

'''
  Requires one argument: filename to open to create pyStruct from
  Uses variadic argument to elegantly handle user failure during runtime
  Blueprint names are globally reserved namespaces
  Element names are independently reserved namespaces within blueprints

  Ex:
  declare blueprint car
  define car...field make...str()
  define car...field year...int(1990)
  define car...list previous_owners...str([])
  declare blueprint boat
  define boat...field make...str()
  define boat...field year...int(2000)
'''

def pyStruct_declare(target, data):
  if len(target.split('...')) != 1:
    raise pyStructError("Invalid declaration", "No target subdivision for declarations")
  primary_target = target
  name = data
  if name in dir(__builtins__):
    raise pyStructError("Invalid name", "Cannot redefine native Python types")
  if name == "blueprint":
    raise pyStructError("Invalid name", "Namespace 'blueprint' is reserved by pyStruct")
  if recursive_find_key(pyStructs, name):
    raise pyStructError("Clobbering dictionary", "'"+name+"' is already defined")
  # At this point, the declare command is successful
  valid_targets['primary'].append(name)
  new_dataTypes.append(name)
  pyStructs[name] = {}
  recordedTypes[name] = {}

def pyStruct_define(target, data):
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
  if name in pyStructs.keys():
    raise pyStructError("Invalid name", "'"+name+"' is already declared as a blueprint")
  if name in pyStructs[primary_target].keys():
    raise pyStructError("Invalid name", "Cannot redefine '"+name+"' in '"+ \
                        primary_target+"' blueprint")
  dataType = metadata[:metadata.find("(")]
  initial_value = metadata[metadata.find("(")+1:metadata.rfind(")")]
  if dataType not in valid_dataTypes and dataType not in new_dataTypes:
    raise pyStructError("Invalid data type", dataType)
  # At this point, the define command is successful
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
        if initial_value.startswith('"') and initial_value.endswith('"'):
          initial_value = initial_value[1:len(initial_value)-1]
        elif initial_value.startswith("'") and initial_value.endswith("'"):
          initial_value = initial_value[1:len(initial_value)-1]
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
        initial_list = initial_value.split(',')
        for value in initial_list:
          try:
            if (value.startswith('"') and value.endswith('"')):
              value = value[1:len(value)-1]
            elif (value.startswith("'") and value.endswith("'")):
              value = value[1:len(value)-1]
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
          initial_dictionary = initial_value.split(',')
          for key, value in initial_dictionary.split(':'):
            try:
              if value.startswith('"') and value.endswith('"'):
                value = value[1:len(value)-1]
              elif value.startswith("'") and value.endswith("'"):
                value = value[1:len(value)-1]
              pyStructs[primary_target][name][key] = str(value)
            except ValueError as e:
              raise pyStructError("Type disagreement", e.args[0])

def pyStruct_rename(target, data):
  namespace_target, specific_target = target.split('...')
  if namespace_target not in valid_targets['primary']:
    raise argumentError("Invalid argument", namespace_target, "Is not a proper namespace")
  if namespace_target == "blueprint":
    # Redefine a blueprint name
    if specific_target not in valid_targets['primary']:
      raise argumentError("Invalid argument", specific_target, "Is not a proper namespace")
    if data in valid_targets['primary']:
      raise pyStructError("Clobbered dictionary", "Cannot duplicate namespace", data)
    if data in dir(__builtins__):
      raise pyStructError("Invalid name", "Cannot redefine native Python types")
    if data == "blueprint":
      raise pyStructError("Invalid name", "Namespace 'blueprint' is reserved by pyStruct")
    # At this point, the rename command is successful
    recursive_replace_key(pyStructs, specific_target, data)
    recursive_replace_key(recordedTypes, specific_target, data)
    recursive_replace_value(recordedTypes, specific_target, data)
    valid_targets['primary'].remove(specific_target)
    valid_targets['primary'].append(data)
  else:
    # Redefine an element name
    if specific_target not in pyStructs[namespace_target].keys():
      raise pyStructError("Invalid target", "'"+specific_target+ \
                          "' is not an element in '"+namespace_target+"'")
    if data in dir(__builtins__):
      raise pyStructError("Invalid name", "Cannot redefine native Python types")
    if data in pyStructs.keys():
      raise pyStructError("Invalid name", "'"+data+"' is already declared as a blueprint")
    if data in pyStructs[namespace_target].keys():
      raise pyStructError("Invalid name", "Cannot duplicate '"+data+"' in '"+ \
                          namespace_target+"' blueprint")
    # At this point, the rename command is successful
    recursive_replace_key(pyStructs, specific_target, data)
    recursive_replace_key(recordedTypes, specific_target, data)

def pyStruct_load(*fileName):
  if len(fileName[0]) != 1:
    raise argumentError("Requires one argument", "File to be opened")
  fileName = fileName[0][0]
  try:
    pyStructFile = open(fileName, 'r')
  except IOError:
    raise IOError("File '"+fileName+"' does not exist")
  else:
    line_num = 0
    for instruction in pyStructFile:
      line_num += 1
      instruction = instruction.rstrip('\n')
      if instruction == '':
        continue
      # Valid pyStruct instructions must have 3 parts
      instruction = instruction.split(' ')
      if len(instruction) != 3:
        raise pyStructError("Improperly formatted instruction", instruction[0], \
                            "at "+fileName+":"+str(line_num))
      # Verify all three parts of pyStruct instruction
      command, target, data = instruction
      if command not in valid_pyStruct_commands:
        raise pyStructError("Invalid command", command, \
                            "at "+fileName+":"+str(line_num))
      if command == "declare":
        try:
          pyStruct_declare(target, data)
        except pyStructError as e:
          raise pyStructError(str(e), "at "+fileName+":"+str(line_num))
      elif command == "define":
        try:
          pyStruct_define(target, data)
        except pyStructError as e:
          raise pyStructError(str(e), "at "+fileName+":"+str(line_num))
      elif command == "rename":
        try:
          pyStruct_rename(target, data)
        except pyStructError as e:
          raise pyStructError(str(e), "at "+fileName+":"+str(line_num))
    pyStructFile.close()
    '''
    print("Structs:")
    print(pyStructs)
    print("Recorded Types:")
    print(recordedTypes)
    '''

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
        try:
          output.writelines("define "+declarable_object+"..."+fieldString+" "+ \
                            definable_element+"..."+ \
                            recordedTypes[declarable_object][definable_element]+"("+ \
                            str(pyStructs[declarable_object][definable_element]).replace(' ','')+")\n")
        except KeyError as e:
          print('Struct:')
          print(pyStructs)
          print('Types:')
          print(recordedTypes)
          print('at:'+str(declarable_object)+': '+str(definable_element))
          raise e
      output.writelines('\n')

if __name__ == "__main__":
  os.system("clear")
  print("Welcome to pyStruct Editor "+pyStructEditorVersion+"!")
  prompt = "COMMANDS:\n" \
    "load [file] : Read pyStruct from file\n" \
    "declare blueprint [namespace] : Add a namespace to the working pyStruct\n" \
    "define  [namespace]...[field, list, dict] [name]...[type](initial_value) :" \
    " Define an element in namespace\n" \
    "rename blueprint...[namespace] [newname] : Rename a namespace\n" \
    "rename [namespace]...[element] [newname] : Rename a defined element\n" \
    "view : Visualize the current pyStruct \n" \
    "export [file] : Export current pyStruct to file\n" \
    "reset : Restart the editor (note: do not use this command from other programs) \n" \
    "quit : Exit the editor\n" \
    "more to come soon!\n"
  while True:
    user_input = raw_input(prompt)
    command = user_input.split(' ')[0]
    arguments = user_input[len(command)+1:].split(' ')
    if command == "quit":
      print("Shutting down...")
      break
    if command == "reset":
      os.system("python "+os.path.basename(__file__))
      break

    os.system("clear")
    try:
      if command == "load":
        try:
          pyStruct_load(arguments)
          print("Successfully loaded")
        except IOError as e:
          # File corrupted or otherwise unable to open
          print("ERROR:")
          print(e)
      elif command == "declare":
        pyStruct_declare(arguments[0], arguments[1])
        print("Successfully declared")
      elif command == "define":
        pyStruct_define(arguments[0], arguments[1])
        print("Successfully defined")
      elif command == "rename":
        pyStruct_rename(arguments[0], arguments[1])
        print("Successfully renamed")
      elif command == "view":
        print('Saved data structures:')
        print(pyStructs)
        print('Saved type associations:')
        print(recordedTypes)
      elif command == "export":
        pyStruct_export(arguments)
        print("Successfully exported")
      else:
        print("Command not recognized")
    except IndexError as e:
      print("ERROR: Too few arguments supplied")
    except (argumentError, pyStructError) as e:
      print("ERROR:")
      print(e)
