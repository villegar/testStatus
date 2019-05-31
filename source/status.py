#! /usr/bin/env python3

# Build a testing status web page. Based on
# What functions exist in R folder
# what test files exist in the testhtat folder
# output of devtools::test()

# Currently trying the junit output of devtools::test as I think that is more
# parseable

# options(testthat.output_file = "somefile")
# devtools::test('/home/vagrant/dsdev/dsbetatestclient', reporter = "junit")

# To do:
# - pass in repo and branch name as arguements


import glob
import pprint
import re
import os.path
import xml.etree.ElementTree as ET

__author__ = "Olly Butters"
__date__ = 31/5/19

# local_root_path = "./"
local_root_path = "/home/olly/git/"
remote_root_path = "http://github.com/datashield/"
repo_name = "dsBetaTestClient"
branch_name = "master"
output_file_name = "status.html"
devtools_test_output_file = "../logs/test_results.xml"
# devtools_test_output_file = "test_results.xml"


pp = pprint.PrettyPrinter(indent=4)

local_repo_path = local_root_path + repo_name
remote_repo_path = remote_root_path + repo_name

# Check repo exists
print("local repo path: " + local_repo_path)
print("remote repo path: " + remote_repo_path)




################################################################################
# Get list of functions from R folder
#
print("\n\n##########")
ds_functions_path = glob.glob(local_repo_path + "/R/*.R")

print("Number of local functions found: " + str(len(ds_functions_path)))

ds_functions = []
for this_path in ds_functions_path:
    ds_functions.append(os.path.basename(this_path))

ds_functions.sort()


for this_function in ds_functions:
    print(this_function)


# Make the test status dictionary
ds_test_status = {}
for this_function in ds_functions:
    # Drop the .R part from the end.
    this_function = this_function.replace('.R', '')
    ds_test_status[this_function] = {}



################################################################################
# Get the list of tests
print("\n\n##########")
ds_tests_path = glob.glob(local_repo_path + "/tests/testthat/*.R")

print("Number of local test files found: " + str(len(ds_tests_path)))

ds_tests = []
for this_test in ds_tests_path:
    ds_tests.append(os.path.basename(this_test))

# Drop the before and after scripts
ds_tests.remove('setup.R')
ds_tests.remove('teardown.R')

ds_tests.sort()

for this_test in ds_tests:
    print(this_test)


################################################################################
# Parse the devtools::tests() log file, this is the output of the testthat tests
#devtools_h = open(devtools_test_output_file, "r")
#devtools_results = devtools_h.read()
#print(devtools_results)
print("\n\n##########")

print("Parsing XML!!!")

tree = ET.parse(devtools_test_output_file)
root= tree.getroot()

print(root.tag)

# Define status dictionary and assign zeros for each test (NOTE: this is like ds.cov.R)
# for this_test in ds_tests:
#     ds_test_status[this_test] = {'number':0, 'errors':0}

# Cycle through the xml line by line. This will have data for ALL tests.
# The 'context' in testthat is the 'name' in the xml file.
# The expected format of the context is:
# <function name>::<test type>
# ds.asFactor.o::smoke
for child in root:
    print('\n', child.attrib['name'], child.attrib['tests'], child.attrib['errors'])

    context = child.attrib['name']
    # temp_name = temp_name[18:]   # Drop the dsBetaTestClient:: prefix
    context = context.replace('dsBetaTestClient::','')
    #re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", temp_name)   # Drop brackets and contents

    print(context)

    # Just pasrsing contexts with (): as a delimiter. NEEDS UPDATING WHEN TESTS CHANGED.
    context_parts = context.split('():')

    try:
        function_name = context_parts[0]
        test_type = context_parts[1]
        print(function_name)
        print(test_type)
    except:
        pass

    # Look to see if this test has a match in the existing list of tests
    #for this_test in ds_tests:
        # Dont need the 'test-' and the '.R' bit of the test name
    #    if this_test[5:-2] in child.attrib['name']:
    #        ds_test_status[this_test]['number'] = int(ds_test_status[this_test]['number']) +int(child.attrib['tests'])
    #        ds_test_status[this_test]['errors'] = int(ds_test_status[this_test]['errors']) +int(child.attrib['errors'])

    # Build the dictionary ds_test_status[function_name][test_type]{number, error}
    try:
        ds_test_status[function_name][test_type] = {}
        ds_test_status[function_name][test_type]['number'] = int(child.attrib['tests'])
        ds_test_status[function_name][test_type]['errors'] = int(child.attrib['errors'])
    except:
        pass

pp.pprint(ds_test_status)


################################################################################
# Make an HTML table of the results.
# Currently hard coding test types, but could automatically pull these out.
print("\n\n##########")

h = open(output_file_name, "w")
h.write('<!DOCTYPE html>\n<html>\n<head>\n<link rel="stylesheet" href="status.css">\n</head>\n<body>')

h.write("<h2>" + repo_name + "</h2>")

h.write("<table border=1>")
h.write("<tr><th>Function name</th><th>Smoke test file exist</th><th>Number</th><th>Errors</th><th>Test file exist</th><th>Number of tests</th><th>Test pass</th></tr>")

for this_function in ds_test_status.keys():
    print('===', this_function)

    # Function name with link to repo
    h.write("<tr>")
    h.write("<td><a href=" + remote_repo_path + "/blob/" + branch_name + "/R/" + this_function + ".R>" + this_function + "</a></td>")

    ####################
    # Smoke test
    # See if test file exists
    expected_test_name = "test-smk-"+this_function+'.R'
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '">' + expected_test_name + '</a></td>')
    else:
        h.write("<td></td>")

    # See how many tests exist
    try:
        h.write("<td>" + str(ds_test_status[this_function]['smoke']['number']) + "</td>")
    except:
        h.write("<td></td>")

    # See how many tests fail
    try:
        h.write("<td>" + str(ds_test_status[this_function]['smoke']['errors']) + "</td>")
    except:
        h.write("<td></td>")


    ####################
    # Other tests
    # See if test exists
    expected_test_name = "test-"+this_function
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '">' + expected_test_name + '</a></td>')
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
