***********************
Background and Features
***********************

.. index:: background

The addon **service.ipcdatastore** utilizes the module (**script.module.ipc**) to create
a datastore that may be used *to transfer objects/data between different python processes*. This serves 1) to
demonstrate how **script.module.ipc** can be used and 2) to provide a working server that can be used without
further modification to share data amongst Kodi python addons.

*Background:* Moving data between python processes is somewhat difficult in Kodi. Thankfully, there are relatively
few situations where this is needed. Examples of these are:

    1)  A background service needs to provide data to a plugin script invoked by the user. This can be preferable
        in situations where the data gathered by the service is via relatively slow channels (external http scraping)
        and there is an unacceptable delay when the script is invoked.
    #)  A script is invoked by RunScript in keyboard.xml or settings.xml in order to implement a hotkey or make
        make other changes and these changes need to be communicated to a background service.
    #)  The same I/O bound data is required by several different processes and it would be more economical to have
        it gathered only once and then retrieved by all.

There are a number of possible ways this type of data sharing may be implemented in Python. Some of these include:

    1) Saving data to a file which can then be read back in from another process
    #) Saving data to a hidden field in on addon's settings.xml which is read by another
    #) Using shared memory space with mmap
    #) Using sockets to move data with a simple python dict for volatile data or a sql based backend for storage.

The module **script.module.ipc** contains **Pyro4** packaged for Kodi. Pyro4 stands for Python Remote Objects. The
author of this package is Irmen de Jong and the original package and it's documentation can be found
at: https://pythonhosted.org/Pyro4/ Pyro4 is coded entirely in Python, making it suitable for potential inclusion in
the official Kodi repo.

In brief, Pyro4 provides a socket interface and a serializer to allow interprocess communication. Using these, objects
may be moved between processes. How complex these objects are is dependent on the serializer. In the implementation
provided, *pickle* is used as the default serializer. The main drawback to pickle is that there are security issues,
however in the vast majority of situations, this will be used exclusively on one machine and these security concerns
are moot as long as the external firewall keeps the port(s) used from being exposed. On the plus side, of the available
serializers, pickle is compatible with more complex object types and is the best performing.

The addon directory for **script.module.ipc** contains a lib folder with a directory for Pyro4 (made lower case for
official repo compatibility) and a module directory called *ipc* which contains two lightweight classes that can
be imported to use pyro4 with a specified port to share and access objects. The details of these two lightweight
classes and coding examples can be found :ref:`here <script.module.ipc>`.

.. index:: features

Features of service.ipcdatastore
--------------------------------
- Share data (objects) with minimal additional coding
- Optionally start the server with Kodi
- Configurable host and port
- Utilizes a combined server/client caching mechanism for improved performance
- Tests run at the time of startup and additional tests via the settings page
- Optionally automatically place video info on the server each time a file or stream plays

