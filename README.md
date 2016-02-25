# check-idrac-sensor
Nagios check script utilizing racadm to check getsensorinfo endpoint

##Purpose:
This check script uses racadm to check sensorinfo output from a Dell iDRAC

##Requirements
This check script requires the racadm tool. To install it:
```
wget -q -O - http://linux.dell.com/repo/hardware/latest/bootstrap.cgi | bash
```
```
sudo apt-get update
sudo apt-get install srvadmin-idrac7
```
OR
```
sudo yum install srvadmin-idrac7
```

##Installation
Clone the repo and move the check-idrac-sensor.py script to your Nagios plugin directory

##Usage:
Below is the minimal usage. The default command (-C) is "getsensorinfo" and default sensors (-s) are "all". Perfdata does not yet return anything and authfile feature is not yet implemented. 
```
./check-idrac-sensor.py -H 192.168.1.120 -u root -p calvin

usage: check-idrac-sensor.py [-h] -H HOST -u USERNAME -p PASSWORD
                             [-a AUTHFILE] [-C CMD] [-f PERFDATA] [-s SENSOR]
                             [-d DEBUG]
```

##Bugs
-If you encounter a problem, please open an issue and I will do my best to help

##Known Issues/Compatibility
-Sometimes racadm responds with bad username/password when it is really a response issue with the device. Common on older firmware versions. 
-This has only been tested on iDRAC7
-Authfile and perfdata are options but not yet implemented

##TODO
-Perfdata for certain sensortypes
-Handle some of the failure cases better
-Implement single/multi sensor return (as opposed to just 'all')
