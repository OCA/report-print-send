Requirements:

#. Computer serving as print server:

   * Where the PrintNode client can be installed
   * Where the printer to be shared is connected and accessible.
   * Have internet access

#. Printer to share
#. Account registered at https://www.printnode.com/

Brefore configure this module, you need to:

#. Get an API Key from PrintNode:

   #. After creating an account on Printnode go to https://app.printnode.com/app/apikeys (enter the account password if is requested)
   #. Enter some description in the "API Key Description" text box like "Odoo" and hit the "CREATE" button.
   #. Copy the generated API key. We will need this below.

#. Installing the PrintNode Client on the print server:

   * Guide for windows users https://www.printnode.com/en/docs/installation
   * Guide for windows macOS / OS X
   * Guide for Linux (Ubuntu):

      #. Download Cliet binary

         * Go to https://app.printnode.com/app/downloads
         * Login
         * Download the correct version acording your SO and architecture. For example for Ubuntu 20.04 TLS x64, download PrintNode-4.24.1-ubuntu-20.04-x86_64.tar.gz
      #. Install (With UI)

         * uncompress the downloaded file on the directory /usr/local/PrintNode
         * go to /usr/local/PrintNode directory and execute the instalator ./PrintNode
      #. Install (Console)

         Assuming the file was downloaded in ~/Downloads

         .. code-block:: bash

            tar xf PrintNode-4.24.1-ubuntu-20.04-x86_64.tar.gz

            sudo mv PrintNode-4.24.1-ubuntu-20.04-x86_64 /usr/local/PrintNode

            cd /usr/local/PrintNode

            ./PrintNode --headless --web-interface --web-interface-shutdown --shutdown-on-sigint

         Now you can go to http://localhost:8888/ to configure the client. You can also access here (using the computer's IP instead of localhost) from the lan network (you may need to open port 8888 in the firewall)

#. Configuring the client.

   * On the web client (or UI) login with your acccount
   * Go to "Printers" tab
   * The printers installed in the system should appear under this section. With this, your printers will be synchronized with PrintNode

#. Install Client as service

   .. code-block:: bash

      cd /usr/local/PrintNode

      sudo cp init.sh /etc/init.d/PrintNode

      sudo update-rc.d PrintNode defaults

      sudo systemctl daemon-reload

      sudo /etc/init.d/PrintNode start

   (Optional or for advanced users) You can edit "init.sh" file to modify the user with which this client runs, by default it is done as root.

#. Testing installation

   * go to https://app.printnode.com/app/print (and login)
   * go in the menu to the option "Print Something"
   * select:

      * Source: “PrintNode Test Page”
      * Printer: name of configurated printer
      * Test File: “test.pdf”
   * and now hit on "PRINT" button

#. Odoo configuration

   #. First you need link Print Node with odoo

      * go to settings / general options
      * on "integrations" secction enter the API Key under the label "Print Node Api Key"

   #. Printer Configuring

      * go to settings / printing
      * hit on "sync printers from cups" and next on "OK"
      * after that you can see the printers on list
      * open the new printer and mark it as the default printer.
