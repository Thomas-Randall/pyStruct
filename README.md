# pyStruct: Dynamic Structs for Python

Define, update, import, and export struct formats to organize data for Python Runtimes

## Implemented
v0.2: In-editor key features
  + Code simplified to support in-editor actions
  + View current pyStruct in-editor

v0.2.1: Renaming features
  + Rename blueprint namespaces
  + Rename elements
  + Reset editor achieved by exec() over own process

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

## To Be Implemented
+ In-editor deletion, redefinition, editing
+ Generate object instance from blueprint

