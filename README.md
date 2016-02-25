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
```
./check-idrac-sensor.py -H 10.201.214.139 -u root -p calvin

usage: check-idrac-sensor.py [-h] -H HOST -u USERNAME -p PASSWORD
                             [-a AUTHFILE] [-C CMD] [-f PERFDATA] [-s SENSOR]
                             [-d DEBUG]
```

#TODO
-Perfdata for certain sensortypes
