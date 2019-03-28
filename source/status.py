#! /usr/bin/env python3

# Build a testing status web page. Based on
# What functions exist in R folder
# what test files exist in the testhtat folder
# output of devtools::test()

# Currently trying the junit output of devtools::test as I think that is more
# parseable

# options(testthat.output_file = "somefile")
# devtools::test('/home/vagrant/dsdev/dsbetatestclient', reporter = "junit")


import glob
import os.path
import xml.etree.ElementTree as ET

local_root_path = "/home/olly/git/"
remote_root_path = "http://github.com/datashield/"
repo_name = "dsBetaTestClient"
output_file_name = "status.html"
# devtools_test_output_file = "logs/Job/6_Devtools tests.txt"
devtools_test_output_file = "output"

local_repo_path = local_root_path + repo_name
remote_repo_path = remote_root_path + repo_name


# Check repo exists

################################################################################
# Get list of functions from R folder
ds_functions_path = glob.glob(local_repo_path + "/R/*.R")

ds_functions = []
for this_path in ds_functions_path:
    ds_functions.append(os.path.basename(this_path))

ds_functions.sort()


for this_function in ds_functions:
    print(this_function)


################################################################################
# Get the list of tests
ds_tests_path = glob.glob(local_repo_path + "/tests/testthat/*.R")

ds_tests = []
for this_test in ds_tests_path:
    ds_tests.append(os.path.basename(this_test))

# Drop the before and after scripts
ds_tests.remove('setup.R')
ds_tests.remove('teardown.R')

ds_tests.sort()

################################################################################
# Parse the devtools::tests() log file, this is the output of the testthat tests
#devtools_h = open(devtools_test_output_file, "r")
#devtools_results = devtools_h.read()
#print(devtools_results)

print("XML!!!")

tree = ET.parse(devtools_test_output_file)
root= tree.getroot()

print(root.tag)

# Define status dictionary and assign zeros for each test (NOTE: this is like ds.cov.R)
ds_test_status = {}
for this_test in ds_tests:
    ds_test_status[this_test] = {'number':0, 'errors':0}

# Cycle through the xml line by line. This will have data for ALL tests.
for child in root:
    print(child.attrib['name'], child.attrib['tests'], child.attrib['errors'])

    # Look to see if this test has a match in the existing list of tests
    for this_test in ds_tests:
        #print(this_test[5:-2])
        # Dont need the 'test-' and the '.R' bit of the test name
        if this_test[5:-2] in child.attrib['name']:
            ds_test_status[this_test]['number'] = int(ds_test_status[this_test]['number']) +int(child.attrib['tests'])
            ds_test_status[this_test]['errors'] = int(ds_test_status[this_test]['errors']) +int(child.attrib['errors'])

print(ds_test_status)


################################################################################
#Make some html
h = open(output_file_name, "w")
h.write('<!DOCTYPE html>\n<html>\n<head>\n<link rel="stylesheet" href="status.css">\n</head>\n<body>')

h.write("<h2>" + repo_name + "</h2>")

h.write("<table border=1>")
h.write("<tr><th>Function name</th><th>Test file exist</th><th>Number of tests</th><th>Test pass</th></tr>")
for this_function in ds_functions:
    h.write("<tr>")
    h.write("<td><a href=" + remote_repo_path + "/R/" + this_function + ">" + this_function + "</td>")

    # See if test exists
    expected_test_name = "test-"+this_function
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good">Y</td>')
    else:
        h.write("<td></td>")

    # See how many tests exist
    try:
        h.write("<td>" + str(ds_test_status[expected_test_name]['number']) + "</td>")
    except:
        h.write("<td></td>")

    # See how many tests fail
    try:
        h.write("<td>" + str(ds_test_status[expected_test_name]['errors']) + "</td>")
    except:
        h.write("<td></td>")


    h.write("</tr>\n")
h.write("</table>\n</body>\n</html>")
