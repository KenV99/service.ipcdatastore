*****************
script.module.ipc
*****************

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
    <import addon="script.module.ipc" version="0.0.2" />
  </requires>

pyro4 should be imported simply as `import pyro4`

There are two modules in the ipc directory. These are included to set up a simple server or client using a specified
host and port. Pyro4 contains the libraries needed to use a nameserver and random ports, but for simplicity sake these
helper classes do not utilize a nameserver. They are meant to be imported as:

::

    from ipcserver import IPCServer
    from ipcclient import IPCClient

or however you wish. Objects can be shared from the server using the default configuration (see below) simply as:

::

    from ipc.ipcserver import IPCServer

    # see notes about the following 3 lines
    path_to_shared_obj = os.path.join(xbmcaddon.Addon('addon where the obj is').getAddonInfo('path'), 'resources', 'lib')
    if path_to_shared_obj not in sys.path:
        sys.path.insert(0, path_to_shared_obj)

    import MyObjectToBeShared

    obj = MyObjectToBeShared()
    myserver = IPCServer(expose_obj=obj)
    myserver.start()


These can be then used on the client, again using the default configuration as:

::

    from ipc.ipcclient import IPCClient

    # see notes about the following 3 lines
    path_to_shared_obj = os.path.join(xbmcaddon.Addon('addon where the obj is').getAddonInfo('path'), 'resources', 'lib')
    if path_to_shared_obj not in sys.path:
        sys.path.insert(0, path_to_shared_obj)

    myclient = IPCClient()
    obj = myclient.get_exposed_object()
    myvalue = obj.mymethod()

.. warning::

    The path to the exposed object **must** be in the PYTHONPATH in both circumstances even though it is
    not required that you import it on the client. During instantiation, the class definition is needed to expose the
    methods and attributes of the original object remotely. If you are using the client on a separate machine, an exact
    copy of the module containing the definition needs to be made available.

The above examples do not provide for any exception handling. For a more detailed example with handling of both
client side and server side errors, see:.

.. index:: Classes and methods

==========================================
Classes and methods from script.module.ipc
==========================================

.. automodule:: ipcserver
    :members:

.. automodule:: ipcclient
    :members:

.. index:: example usage

=======================================
Example usage of ipcserver and ipclient
=======================================