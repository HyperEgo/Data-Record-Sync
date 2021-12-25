Role Name
=========
firewalld_rules
This role starts and enables firewalld.
It adds IP4 and IP6 rules to allow all inbound traffic to the public zone (which is the default).
This role will be updated at a later date to only allow authorized ports and services.

Check Firewalld settings:
systemctl list-unit-files | grep firewall
firewall-cmd --state
firewall-cmd --list-all

Requirements
------------


Role Variables
--------------


Dependencies
------------


Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: localhost
      roles:
         - firewalld_rules

License
-------

IBCS OS Engineering

Author Information
------------------
Date		Dev		Jira#		Comment
12/2/2020	kpatrick	IBCS-8563	Initial Release
1/21/2021	kpatrick	IBCS-9857	Update to IP6 rule

Verification:
firewall-cmd --list-all
