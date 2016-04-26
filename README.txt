README
======

Follow the steps below to setup the env for ACI Webkit:
-   Apache web server
-   Cgi
-   Acitoolkit and cobra (need match apic)
-   And several python package/module (refer to the python script)
-   Setup the directories and copy files to match the tree view below
    / 
    ├───usr
    │   └───lib
    │       └───cgi-bin
    │               aci_webkit.py
    │               
    └───var
        └───www
            └───html
                │   aci_webkit.html
                │   favicon.png
                │   index.html
                │   
                ├───src
                │       bootstrap-duallistbox.css
                │       bs3_submenu.css
                │       dataTables.bootstrap.css
                │       jquery.bootstrap-duallistbox.js
                │       style.min.css
                │       
                └───tmp


copy cgi-bin/aci_webkit.py /usr/lib/cgi-bin/
chmod +x /usr/lib/cgi-bin/aci_webkit.py 

a2enmod cgi 
service apache2 restart 

cp -r html/* /var/www/html 
chown -R www-data:www-data /var/www/html/tmp 

download acicobra and acimodel - ACI SDK 
http://{apic_hosts}//cobra/_downloads 
install SDK acicobra_xxx.egg first 
easy_install acicobra_xxx.egg 
easy_install acimodel_xxx.egg 


