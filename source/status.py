#! /usr/bin/env python3

# Build a testing status web page. Based on:
#   1) What functions exist in the R folder of the local repo.
#   2) What test files exist in the testhtat folder in the local repo.
#   3) Output of devtools::test().

# The list of functions in the R folder is the canonical list this script uses.

# Using the junit output of devtools::test
# options(testthat.output_file = "somefile")
# devtools::test('/home/vagrant/dsdev/dsbetatestclient', reporter = "junit")

# Drive everything from the context specified in the testthat scripts.
# The pre-defined format of these is:
# <function name>()::<test type>::<Optional other info>
# someFunction()::smoke::extra information.

# To do:
# - pass in repo and branch name as arguements

import argparse
import datetime
import glob
import os.path
import pprint
import re
import xml.etree.ElementTree as ET

__author__ = "Olly Butters"
__date__ = 7/6/19

# local_root_path = "./"
# local_root_path = "/home/olly/git/"
remote_root_path = "http://github.com/datashield/"
repo_name = "dsBetaTestClient"
branch_name = "master"
# output_file_name = "status.html"
# devtools_test_output_file = "../logs/test_results.xml"
# devtools_test_output_file = "test_results.xml"



parser = argparse.ArgumentParser()
parser.add_argument("log_file_path", help="Path to the log file.")
parser.add_argument("output_file_path", help="Path to the output file.")
parser.add_argument("local_repo_path", help="Path to the locally checked out repository.")
args = parser.parse_args()
devtools_test_output_file = args.log_file_path
output_file_name = args.output_file_path
local_repo_path = args.local_repo_path
# print(devtools_test_output_file)
# exit()

pp = pprint.PrettyPrinter(indent=4)

# local_repo_path = local_root_path + repo_name
remote_repo_path = remote_root_path + repo_name

# Check repo exists
print("local repo path: " + local_repo_path)
print("remote repo path: " + remote_repo_path)




################################################################################
# Get list of functions from R folder in the local repo
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
    this_function = this_function.replace('.R', '')  # Drop the .R part from the end.
    ds_test_status[this_function] = {}



################################################################################
# Get the list of tests from the local repo
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
#
print("\n\n##########")

print("Parsing XML file: " + devtools_test_output_file)

tree = ET.parse(devtools_test_output_file)
root= tree.getroot()

print(root.tag)


log_file = os.path.basename(devtools_test_output_file)
gh_log_url = 'https://github.com/datashield/testStatus/blob/master/logs/' + log_file

# Cycle through the xml line by line. This will have data for ALL tests.
# The 'context' in testthat is the 'name' in the xml file.
# The expected format of the context is:
# <function name>()::<test type>::<Optional other info>
# e.g.
# ds.asFactor.o::smoke
for child in root:
    print('\n', child.attrib['name'], child.attrib['tests'], child.attrib['skipped'], child.attrib['failures'], child.attrib['errors'])

    context = child.attrib['name']
    context = context.replace('dsBetaTestClient::','')        # Drop dsBetaTestClient:: from context. Factor this out of testthat code.

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
        print("ERROR with " + context)
        pass

    # Build the dictionary ds_test_status[function_name][test_type]{number, skipped, failures, errors}
    # This should automatically make an entry for each test type specified in the testthat files.
    try:
        ds_test_status[function_name][test_type] = {}
        ds_test_status[function_name][test_type]['number'] = int(child.attrib['tests'])
        ds_test_status[function_name][test_type]['skipped'] = int(child.attrib['skipped'])
        ds_test_status[function_name][test_type]['failures'] = int(child.attrib['failures'])
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
h.write(str(datetime.datetime.now()))

h.write("<table border=1>")
h.write("<tr><th>Function name</th><th>Coverage</th><th>Smoke test<br/>file exist</th><th>Test file exist</th><th>Smoke test<br/>pass rate</th><th>Functional<br/>pass rate</th><th>Mathematical<br/>pass rate</th></tr>")

for this_function in sorted(ds_test_status.keys()):
    print('===', this_function)

    # Function name with link to repo
    h.write("<tr>")
    h.write('<td><a href="' + remote_repo_path + '/blob/' + branch_name + '/R/' + this_function + '.R" target="_blank">' + this_function + "</a></td>")

    # Coverage columne
    h.write("<td></td>")

    ####################
    # Smoke test
    # See if test file exists
    expected_test_name = "test-smk-"+this_function+'.R'
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '" target="_blank">' + expected_test_name + '</a></td>')
    else:
        h.write("<td></td>")


    ####################
    # Other tests
    # See if test exists
    expected_test_name = "test-"+this_function+'.R'
    print(expected_test_name)
    if expected_test_name in ds_tests:
        h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '">' + expected_test_name + '</a></td>')
    else:
        h.write("<td></td>")


    ###################
    # Work out the pass rate
    try:
        this_skipped = int(ds_test_status[this_function]['smoke']['skipped'])
        this_failures = int(ds_test_status[this_function]['smoke']['failures'])
        this_errors = int(ds_test_status[this_function]['smoke']['errors'])
        this_number = int(ds_test_status[this_function]['smoke']['number'])

        this_problems = this_skipped + this_failures + this_errors

        if this_problems == 0:
            h.write('<td class="good"><a href ="' + gh_log_url + '">' + str(this_number) + "/" + str(this_number) + "</a></td>")
        elif this_error > 0:
            h.write('<td class="bad">' + str(this_number - this_problems) + "/" + str(this_number) + "</td>")
    except:
        h.write("<td></td>")



    h.write("<td></td>")
    h.write("<td></td>")



    h.write("</tr>\n")
h.write("</table>\n</body>\n</html>")
