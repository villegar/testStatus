#!/usr/bin/env python3

# Build a testing status web page. Based on:
#   1) The functions that exist in the R folder of the local repo.
#   2) The test files that exist in the testhtat folder in the local repo.
#   3) Output of devtools::test().
#   4) Output of covr::package_coverage()

# The list of functions in the R folder is the canonical list this script uses.

# Using the junit output of devtools::test
# options(testthat.output_file = "somefile")
# devtools::test('/home/vagrant/dsdev/dsbetatestclient', reporter = "junit")

# Drive everything from the context specified in the testthat scripts.
# The pre-defined format of these is:
# <function name>()::<test type>::<Optional other info>::single
# someFunction()::smoke::extra information.

# Assuming the locally checked out repo is the branch that I need.

# To do:
# - pass in repo and branch name as arguements

import argparse
import datetime
import csv
import glob
import os.path
import pprint
import sys
import xml.etree.ElementTree as ET

__author__ = "Olly Butters"
__date__ = 20/11/19


################################################################################
# Build summary table
def build_summary_table(ds_test_status, unique_test_types, pp):
    summary = {}

    pp.pprint(ds_test_status)

    # Initialize as zero
    for this_unique_test_type in unique_test_types:
        summary[this_unique_test_type] = {}
        summary[this_unique_test_type]['pass'] = 0
        summary[this_unique_test_type]['problems'] = 0
        summary[this_unique_test_type]['number'] = 0
        summary[this_unique_test_type]['time'] = 0

    # Totals
    summary['total'] = {}
    summary['total']['pass'] = 0
    summary['total']['problems'] = 0
    summary['total']['number'] = 0
    summary['total']['time'] = 0

    pp.pprint(summary)

    for this_function_name in ds_test_status:
        pp.pprint(this_function_name)
        for this_unique_test_type in unique_test_types:
            try:
                this_skipped = int(ds_test_status[this_function_name][this_unique_test_type]['skipped'])
                this_failures = int(ds_test_status[this_function_name][this_unique_test_type]['failures'])
                this_errors = int(ds_test_status[this_function_name][this_unique_test_type]['errors'])
                this_number = int(ds_test_status[this_function_name][this_unique_test_type]['number'])
                this_time = float(ds_test_status[this_function_name][this_unique_test_type]['time'])

                this_problems = this_skipped + this_failures + this_errors

                summary[this_unique_test_type]['pass'] += (this_number - this_problems)
                summary[this_unique_test_type]['problems'] += this_problems
                summary[this_unique_test_type]['number'] += this_number
                summary[this_unique_test_type]['time'] += this_time

                summary['total']['pass'] += (this_number - this_problems)
                summary['total']['problems'] += this_problems
                summary['total']['number'] += this_number
                summary['total']['time'] += this_time
            except:
                pass

    print("#####################################\nSUMMARY")
    pp.pprint(summary)

    return summary


################################################################################
# Calculate the pass rate of this function and test class, then make a HTML
# table cell out of it. If there are errors put them in the cell.
def calculate_pass_rate(ds_test_status, function_name, test_class, gh_log_url):
    try:
        this_skipped = int(ds_test_status[function_name][test_class]['skipped'])
        this_failures = int(ds_test_status[function_name][test_class]['failures'])
        this_errors = int(ds_test_status[function_name][test_class]['errors'])
        this_number = int(ds_test_status[function_name][test_class]['number'])

        this_problems = this_skipped + this_failures + this_errors

        if this_problems == 0:
            return('<td class="good" style="text-align:center;"><a href ="' + gh_log_url + '" target="_blank">' + str(this_number) + "/" + str(this_number) + "</a></td>")
        elif this_problems > 0:
            return('<td class="bad" style="text-align:center;""><span class="tooltip"><a href ="' + gh_log_url + '" target="_blank">' + str(this_number - this_problems) + "/" + str(this_number) + '</a><span class="tooltiptext">' + '<br/>----------<br/>'.join(map(str, ds_test_status[function_name][test_class]['failureText'])) + '</span></span></td>')
    except:
        return("<td></td>")


################################################################################
# Parse the coverage file, returning a dict of file coverages
def parse_coverage(coverage_file_path):
    coverage = {}
    input_file = csv.reader(open(coverage_file_path))
    # Skip the header
    next(input_file)

    for row in input_file:
        print(row)
        this_function_name = row[0].replace("R/", "")
        this_function_name = this_function_name.replace(".R", "")
        coverage[this_function_name] = round(float(row[1]), 1)

    return coverage


################################################################################
#
def main(args):
    remote_root_path = "http://github.com/datashield/"
    # repo_name = "dsBetaTestClient"
    # branch_name = "master"

    parser = argparse.ArgumentParser()
    parser.add_argument("log_file_path", help="Path to the log file.")
    parser.add_argument("coverage_file_path", help="Path to the coverage file.")
    parser.add_argument("output_file_path", help="Path to the output file.")
    parser.add_argument("local_repo_path", help="Path to the locally checked out repository.")
    parser.add_argument("remote_repo_name", help="Name of the remote repository.")
    parser.add_argument("branch", help="Branch name.")
    args = parser.parse_args()
    devtools_test_output_file = args.log_file_path
    coverage_file_path = args.coverage_file_path
    output_file_name = args.output_file_path
    local_repo_path = args.local_repo_path
    remote_repo_name = args.remote_repo_name
    branch_name = args.branch

    pp = pprint.PrettyPrinter(indent=4)

    remote_repo_path = remote_root_path + remote_repo_name

    log_file = os.path.basename(devtools_test_output_file)
    gh_log_url = 'https://github.com/datashield/testStatus/blob/master/logs/' + remote_repo_name + '/' + branch_name + '/' + log_file

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

        # Differentiate the internal and external functions - makes for prettier sorting later.
        if(this_function.startswith('ds')):
            ds_test_status[this_function]['function_type'] = 'ds'
        else:
            ds_test_status[this_function]['function_type'] = 'internal'

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
    root = tree.getroot()

    print(root.tag)

    # Cycle through the xml line by line. This will have data for ALL tests.
    # The 'context' in testthat is the 'name' in the xml file.
    # The expected format of the context is:
    # <function name>::<maths|expt|smk|args|disc>::<Optional other info>::<single|multiple>
    # e.g.
    # ds.asFactor.o::smoke
    for testsuite in root:
        print('\n', testsuite.attrib['name'], testsuite.attrib['tests'], testsuite.attrib['skipped'], testsuite.attrib['failures'], testsuite.attrib['errors'], testsuite.attrib['time'])

        context = testsuite.attrib['name']
        context = context.replace('dsBetaTestClient::', '')        # Drop dsBetaTestClient:: from context. Factor this out of testthat code.

        # Split by :: delimiter
        context_parts = context.split('::')

        # Function name
        try:
            function_name = context_parts[0]
            function_name = function_name.replace('()', '')  # Drop the brackets from the function name
            print(function_name)
        except:
            print("ERROR: function name not parsable in: " + context)
            pass

        # Test type
        try:
            test_type = context_parts[1]
            print(test_type)
        except:
            print("ERROR: test type not parsable in: " + context)

        try:
            test_type_extra = context_parts[2]
            print(test_type_extra)
        except:
            print("No extra test type.")

        # Build the dictionary ds_test_status[function_name][test_type]{number, skipped, failures, errors, time}
        # This should automatically make an entry for each test type specified in the testthat files.
        try:

            # If this test_type is not defined then initiate it for this function_name
            if test_type not in ds_test_status[function_name]:
                ds_test_status[function_name][test_type] = {}
                ds_test_status[function_name][test_type]['number'] = 0
                ds_test_status[function_name][test_type]['skipped'] = 0
                ds_test_status[function_name][test_type]['failures'] = 0
                ds_test_status[function_name][test_type]['errors'] = 0
                ds_test_status[function_name][test_type]['time'] = 0
                ds_test_status[function_name][test_type]['failureText'] = list()

            ds_test_status[function_name][test_type]['number'] += int(testsuite.attrib['tests'])
            ds_test_status[function_name][test_type]['skipped'] += int(testsuite.attrib['skipped'])
            ds_test_status[function_name][test_type]['failures'] += int(testsuite.attrib['failures'])
            ds_test_status[function_name][test_type]['errors'] += int(testsuite.attrib['errors'])
            ds_test_status[function_name][test_type]['time'] += float(testsuite.attrib['time'])

            # Parse the text from the failure notice into the ds_test_status dictionary
            # if ds_test_status[function_name][test_type]['failures'] > 0:
            if ds_test_status[function_name][test_type]['failures'] > 0 or ds_test_status[function_name][test_type]['errors'] > 0:
                print("\n\nERRORS")
                print(testsuite.tag, testsuite.attrib)
                for testcase in testsuite:
                    print(testcase.tag, testcase.attrib)
                    for failure in testcase:
                        try:
                            print(failure.tag, failure.attrib)
                            print(failure.attrib['message'])
                            print(failure.text)
                            ds_test_status[function_name][test_type]['failureText'].append(failure.text)
                        except:
                            pass

                    for error in testcase:
                        try:
                            print(error.tag, error.attrib)
                            print(error.attrib['message'])
                            print(error.text)
                            ds_test_status[function_name][test_type]['failureText'].append(error.text)
                        except:
                            pass
        except:
            pass

    pp.pprint(ds_test_status)

    # Get the coverage
    coverage = parse_coverage(coverage_file_path)

    # Get a list of unique test types (derived from the contexts), in aphabetical order
    test_types = []
    for this_function in ds_test_status.keys():
        for this_test_type in ds_test_status[this_function].keys():
            if this_test_type != 'function_type':
                test_types.append(this_test_type)

    unique_test_types = sorted(set(test_types))

    ################################################################################
    # Make an HTML file of the results.

    h = open(output_file_name, "w")
    h.write('<!DOCTYPE html>\n')
    h.write('<html>\n')
    h.write('<head>\n')
    h.write('<link rel="stylesheet" href="../../../status.css">\n')
    h.write('<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>\n')
    h.write('<script type="text/javascript" src="jquery.tablesorter.js"></script>\n')
    h.write("<script>$(function(){$('table').tablesorter({widgets        : ['zebra', 'columns'],usNumberFormat : false,sortReset      : true,sortRestart    : true});});</script>\n")
    h.write('</head>\n')
    h.write('<body>\n')

    h.write("<h2>" + remote_repo_name + " - " + branch_name + "</h2>")
    h.write("Made on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    ############################################################################
    # Summary table
    summary = build_summary_table(ds_test_status, unique_test_types, pp)

    h.write("<table>")
    h.write("<tr><th>Test type</th><th>Number of tests</th><th>Pass rate</th><th>Time taken (s)</th></tr>")
    for this_unique_test_type in sorted(summary):
        if this_unique_test_type != 'total':
            h.write("<tr><td>" + this_unique_test_type + '</td><td style="text-align:right">' + str(summary[this_unique_test_type]['number']) + '</td><td  style="text-align:right">' + str(summary[this_unique_test_type]['pass']) + '</td><td style="text-align:right">' + str(int(summary[this_unique_test_type]['time'])) + "</td></tr>")
        else:
            h.write('<tr style="font-weight:bold"><td>Total</td><td style="text-align:right">' + str(summary[this_unique_test_type]['number']) + '</td><td style="text-align:right">' + str(summary[this_unique_test_type]['pass']) + '</td><td style="text-align:right">' + str(int(summary[this_unique_test_type]['time'])) + "</td></tr>")
    h.write("</table>")
    h.write("<br/><br/>")

    h.write('<table class="tablesorter">')
    h.write('<thead>')

    ############################################################################
    # Main table
    # Some fixed named columns to begin with, then use the unique test types derived from the data.
    h.write('<tr><th rowspan="2">Function name <br/>&uarr;&darr;</th><th rowspan="2">Coverage <br/>&uarr;&darr;</th>')
    h.write('<th colspan="' + str(len(unique_test_types)) + '">Test file links</th>')
    h.write('<th colspan="' + str(len(unique_test_types)) + '">Pass rate</th>')
    h.write('<th colspan="' + str(len(unique_test_types)) + '">Test run time (s)</th>')
    h.write("</tr>")

    for this_unique_test_type in unique_test_types:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")
    for this_unique_test_type in unique_test_types:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")
    for this_unique_test_type in unique_test_types:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")

    h.write("</tr>")
    h.write('</thead><tbody>')

    # Sort the dict so it is separated by ds functions and internal functions, then alphabetically.
    for this_function in sorted(ds_test_status, key=lambda x: (ds_test_status[x]['function_type'], x)):

        # Function name with link to repo
        h.write("<tr>")
        h.write('<td><a href="' + remote_repo_path + '/blob/' + branch_name + '/R/' + this_function + '.R" target="_blank">' + this_function + "</a></td>")

        # Coverage columne
        if this_function in coverage:
            this_coverage = float(coverage[this_function])
            if this_coverage > 80:
                h.write('<td class="good" style="text-align:right;">' + str(this_coverage) + '</td>')
            elif this_coverage > 60:
                h.write('<td class="ok" style="text-align:right;">' + str(this_coverage) + '</td>')
            else:
                h.write('<td class="bad" style="text-align:right;">' + str(this_coverage) + '</td>')
        else:
            h.write('<td></td>')

        # Cycle through all the test types putting in a link to the test file
        for this_unique_test_type in unique_test_types:
            expected_test_name = "test-" + this_unique_test_type + "-" + this_function+'.R'
            print(expected_test_name)
            if expected_test_name in ds_tests:
                # h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '" target="_blank">' + expected_test_name + '</a></td>')
                h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '" target="_blank">link</a></td>')
            else:
                h.write("<td></td>")

        # Cycle through all the test types putting in the pass rate with a link to the xml file and hover text for any errors.
        for this_unique_test_type in unique_test_types:
            h.write(calculate_pass_rate(ds_test_status, this_function, this_unique_test_type, gh_log_url))

        # Cycle through all the test types and put the time taken for each test to run.
        for this_unique_test_type in unique_test_types:
            try:
                h.write('<td style="text-align:right;">' + str(round(ds_test_status[this_function][this_unique_test_type]['time'], 1)) + '</td>')
            except:
                h.write("<td></td>")

        h.write("</tr>\n")
    h.write('<tbody>')
    h.write("</table>\n</body>\n</html>")


if __name__ == '__main__':
    main(sys.argv[1:])
