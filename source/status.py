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
__date__ = 4/6/19

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
# <function name>()::<test type>::<Optional other info>
# ds.asFactor.o::smoke
for child in root:
    print('\n', child.attrib['name'], child.attrib['tests'], child.attrib['errors'])

    context = child.attrib['name']
    context = context.replace('dsBetaTestClient::','')        # Drop dsBetaTestClient:: from context. Factor this out of real code.
    #re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", temp_name)   # Drop brackets and contents

    print(context)

    # Split by :: delimiter
    context_parts = context.split('::')

    try:
        function_name = context_parts[0]
        function_name = function_name.replace('()','') # Drop the brackets from the function name
        test_type = context_parts[1]
        print(function_name)
        print(test_type)
    except:
        pass

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
h.write("<tr><th>Function name</th><th>Smoke test<br/>file exist</th><th>Test file exist</th><th>Smoke test<br/>pass rate</th><th>Functional<br/>pass rate</th><th>Mathematical<br/>pass rate</th></tr>")

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


    ####################
    # Other tests
    # See if test exists
    expected_test_name = "test-"+this_function
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '">' + expected_test_name + '</a></td>')
    else:
        h.write("<td></td>")


    ###################
    # Work out the pass rate
    try:
        this_error = int(ds_test_status[this_function]['smoke']['errors'])
        this_number = int(ds_test_status[this_function]['smoke']['number'])

        if this_error == 0:
            h.write("<td>" + str(this_number) + "/" + str(this_number) + "</td>")
        elif this_error > 0:
            h.write("<td>" + str(this_number - this_error) + "/" + str(this_number) + "</td>")
    except:
        h.write("<td></td>")



    h.write("<td></td>")
    h.write("<td></td>")



    h.write("</tr>\n")
h.write("</table>\n</body>\n</html>")
