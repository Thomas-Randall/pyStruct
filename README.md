# pyStruct: Dynamic Structs for Python

Define, update, import, and export struct formats to organize data for Python Runtimes

## To Be Implemented
+ Unit tests to make sure things remain working (v0.3.1)
+ Generate object instance from blueprint (v0.3.1)
+ In-editor object-instance editing (v0.3.2)

## Implemented
v0.3: PyStruct Class, Redefinition features
  + Basic command layout now associates namespace...element_name field_type...variable_type(initial_value)
  + Redefine an element in a blueprint
  + Soft- or hard-reset the editor
  + Spaces no longer permitted in blueprint names
  + Spaces are now permitted in list/dictionary definitions and within string initializations
  + Deletion now removes associated types etc from types, use 'remove' method rather than 'pop'
  + Argument errors now more common to help when delimiter rules not followed
  + More concise try/catch for errors when defining elements, using functions in pyStruct_load(), main()
  + Class-local template now called pyTemplate rather than somewhat confusing pyStructs

v0.2.2: Deletion features
  + Delete a namespace
  + Delete an element
  + Load command now follows 3-argument format
  + Load commands can be used in pyStruct files
    * Note that the editor's export feature still explicitly exports completely-self-defined pyStructs, meaning that it will not output any load commands
    * Best practice for now is to define/export primitives, reset, define dummy primitives, define/export secondary, then manually edit secondary export to load the primitive export rather than the dummy definitions

v0.2.1: Renaming features
  + Rename blueprint namespaces
  + Rename elements
  + Reset editor achieved by exec() over own process

v0.2: In-editor key features
  + Code simplified to support in-editor actions
  + View current pyStruct in-editor

v0.1: Import and export operations
 + pyStruct formatting and rules:
   * One instruction per line with three fields: command, target, and data
     + Fields are delimited by ' '
     + Subfields are delimited by '...'
     + Tertiary fields are delimited by '()'
   * Commands: declare, define
   * Targets: blueprint (required for declare command) or declared namespace
     + Subtarget: specifies definition as element of type: [field, list, dict]
   * Data: name
     + Subdata: specifies type of data
     + Tertiary data: initial value for definition
   * Formatting delimiters [' ', '...', '()'] are reserved for pyStruct parsing
   * Tertiary data must be supplied for all definitions except strings
