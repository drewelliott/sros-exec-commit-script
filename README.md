# Nokia SROS Commit Script
### While Nokia SROS does not have a specific application called "commit script" as you may have used in other NOS, there is a way we can utilize existing onbox tools that will allow us to create a similar function.

### We will be combining a `cli-alias` with an `exec` script. The exec script will be calling a python script which gives us a great deal of flexibility to accomplish whatever we need to do.

### Pysros has all of the tools needed to interact with the commit API and will use whatever configuration mode the user is already in (exclusing/global/private).



## For this script, we will be validating the following conditions each time there is a commit:

**Logging**
- check each installed CPM for a CF
    - if CF is absent, generate error message
- all logging must be set to a CF that is present and not to cf3:
    - if logging is set to cf3: or a missing CF, generate an error message and block commit


## Router configuration

The router configuration is very simple.

We will be creating an `exec` script, then calling it with a `command-alias` that we can name ourselves. In this case, I am calling it `commit-script`

```
*[gl:/configure system management-interface cli md-cli environment command-alias]
A:admin@r1# info
    alias "commit-script" {
        admin-state enable
        description "Commit script example"
        cli-command "exec \"commit-script\""
        mount-point global { }
    }
```

## Exec script

> The reason an `exec` script is required, is because configuration candidates are unique per session. When a `python` script is run, a new session is created. Using an `exec` script can be thought of as behaving as if two users were concurrently making the same changes.

The `exec` script will get a copy of the entire candidate and pipe it into the `stdin` of the `pysros` script. At this point, the `pysros` will use the configuration that has all of the changes and it will be able to perform the required logic and then take the appropriate actions based on the results (commit/discard/log/warn/etc...)

```
info json full-context / | pyexec cf3:/myscript.py
```

## Python Script

First, there is a framework that we need to have in place before adding any of our own logic. This is required to be able to handle the configuration appropriately.

```
from pysros.management import connect
import sys
import json

c=connect()

def parse_config():
    config=[]
    for line in sys.stdin:
        config.append(line)
    _config = "".join(str(e) for e in config)
    pysros_config = c.convert('/', _config, source_format='json', destination_format='pysros')
    return pysros_config

### write your code using the pysros_config as the candidate to validate
```
### Caveats

There are caveats to consider for this `commit-script` workaround:

1) It is highly recommended to always use `configure private` with this approach. *if `configure global` is used, it could cause confusion if the user does not manually run `discard` after the configuration because leftover configurations will remain*

3) The users need to run the cli-alias instead of the built-in `commit` keyword. 

4) This approach does not work with `configure exclusive` mode.

## Additional Ideas

Here are some additional ideas that could be use-cases for commit script validations

**Interface Naming**
- interface naming for lags is set to "lagX" where "X" is a number between 1-64
    - if name does not comply to this standard, generate an error message and block commit

**Service MTU**
- service MTU is set to 9114
    - if MTU is set to something other than 9114, generate an error message and allow commit

**Routing Protocols**
- if bgp/ospf/isis already present in the configuration, no changes are allowed, but if not present, allow commit

**SAA Tests**
- check for running saa tests, generate an error message if there are more than 8 continuous tests running, allow commit

**QoS Policy**
- check that a qos policy is applied to each service
    - if qos policy is missing, generate error and block commit

**CPM and MAF Filters**
- check that cpm and maf filters are applied and enabled
    - if they are missing or disabled, generate an error message and block commit
    - there are occasions when an engineer would need to disable these for troubleshooting purposes, so this will be its own script that can be disabled separately.
