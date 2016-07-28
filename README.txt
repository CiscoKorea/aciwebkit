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

New Deployment with Ansible 

0. install ansible on your desktop(not target vm) with latest version from githbu.com 
  ```
  verify python 2.7.x (latest version) installed 
  git clone https://github.com/ansible/ansible --recursive 
  cd ansible 
  python setup.py install ( you may need sudo)
  ```
1. update target vm(only ubuntu 14.04 support now) ip on hosts file 
2. make account cisco with sudo previledge on target vm 
3. configure PasswordAuthentication yes on /etc/ssh/sshd_config  & restart ssh service with 'sudo service ssh restart'
4. update apic credential on aciwebkit.yml and acitoolkit.yml with your own apic hosts ip, username and password 
5. specifiy apic's version on aciwebkit.yml ( expample 1.3_1i ==> 1.3(1i) on apic web gui)
6.1. run 
  $ansible-playbook aciwebkit.yml -i hosts -u cisco -K -k 
6.2. run 
  $ansible-playbook acitoolkit.yml -i hosts -u cisco -K -k 

Happy Selling ACI with Opensource Power !! 
