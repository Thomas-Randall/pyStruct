import os

pyStructEditorVersion = "v0.3"

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
  Blueprint names are globally reserved namespaces
  Element names are independently reserved namespaces within blueprints

  Example usage:
  declare blueprint car
  define car...make field...str()
  define car...year field...int(1990)
  define car...previous_owners list...str(Jerry, Tom, Somebody)
  declare blueprint boat
  define boat...dock_coords list...float()
  define boat...last_parked field...str(Yesterday)
'''
class pyStruct:
  # Used in editing/creation of pyStructs
  valid_pyStruct_commands = ['declare', 'define', 'rename', 'redefine',
                             'delete', 'load', 'export']
  def __init__(self):
    self.valid_targets = { 'primary': ['blueprint'],
      'secondary': ['field', 'list', 'dict'] }
    self.valid_dataTypes = ['int', 'integer', 'long', 'float', 'str', 'string']
    self.new_dataTypes = []
    self.pyTemplate = {}
    self.recordedTypes = {}

  # Create new namespace in template
  def pyStruct_declare(self, target, data):
    if target != "blueprint":
      raise pyStructError("Undefined declaration type", target)
    if len(data.split(' ')) > 1:
      raise pyStructError("Invalid name", "Spaces cannot be used in blueprint names")
    if data == "blueprint":
      raise pyStructError("Invalid name", "Namespace 'blueprint' is reserved by pyStruct")
    if data in dir(__builtins__):
      raise pyStructError("Invalid name", "Cannot redefine native Python types")
    if recursive_find_key(self.pyTemplate, data):
      raise pyStructError("Invalid name", "Namespace '"+data+"' is already defined")
    # At this point, the declare command is successful
    self.valid_targets['primary'].append(data)
    self.new_dataTypes.append(data)
    self.pyTemplate[data] = {}
    self.recordedTypes[data] = {}

  # Delete namespace or element from template
  def pyStruct_delete(self, target, data):
    if target == "blueprint":
      if data not in self.valid_targets['primary']:
        raise argumentError("Invalid argument", data, "Is not a proper namespace")
      self.valid_targets['primary'].remove(data)
      self.new_dataTypes.remove(data)
      self.pyTemplate.pop(data, None)
      self.recordedTypes.pop(data, None)
    else:
      if target not in self.valid_targets['primary']:
        raise argumentError("Invalid argument", target, "Is not a proper namespace")
      if data not in self.pyTemplate[target].keys():
        raise pyStructError("Invalid target", "'"+data+"' is not an element in '"+target+"'")
      self.pyTemplate[target].pop(data)
      self.recordedTypes[target].pop(data)

  # Create new element in template under a specific namespace
  def pyStruct_define(self, target, data):
    if len(target.split('...')) != 2:
      raise argumentError("Invalid delimiter count for first argument", "Expected: 2", \
                          "Received", len(target.split('...')))
    namespace_target, name = target.split('...')
    if namespace_target not in self.valid_targets['primary']:
      raise argumentError("Invalid argument", namespace_target, "Is not a proper namespace")
    if name in dir(__builtins__):
      raise pyStructError("Invalid element name", "Cannot redefine native Python types")
    if name in self.pyTemplate.keys():
      raise pyStructError("Invalid element name", "'"+name+"' is already declared as a blueprint")
    if name in self.pyTemplate[namespace_target].keys():
      raise pyStructError("Invalid element name", "Cannot redefine '"+name+"' in '"+ \
                          namespace_target+"' blueprint")
    # Determine validity of new data
    if len(data.split('...')) != 2:
      raise argumentError("Invalid delimiter count for second argument", "Expected: 2", \
                          "Received", len(data.split('...')))
    field_target, metadata = data.split('...')
    if field_target not in self.valid_targets['secondary']:
      raise pyStructError("Invalid element declaration", field_target, "Must be field, list, or dict")
    dataType = metadata[:metadata.find('(')]
    initial_value = metadata[metadata.find('(')+1:metadata.rfind(')')]
    if dataType not in self.valid_dataTypes and dataType not in self.new_dataTypes:
      raise pyStructError("Invalid element data type", dataType)
    # At this point, the define command is successfully formatted
    self.recordedTypes[namespace_target][name] = dataType
    if field_target in self.new_dataTypes:
      self.pyTemplate[namespace_target][name] = initial_value
    # Try catches ValueError (provided type does not match expected type)
    try:
      if field_target == 'field':
        if dataType == 'int' or dataType == 'integer':
          self.pyTemplate[namespace_target][name] = int(initial_value)
        elif dataType == 'long':
          self.pyTemplate[namespace_target][name] = long(initial_value)
        elif dataType == 'float':
          self.pyTemplate[namespace_target][name] = float(initial_value)
        elif dataType == 'str' or dataType == 'string':
          if initial_value.startswith('"') and initial_value.endswith('"'):
            initial_value = initial_value[1:len(initial_value)-1]
          elif initial_value.startswith("'") and initial_value.endswith("'"):
            initial_value = initial_value[1:len(initial_value)-1]
          self.pyTemplate[namespace_target][name] = str(initial_value)
      elif field_target == 'list':
        self.pyTemplate[namespace_target][name] = []
        # Shortcut empty list by omission
        if initial_value.startswith("[") and initial_value.endswith("]"):
          initial_value = initial_value[1:-1]
        if initial_value != "":
          if dataType == 'int' or dataType == 'integer':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][name].append(int(value))
          elif dataType == 'long':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][name].append(long(value))
          elif dataType == 'float':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][name].append(float(value))
          elif dataType == 'str' or dataType == 'string':
            initial_list = initial_value.split(',')
            for value in initial_list:
              value = value.lstrip(' ')
              if (value.startswith('"') and value.endswith('"')):
                value = value[1:len(value)-1]
              elif (value.startswith("'") and value.endswith("'")):
                value = value[1:len(value)-1]
              self.pyTemplate[namespace_target][name].append(str(value))
      elif field_target == 'dict' or field_target == 'dictionary':
        self.pyTemplate[namespace_target][name] = {}
        # Shortcut empty dictionary by omission
        if initial_value.startswith("{") and initial_value.endswith("}"):
          initial_value = initial_value[1:-1]
        if initial_value != "":
          if dataType == 'int' or dataType == 'integer':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for dictionary_entry in initial_dictionary:
              for key, value in dictionary_entry.split(':'):
                self.pyTemplate[namespace_target][name][key] = int(value)
          elif dataType == 'long':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for dictionary_entry in initial_dictionary:
              for key, value in dictionary_entry.split(':'):
                self.pyTemplate[namespace_target][name][key] = long(value)
          elif dataType == 'float':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for dictionary_entry in initial_dictionary:
              for key, value in dictionary_entry.split(':'):
                self.pyTemplate[namespace_target][name][key] = float(value)
          elif dataType == 'str' or dataType == 'string':
            initial_dictionary = initial_value.split(',')
            for dictionary_entry in initial_dictionary:
              for key, value in dictionary_entry.split(':'):
                value = value.lstrip(' ')
                if value.startswith('"') and value.endswith('"'):
                  value = value[1:len(value)-1]
                elif value.startswith("'") and value.endswith("'"):
                  value = value[1:len(value)-1]
                self.pyTemplate[namespace_target][name][key] = str(value)
    except ValueError as e:
      raise pyStructError("Type disagreement", e.args[0])

  # Re-spec an exisiting element (change type, number, and initialization)
  def pyStruct_redefine(self, target, data):
    # Determine validity of target
    namespace_target, field_target = target.split('...')
    if namespace_target not in self.valid_targets['primary']:
      raise argumentError("Invalid argument", namespace_target, "Is not a proper namespace")
    if field_target not in self.pyTemplate[namespace_target].keys():
      raise pyStructError("Invalid target", "'"+field_target+ \
                          "' is not an element in '"+namespace_target+"'")
    # Determine validity of new data
    secondary_target, metadata = data.split('...')
    if secondary_target not in self.valid_targets['secondary']:
      raise pyStructError("Invalid element", secondary_target)
    dataType = metadata[:metadata.find('(')]
    initial_value = metadata[metadata.find('(')+1:metadata.rfind(')')]
    if dataType not in self.valid_dataTypes and dataType not in self.new_dataTypes:
      raise pyStructError("Invalid data type", dataType)
    # At this point, the define command is successfully formatted
    self.recordedTypes[namespace_target][field_target] = dataType
    if secondary_target in self.new_dataTypes:
      self.pyTemplate[namespace_target][field_target] = initial_value
    # Try catches ValueError (provided type does not match expected type)
    try:
      if secondary_target == 'field':
        if dataType == 'int' or dataType == 'integer':
          self.pyTemplate[namespace_target][field_target] = int(initial_value)
        elif dataType == 'long':
          self.pyTemplate[namespace_target][field_target] = long(initial_value)
        elif dataType == 'float':
          self.pyTemplate[namespace_target][field_target] = float(initial_value)
        elif dataType == 'str' or dataType == 'string':
          if initial_value.startswith('"') and initial_value.endswith('"'):
            initial_value = initial_value[1:len(initial_value)-1]
          elif initial_value.startswith("'") and initial_value.endswith("'"):
            initial_value = initial_value[1:len(initial_value)-1]
          self.pyTemplate[namespace_target][field_target] = str(initial_value)
      elif secondary_target == 'list':
        self.pyTemplate[namespace_target][field_target] = []
        # Shortcut empty list by omission
        if initial_value != "[]":
          if dataType == 'int' or dataType == 'integer':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][field_target].append(int(value))
          elif dataType == 'long':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][field_target].append(long(value))
          elif dataType == 'float':
            initial_list = initial_value[1:len(initial_value)-1].split(',')
            for value in initial_list:
              self.pyTemplate[namespace_target][field_target].append(float(value))
          elif dataType == 'str' or dataType == 'string':
            initial_list = initial_value.split(',')
            for value in initial_list:
              if (value.startswith('"') and value.endswith('"')):
                value = value[1:len(value)-1]
              elif (value.startswith("'") and value.endswith("'")):
                value = value[1:len(value)-1]
              self.pyTemplate[namespace_target][field_target].append(str(value))
      elif secondary_target == 'dict' or secondary_target == 'dictionary':
        self.pyTemplate[namespace_target][field_target] = {}
        # Shortcut empty dictionary by omission
        if initial_value != "{}":
          if dataType == 'int' or dataType == 'integer':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for key, value in initial_dictionary.split(':'):
              self.pyTemplate[namespace_target][field_target][key] = int(value)
          if dataType == 'long':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for key, value in initial_dictionary.split(':'):
              self.pyTemplate[namespace_target][field_target][key] = long(value)
          if dataType == 'float':
            initial_dictionary = initial_value[1:len(initial_value)-1].split(',')
            for key, value in initial_dictionary.split(':'):
              self.pyTemplate[namespace_target][field_target][key] = float(value)
          if dataType == 'str' or dataType == 'string':
            initial_dictionary = initial_value.split(',')
            for key, value in initial_dictionary.split(':'):
              if value.startswith('"') and value.endswith('"'):
                value = value[1:len(value)-1]
              elif value.startswith("'") and value.endswith("'"):
                value = value[1:len(value)-1]
              self.pyTemplate[namespace_target][field_target][key] = str(value)
    except ValueError as e:
      raise pyStructError("Type disagreement", e.args[0])

  # Change the name of a blueprint or element in a namespace
  def pyStruct_rename(self, target, data):
    namespace_target, specific_target = target.split('...')
    if namespace_target not in self.valid_targets['primary']:
      raise argumentError("Invalid argument", namespace_target, "Is not a proper namespace")
    if namespace_target == "blueprint":
      # Redefine a blueprint name
      if specific_target not in self.valid_targets['primary']:
        raise argumentError("Invalid argument", specific_target, "Is not a proper namespace")
      if len(data.split(' ')) > 1:
        raise pyStructError("Invalid name", "Spaces cannot be used in blueprint names")
      if data == "blueprint":
        raise pyStructError("Invalid name", "Namespace 'blueprint' is reserved by pyStruct")
      if data in dir(__builtins__):
        raise pyStructError("Invalid name", "Cannot redefine native Python types")
      if data in self.valid_targets['primary']:
        raise pyStructError("Invalid name", "Namespace '"+data+"' is already defined")
      # At this point, the rename command is successful
      recursive_replace_key(self.pyTemplate, specific_target, data)
      recursive_replace_key(self.recordedTypes, specific_target, data)
      recursive_replace_value(self.recordedTypes, specific_target, data)
      self.valid_targets['primary'].remove(specific_target)
      self.valid_targets['primary'].append(data)
    else:
      # Redefine an element name
      if specific_target not in self.pyTemplate[namespace_target].keys():
        raise pyStructError("Invalid target", "'"+specific_target+ \
                            "' is not an element in '"+namespace_target+"'")
      if data in dir(__builtins__):
        raise pyStructError("Invalid name", "Cannot redefine native Python types")
      if data in self.pyTemplate.keys():
        raise pyStructError("Invalid name", "'"+data+"' is already declared as a blueprint")
      if data in self.pyTemplate[namespace_target].keys():
        raise pyStructError("Invalid name", "Cannot duplicate '"+data+"' in '"+ \
                            namespace_target+"' blueprint")
      # At this point, the rename command is successful
      recursive_replace_key(self.pyTemplate, specific_target, data)
      recursive_replace_key(self.recordedTypes, specific_target, data)

  # Load pyStruct instructions from a file
  def pyStruct_load(self, fileStr, fileName):
    if fileStr != "file":
      raise argumentError("Invalid load format")
    try:
      pyStructFile = open(fileName, 'r')
    except IOError:
      raise IOError("File '"+fileName+"' could not be opened")
    else:
      line_num = 0
      for instruction in pyStructFile:
        line_num += 1
        instruction = instruction.rstrip('\n')
        if instruction == '':
          continue
        # Valid pyStruct instructions must have 3 parts
        instruction = instruction.split(' ')
        if len(instruction) < 3:
          raise pyStructError("Improperly formatted instruction", instruction[0], \
                              "at "+fileName+":"+str(line_num))
        # Force 3-argument format from file
        elif len(instruction) > 3:
          for extraArg in instruction[3:]:
            instruction[2] += str(extraArg)
            instruction.remove(extraArg)
        # Verify all three parts of pyStruct instruction
        command, target, data = instruction
        if command not in self.valid_pyStruct_commands:
          raise pyStructError("Invalid command", command, "at "+fileName+":"+str(line_num))
        try:
          if command == "declare":
            self.pyStruct_declare(target, data)
          elif command == "delete":
            self.pyStruct_delete(target, data)
          elif command == "define":
            self.pyStruct_define(target, data)
          elif command == "redefine":
            self.pyStruct_redefine(target, data)
          elif command == "rename":
            self.pyStruct_rename(target, data)
          elif command == "load":
            try:
              self.pyStruct_load(target, data)
            except (argumentError, IOError) as e:
              raise pyStructError(str(e), "at "+fileName+":"+str(line_num))
        except pyStructError as e:
          raise pyStructError(str(e), "at "+fileName+":"+str(line_num))
      pyStructFile.close()

  '''
    Reverse engineers the pyStruct into a replicable series of commands that allow
    for future re-loading/regeneration. An alternative would be to pickle the structure,
    but this format of data persistence is more resilent to the editable nature of
    pyStructs.
    Theoretically, pyStruct files should be small, and compression can be used if
    that is no longer the case.

    Note that exporting consolidates the current data structure into ONE SELF-SUFFICIENT FILE,
    that is to say it will not include any calls to load external data. Modular exporting is
    not supported at this time, so it is encouraged to build primitives, export, reset, redefine
    primitives (for dictionary agreement only), build secondary layers, and export, then manually
    substitute the secondary layers' empty definitions with a suitable load command
  '''
  def pyStruct_export(self, *args):
    if len(args[0]) != 1 and len(args[0]) != 2:
      raise argumentError("Requires one or two arguments", "(1) File to be opened (2) Force overwrite")
    fileName = args[0][0]
    forceOverwrite = False
    if len(args[0]) == 2:
      forceOverwrite = args[0][1].lower() == 'true'
    if not forceOverwrite and os.path.exists(fileName):
      raise argumentError("File already exists!", "Can force overwrite with argument 'True'")
    with open(fileName, 'w') as output:
      for declarable_object in self.pyTemplate.keys():
        output.writelines("declare blueprint "+declarable_object+"\n")
        for definable_element in self.pyTemplate[declarable_object].keys():
          fieldString = str(type(self.pyTemplate[declarable_object][definable_element]))
          fieldString = fieldString[fieldString.find("'")+1:fieldString.rfind("'")]
          if fieldString != "list" and fieldString != "dict":
            fieldString = "field"
          try:
            output.writelines("define "+declarable_object+"..."+fieldString+" "+ \
                              definable_element+"..."+ \
                              self.recordedTypes[declarable_object][definable_element]+"("+ \
                              str(self.pyTemplate[declarable_object][definable_element]).replace(' ','')+")\n")
          except KeyError as e:
            print('Struct:')
            print(self.pyTemplate)
            print('Types:')
            print(self.recordedTypes)
            print('at:'+str(declarable_object)+': '+str(definable_element))
            raise e
        output.writelines('\n')

# Live command loop environment
if __name__ == "__main__":
  os.system("clear")
  print("Welcome to pyStruct Editor "+pyStructEditorVersion+"!")
  prompt = "COMMANDS:\n" \
    "load file [path/name] : Read pyStruct from file\n" \
    "declare blueprint [namespace] : Add a namespace to the working pyStruct\n" \
    "define [namespace]...[name] [field, list, dict]...[type](initial_value) :" \
    " Define an element in namespace\n" \
    "redefine [namespace]...[element] [field, list, dict]...[type](initial_value)" \
    " : Redefine an element's amount, type and initial value\n" \
    "rename blueprint...[namespace] [newname] : Rename a namespace\n" \
    "rename [namespace]...[element] [newname] : Rename a defined element\n" \
    "delete blueprint [namespace] : Delete target namespace\n" \
    "delete [namespace] [element] : Delete element in target namespace\n" \
    "view : Visualize the current pyStruct \n" \
    "export [file] : Export current pyStruct to file\n" \
    "reset : Restart the editor (note: do not use this command from other programs) \n" \
    "quit : Exit the editor\n" \
    "more to come soon!\n"
  pyObj = pyStruct()
  while True:
    command = target_argument = data_argument = ''
    user_input = raw_input(prompt)
    command = user_input
    if len(user_input.split(' ')) >= 2:
      command = user_input.split(' ')[0]
      target_argument = user_input.split(' ')[1]
      if len(user_input.split(' ')) >= 3:
        data_argument = user_input[len(command)+len(target_argument)+2:]

    '''
    print "Command: '"+command+"'"
    print "Targ: '"+target_argument+"'"
    print "Data: '"+data_argument+"'"
    '''

    if command == "quit":
      print("Shutting down...")
      break
    if command == "reset":
      if target_argument == "hard":
        os.system("python "+os.path.basename(__file__))
        break
      else:
        del pyObj
        pyObj = pyStruct()
        os.system("clear")
        print("PyStruct object successfully reset")
        continue

    os.system("clear")
    try:
      if command == "load":
        try:
          pyObj.pyStruct_load(target_argument, data_argument)
          print("Successfully loaded")
        except IOError as e:
          # File corrupted or otherwise unable to open
          print("ERROR: "+str(e))
      elif command == "declare":
        pyObj.pyStruct_declare(target_argument, data_argument)
        print("Successfully declared")
      elif command == "delete":
        pyObj.pyStruct_delete(target_argument, data_argument)
        print("Successfully deleted")
      elif command == "define":
        pyObj.pyStruct_define(target_argument, data_argument)
        print("Successfully defined")
      elif command == "redefine":
        pyObj.pyStruct_redefine(target_argument, data_argument)
        print("Successfully redefined")
      elif command == "rename":
        pyObj.pyStruct_rename(target_argument, data_argument)
        print("Successfully renamed")
      elif command == "view":
        print('Saved data structures:')
        print(pyObj.pyTemplate)
        print('Saved type associations:')
        print(pyObj.recordedTypes)
      elif command == "export":
        arguments = []
        for item in target_argument, data_argument:
          if item != '':
            arguments.append(item)
        pyObj.pyStruct_export(arguments)
        print("Successfully exported")
      else:
        print("Command not recognized")
    except IndexError as e:
      print("ERROR: Too few arguments supplied")
    except (argumentError, pyStructError) as e:
      print("ERROR: "+str(e))

