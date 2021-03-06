### README - gaplint
---
Gaplint automatically checks the format of a GAP file according to some conventions, *rules*. It prints the nature and location of instances of incorrect formatting as well as correcting others.

### 1. Rules
---
***Rules that report formatting errors (codes begin with 'W' for 'warning'):***

| Code | Name | Rule Description |
| --- | --- | --- |
| `W001` | `line-too-long` | Max 80 characters per line |
| `W002` | `empty-lines` | No consecutive empty lines |
| `W003` | `trailing-whitespace` | No whitespace at the end of a line |
| `W004` | `indentation` | Minimum indentation level required |
| `W005` | `space-after-comma` | Exactly one space after a comma |
| `W006` | `space-before-comma` | No spaces before a comma |
| `W007` | `space-after-bracket` | No spaces after a bracket |
| `W008` | `space-before-bracket` | No spaces before a bracket |
| `W009` | `multiple-semicolons` | Not more than one semicolon per line |
| `W010` | `keyword-function` | Keyword *function* must be followed by an open bracket |
| `W011` | `whitespace-op-colon-equals` | Exactly one space either side of a colon-equals (:=) operator |
| `W012` | `tabs` | Replace inline tabs with spaces |
| `W013` | `function-local-same-line` | Keywords *function* and *local* cannot appear in the same line |
| `W014` | `whitespace-op-plus` | Exactly one space either side of a plus (+) operator  |
| `W015` | `whitespace-op-multiply` | Exactly one space either side of a multiply (\*) operator |
| `W016` | `whitespace-op-negative` | Exactly one space preceding a negative (-) operator |
| `W017` | `whitespace-op-minus` | Exactly one space either side of a minus (-) operator |
| `W018` | `whitespace-op-less-than` | Exactly one space either side of a less-than (<) operator |
| `W019` | `whitespace-op-less-equal` | Exactly one space either side of a less-than / equal-to (<=) operator |
| `W020` | `whitespace-op-more-than` | Exactly one space either side of a greater-than(>) operator |
| `W021` | `whitespace-op-more-equal` | Exactly one space either side of greater-than / equal-to (>=) operator |
| `W022` | `whitespace-op-equals` | Exactly one space either side of equals (=) operator |
| `W023` | `whitespace-op-mapping` | Exactly one space either side of mapping (->) operator |
| `W024` | `whitespace-op-divide` | Exactly one space either side of divide (/) operator | 
| `W025` | `whitespace-op-power` | No spaces either side of power (^) operator |
| `W026` | `whitespace-op-not-equal` | Exactly one space either side of not-equal (<>) operator |
| `W027` | `whitespace-op-double-dot` | Exactly one space either side of arithmetic progression (\.\.) operator |
| `W028` | `unused-local-variables` | All declared local variables must be used |

***Rules that correct formatting errors (codes begin with 'M' for 'modify'):***

| Code | Name | Rule Description |
| --- | --- | --- |
| `M001` | `remove-comments` | Truncates a line to remove comments to avoid matching linting issues within comments where the issues do not apply. |
| `M002` | `replace-multiline-strings` | Modifies a line, removing multiline strings to avoid matching linting issues within comments where the issues do not apply. |
| `M003` | `replace-double-quotes` | Removes everything between non-escaped double-quotes in a line to avoid matching linting issues where they do not apply. A line's length and content is altered so if either of these is important for another rule, that rule should be run before this one. |
| `M004` | `replace-escaped-quotes` | Removes escaped quotes in a line to avoid matching linting issues where they do not apply. A line's length and content is altered so if either of these is important for another rule, that rule should be run before this one. |

***The*** **`all`** ***"rule":***

| Code | Name | Rule Description |
| --- | --- | --- |
|  | `all` | Not a true rule! Calls all rules stated above. |

### 2. Configuration
---
Certain rules can be configured by the user, for example the the maximum number of characters permitted per line. 

***Configuration keywords:***

* `columns=<integer>` Max number of characters per line. *Defaults to 80*.
* `max-warnings=<integer>` Max number of warnings before gaplint aborts. *Defaults to 1000*.
* `indentation=<integer>` Indentation of nested statements. *Defaults to 2*.
* `disable=<name/code>, <name/code>, ...` Rules can be suppressed using their name or code. *By default, no rules are suppressed*.

As the user can alter the configuration in various places, a configuration hierarchy is used. A preference given somewhere higher on the hierarchy than another will be given precedence.

***Where to configure gaplint and the configuration hierarchy (from the top down):***


1. *Contents of global variable* `__CONFIG` *in* `gaplint.py`:
    These preferences will be applied to all documents linted until they are again altered.

    ```python
    __CONFIG = {} # this is the user configuration dictionary
    ```
    
    For example, if we want 100 characters per line instead of the default 80, an indentation of 4 spaces instead of the default 2, and to supress rules concerning consecutive empty lines and unused local variables, we add to `__CONFIG` as follows:
    
    ```python
    __CONFIG = {'columns': 100, 'indentation': 4, 'disable': ['W002', 'W028']}
    ```
    Note we could also have disabled the rules by name.

2. *Configuration options entered via the command line when running gaplint:*
    These preferences will be applied for a single run of gaplint only (though multiple files may be linted in this run). To configure gaplint to be run on file1, file 2, ..., with preferences as in the example above, we enter the following into the command line:

    ```
    $ python ./gaplint.py --columns=100 --indentation=4 --disable='W002, W028' <file1.g_path> <file2.g_path> ...
    ``` 
    Note if only one rule is being disable, the quotes are not required.
    
3. *Preferences in configuration script* `.gaplint.yml`:
    These preferences are applied until they are again adjusted and saved. Below is the contents of the config script with no user values given. In this case default values are used.

    ```yaml
    columns:
    max-warnings: 
    indentation:
    disable:
    ```
    
    To configure gaplint as in the above example, .gaplint.yml should be modified in the following way and saved:
    
    ```yaml
    columns: 100
    max_warnings:
    indentation: 4
    disable:
    - W002
    - W028
    ```

4. *File/line rule suppressions in user's GAP file (see Disabling Rules for a Line or File*).

5. *Default configuration (no user action required)*

### 3. Disabling Rules for a Line or File
---
Any of the rules in the tables above, including `all`, can be suppressed for a specific line or for a whole file:

* To supress a rule(s) for a given line, include the following after the line of code for which the rule is to be suppressed:

    ```
    # gaplint: disable=<name_or_code>, <name_or_code> ...
    ```
    
* If the above is too long to fit after the relevant line of code, suppressions can be declared in the line above for the line below by including `(nextline)`:

    ```
    # gaplint: disable(nextline)=<name_or_code>, <name_or_code>, ...
    ```
* If rules have been suppressed for a given line using both the in-line and *nextline* options, the union of the two rule sets given for suppression will be disabled for the line.

* To suppress rules for a whole file the following must be included before any code is written (i.e. either as the first line of a GAP file, or preceded by any combination of only whitespace, empty lines and comments):

    ```
    # gaplint: disable=<name_or_code>, <name_or_code>, ...
    ```
