.. _script.module.ipc:

*****************
script.module.ipc
*****************

????

.. highlight:: python
   :linenothreshold: 6

This addon module's only purpose is to make the contained libraries available to other addons. If you are using
**service.ipcdatastore** this is a required module for that to run. However, others may want utilize these directly
in their own addon's module as an import.

The lib folder for this module contains two folders:

    1) pyro4
    #) ipc

If the script.module.ipc directory is in Kodi's addon directory, the included addon.xml *should* make the contents
available to other addons as long as script.module.ipc is included in the *other* addon's addon.xml under the 'requires'
tag:

::

  <requires>
    <import addon="xbmc.python" version="2.1.0"/>
    ...
    <import addon="script.module.ipc" version="0.1.0" />
  </requires>

pyro4 should be imported simply as ``import pyro4``

There are two modules in the ipc directory. These are included to set up a simple server or client using a specified
host and port. Pyro4 contains the libraries needed to use a nameserver and random ports, but for simplicity sake these
helper classes do not utilize a nameserver. They are meant to be imported as:

::

    from ipc.ipcserver import IPCServer
    from ipc.ipcclient import IPCClient

or however you wish. Objects can be shared from the server using the default configuration as simply as:
(see below for details of the default configuration)

::

    import os
    import sys
    import xbmc, xbmcaddon
    from ipc.ipcserver import IPCServer

    # see the note below about the following 3 lines
    path_to_shared_obj = os.path.join(xbmcaddon.Addon('insert addon name here').getAddonInfo('path'),
                         'resources', 'lib')
    if path_to_shared_obj not in sys.path:
        sys.path.insert(0, path_to_shared_obj)

    import MyObjectToBeShared

    obj = MyObjectToBeShared()
    myserver = IPCServer(expose_obj=obj)
    myserver.start()
    while not xbmc.abortRequested:
        xbmc.sleep(1000)
    myserver.stop()

.. note::

    When starting the server, the module that contains the object to be shared is imported. To prevent potential issues
    with the way the server then accesses that object, I highly recommend that the path to the exposed object be placed
    in the PYTHONPATH by using sys.path as shown.

.. warning::

    Under rare circumstances, if Kodi exits erroneously without getting to line 18, the Kodi process may remain running
    despite the GUI being gone. If this occurs, Kodi may not be able to restart until the process is killed manually.

Once the server is running, the shared object can be used on the client, again using the default configuration as
an example:

::

    from ipc.ipcclient import IPCClient

    myclient = IPCClient()
    obj = myclient.get_exposed_object()
    myvalue = obj.mymethod()

As can be seen in the example above, for the client, it not necessary to import the class of the exposed object.
However, during initial development, it is recommended that the actual class is imported and instantiated instead of
using ``obj = myclient.get_exposed_object()``
until you are sure that everything is working correctly with that object and then switching over to using the server
version.

The above examples do not provide for any exception handling. For a more detailed example with handling of both
client side and server side errors, see the actual python file for: :class:`ipcclientx.IPCClientX`.

.. index:: Classes and methods

????

================================================
Classes and class methods from script.module.ipc
================================================

.. automodule:: ipcserver
    :members:
    :show-inheritance:

.. automodule:: ipcclient
    :members:

