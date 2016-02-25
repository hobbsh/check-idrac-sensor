#!/usr/bin/env python

import subprocess
import sys
import argparse
import re
import json
import time

def build_parser():
    parser = argparse.ArgumentParser(description='Check iDRAC Sensors')
    parser.add_argument('-H', '--host', required=True, type=str, dest='host')
    #racadm authentication - username/password or authfile. If authfile is specified, it takes precedence
    parser.add_argument('-u', '--username', required=True, type=str, dest='username')
    parser.add_argument('-p', '--password', required=True, type=str, dest='password')
    parser.add_argument('-a', '--authfile', required=False, type=str, dest='authfile')
    #Root racadm command - currently only getsensorinfo is supported
    parser.add_argument('-C', '--command', required=True, type=str, dest='cmd', default="getsensorinfo")
    #Include perfdata in output? True or False
    parser.add_argument('-f', '--perfdata', required=False, type=bool, dest='perfdata', default=False)
    # Use 'all' to return data for all sensor types at once
    # Valid sensor types: battery, current, intrusion, memory, performance, processor, redundancy, sd_card, voltage
    parser.add_argument('-s', '--sensortype', required=False, type=str, dest='sensor', default="all")
    parser.add_argument('-d', '--debug', required=False, type=bool, dest='debug', default=False)

    return parser

def main():
    global debug

    debug = args.debug

    if not racadm_exists():
	print "ERROR: 'racadm' not found. If it's installed, try a symlink to /sbin:\nln -s /opt/dell/srvadmin/sbin/racadm /sbin/racadm\n"
	sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    if validate_arguments(args):
	host = args.host
        user = args.username
        password = args.password.strip("'").replace('\\', '')

	perfdata = args.perfdata
        command = args.cmd
        sensor = args.sensor
	start = time.time()
	sensor_data = query_idrac(host, user, password, command)

	if debug:
	    print sensor_data

	if sensor_data:
	    parsed = sections_to_dict(sensor_data)

	    if debug:
	        print json.dumps(parsed, sort_keys=True, indent=4)
	    
	    print "Nagios: ", nagios_output(parsed, sensor, perfdata)
	else:
	    print "No response from iDRAC!"
    else:
        print "ERROR: Invalid command or sensortype. Please check that command or sensortype is valid. Exiting...\n"
        sys.exit(1)

	
def clean_lines(data):
    cleaned = []
    for line in data:
	if line:
	    cleaned.append(line)

    return cleaned
    
def clean_headings(data):
    cleaned = []
    for line in data:
	if line.strip():
	    l = line.replace('<','').strip()
	    cleaned.append(l.lower())

    return cleaned

def clean_top_section(section):
    lines = ''
    data = section.split('\r\n')
    for line in data:
	if line:
	    line = re.sub('\[.+?\]', '', line)
	    lines += line+'\r\n'

    return lines

def format_sensor(sensor):
    return sensor.strip().lower().replace(' ', '_')

def set_sensor_info(lines):
    try:
	sensor = format_sensor(lines[0].split(':')[1])
	headings = clean_headings(lines[1].split('>'))
    except:
	sensor = format_sensor(lines[1].split(':')[1])
	headings = clean_headings(lines[2].split('>'))

    return sensor, headings

def sections_to_dict(sensor_data):
    '''Parse sensor info sections into multi-dimensional dict'''
    organized = dict()
    #Sections are separated on double return/newline, so split that way
    all_sections = sensor_data.split('\r\n\r\n')

    main_sections = all_sections[1:]
    top_section = clean_top_section(all_sections[0].split('\r\r\n')[1])
    main_sections.append(top_section)
    
    for section in main_sections:
	#Lines separated by return + newline, so split on that
	lines = section.split('\r\n')
	if len(lines) > 0:
	    try:
		#Format headings and pull sensor names
		sensor, headings = set_sensor_info(lines)
	        organized[sensor] = organized.get(sensor, {})
	    except:
		#Section is invalid (usually blank) so skip it
	        continue

	    for line in lines:
	        if 'Sensor Type' not in line and '<' not in line:
		    if line and len(headings) > 0:
			#Split readings into list on multiple spaces as some sensor names have single spaces
			readings = [ s.strip() for s in line.split('  ') if s.strip() ]
			if len(readings) > 0:
			    sensor_name = readings[0].replace(' ', '_').lower()

		        i = 0
			parsed = {}
		        for reading in readings:
			    #Append formatted readings to sensor type dict
			    sensor_type = headings[i]
			    if reading and i > 0:
		                reading = re.sub('[\s+]', '', reading)
				if sensor in ['fan', 'temperature']:
				    reading = re.sub("[^0-9]", "", reading)

			        parsed[sensor_type] = reading

			    i += 1

			if parsed:
			    #Append parsed section to multidimensional dict 'organized'
			    organized[sensor][sensor_name] = parsed

    return organized

def nagios_output(sensor_data, sensor, perfdata):
    '''provide Nagios output for check results'''
    output = ''
    if sensor == 'all':
	for s, desc in sensor_data.iteritems():
	    for k,v in desc.iteritems():
		if v['status'] and v['status'] is not 'N\A':
	            status = v['status'].upper()
	            output += "%s - %s;" % (k, status)
    else:
	status = sensor_data[sensor]['status'].upper()
	
	#Nagios STDOUT format
	output = "%s - %s;" % (sensor, status)

	if perfdata:
	    output += "| %s" % (status)

    return output
    
def compile_sensordata(sensor_data, sensor):
    status = ''
    for s, subs in sensor_data.iteritems():
	print s	

def validate_arguments(args):
    '''make sure command is valid'''

    validate = [ args.cmd, args.sensor ]

    valid_commands = ['getsensorinfo', 'raid']
    valid_sensortypes = ['battery', 'current', 'intrusion', 'memory', 'performance', 'processor', 'redundancy', 'sd_card', 'voltage', 'all']

    validated = {}
    for option in validate:    
        if option in valid_commands:
	    validated[option] = True
	elif option in valid_sensortypes:
	    validated[option] = True

    if any(a == False for a in validated.values()):
	return False
    else:
	return True

def clean_bracket_content(data):
    return re.sub("\[.*?\]", '', data)

def query_idrac(host, user, password, command):
    '''query iDRAC''' 
    command = "racadm -r %s -u %s -p %s %s" % (host, user, password, command)
    rcode, output, error = exec_command(command)

    if rcode and error:
        print "ERROR: encountered a problem running racadm command" + str(error) + "\n"
    else:
	return output

def racadm_exists():
    rcode, output, error = exec_command('which racadm')
    if rcode is 0 and output != '':
	return True
    else:
	return False

def exec_command(command):
    """Execute command.
       Return a tuple: returncode, output and error message(None if no error).
    """
    sub_p = subprocess.Popen(command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    output, err_msg = sub_p.communicate()
    return (sub_p.returncode, output, err_msg)


if __name__ == "__main__":
    main()
    sys.exit(0)
