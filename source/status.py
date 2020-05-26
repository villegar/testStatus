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

# TO DO
# Name-value arg parsing (with defaults?)
# Add better runtime output/logging control.

import argparse
import datetime
import csv
import glob
import os.path
import pprint
import sys
import xml.etree.ElementTree as ET

__author__ = "Olly Butters"
__date__ = "26/5/20"


################################################################################
# Build summary dictionary.
# Used as the source of data for the HTML summary table at top of page.
# Will look something like:
# summary[smk][pass] = N
# summary[smk][problems] = N
# summary[smk][number] = N
# summary[smk][time] = N
# for each test class, expt etc. And:
# summay[total][pass]
# summay[total][problems]
# summay[total][number]
# summay[total][time]
def build_summary_dictionary(ds_test_status, unique_test_types, envs, pp):
    summary = {}

    # Initialize as zero. Go through all envs, skipping if there are duplicate test_types across envs
    for this_env in envs:
        for this_unique_test_type in unique_test_types[this_env]:
            try:
                summary[this_unique_test_type] = {}
                summary[this_unique_test_type]['pass'] = 0
                summary[this_unique_test_type]['problems'] = 0
                summary[this_unique_test_type]['number'] = 0
                summary[this_unique_test_type]['time'] = 0
            except:
                pass

    # Totals
    summary['total'] = {}
    summary['total']['pass'] = 0
    summary['total']['problems'] = 0
    summary['total']['number'] = 0
    summary['total']['time'] = 0

    for this_env in envs:
        for this_function_name in ds_test_status[this_env]:
            pp.pprint(this_function_name)
            for this_unique_test_type in unique_test_types[this_env]:
                try:
                    this_failures = int(ds_test_status[this_env][this_function_name][this_unique_test_type]['failures'])
                    this_errors = int(ds_test_status[this_env][this_function_name][this_unique_test_type]['errors'])
                    this_number = int(ds_test_status[this_env][this_function_name][this_unique_test_type]['number'])
                    this_time = float(ds_test_status[this_env][this_function_name][this_unique_test_type]['time'])

                    this_problems = this_failures + this_errors

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
def build_pass_rate_table_cell(ds_test_status, function_name, test_class, gh_log_url):
    try:
        this_failures = int(ds_test_status[function_name][test_class]['failures'])
        this_errors = int(ds_test_status[function_name][test_class]['errors'])
        this_number = int(ds_test_status[function_name][test_class]['number'])

        this_problems = this_failures + this_errors

        if this_problems == 0:
            return('<td class="good" style="text-align:center;"><a href ="' + gh_log_url + '" target="_blank">' + str(this_number) + "/" + str(this_number) + "</a></td>")
        elif this_problems > 0:
            # Sometimes there is no failure text.
            if len(ds_test_status[function_name][test_class]['failureText']) > 0:
                return('<td class="bad" style="text-align:center;""><span class="tooltip"><a href ="' + gh_log_url + '" target="_blank">' + str(this_number - this_problems) + "/" + str(this_number) + '</a><span class="tooltiptext">' + '<br/>----------<br/>'.join(map(str, ds_test_status[function_name][test_class]['failureText'])) + '</span></span></td>')
            else:
                return('<td class="bad" style="text-align:center;""><span class="tooltip"><a href ="' + gh_log_url + '" target="_blank">' + str(this_number - this_problems) + "/" + str(this_number) + '</a><span class="tooltiptext">No Error/Failure messages found. grep the xml file to check.</span></span></td>')
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
# Parse the versions file. Write the html table to file.
def parse_versions_file(versions_file_path, h):
    versions = {}
    with open(versions_file_path) as f:
        
        for row in f:
            temp = row.split(':')
            versions[temp[0]] = temp[1]

    print(versions)

    h.write('<table class="versions">')

    for key in versions:
        h.write("<tr><td>" + key + "</td><td>" + versions[key] + "</td></tr>")

    h.write("</table>")



############################################################################
# HTML summary table
def build_html_summary_table(ds_test_status, unique_test_types, envs, pp, h):

    summary = build_summary_dictionary(ds_test_status, unique_test_types, envs, pp)

    h.write('<table class="summary">')
    h.write("<tr><th>Test type</th><th>Number of tests</th><th>Number of passes</th><th>Time taken (s)</th></tr>")
    for this_unique_test_type in sorted(summary):
        if this_unique_test_type != 'total':
            h.write("<tr><td>" + this_unique_test_type + '</td><td style="text-align:right">' + str(summary[this_unique_test_type]['number']) + '</td><td  style="text-align:right">' + str(summary[this_unique_test_type]['pass']) + '</td><td style="text-align:right">' + str(int(summary[this_unique_test_type]['time'])) + "</td></tr>")
        else:
            h.write('<tr style="font-weight:bold"><td>Total</td><td style="text-align:right">' + str(summary[this_unique_test_type]['number']) + '</td><td style="text-align:right">' + str(summary[this_unique_test_type]['pass']) + '</td><td style="text-align:right">' + str(int(summary[this_unique_test_type]['time'])) + "</td></tr>")
    h.write("</table>")


############################################################################
# HTML Main table
def build_html_table(ds_test_status, unique_test_types, env, pp, h, remote_repo_path, branch_name, gh_log_url, coverage, ds_tests, show_coverage_column):

    h.write('<table class="tablesorter">')
    h.write('<thead>')
    # Some fixed named columns to begin with, then use the unique test types derived from the data.
    h.write('<tr><th rowspan="2">Function name <br/>&uarr;&darr;</th>')
    if show_coverage_column: h.write('<th rowspan="2">Coverage <br/>&uarr;&darr;</th>')
    h.write('<th colspan="' + str(len(unique_test_types[env])) + '">Test file links</th>')
    h.write('<th colspan="' + str(len(unique_test_types[env])) + '">Pass rate</th>')
    h.write('<th colspan="' + str(len(unique_test_types[env])) + '">Test run time (s)</th>')
    h.write("</tr>")

    # Put in the up/down arrows to allow table sorting
    for this_unique_test_type in unique_test_types[env]:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")
    for this_unique_test_type in unique_test_types[env]:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")
    for this_unique_test_type in unique_test_types[env]:
        h.write("<th>" + this_unique_test_type + "<br/>&uarr;&darr;</th>")

    h.write("</tr>")
    h.write('</thead><tbody>')

    # Sort the dict so it is separated by ds functions and internal functions, then alphabetically.
    for this_function in sorted(ds_test_status[env], key=lambda x: (ds_test_status[env][x]['function_type'], x)):

        # Function name with link to repo
        h.write("<tr>")
        h.write('<td><a href="' + remote_repo_path + '/blob/' + branch_name + '/R/' + this_function + '.R" target="_blank">' + this_function + "</a></td>")

        if show_coverage_column:
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
        for this_unique_test_type in unique_test_types[env]:
            expected_test_name = "test-" + this_unique_test_type + "-" + this_function + '.R'
            print(expected_test_name)
            if expected_test_name in ds_tests:
                h.write('<td class="good"><a href="' + remote_repo_path + '/blob/' + branch_name + '/tests/testthat/' + expected_test_name + '" target="_blank">link</a></td>')
            else:
                h.write("<td></td>")

        # Cycle through all the test types putting in the pass rate with a link to the xml file and hover text for any errors.
        for this_unique_test_type in unique_test_types[env]:
            h.write(build_pass_rate_table_cell(ds_test_status[env], this_function, this_unique_test_type, gh_log_url))

        # Cycle through all the test types and put the time taken for each test to run.
        for this_unique_test_type in unique_test_types[env]:
            try:
                h.write('<td style="text-align:right;"><span class="tooltip">' + str(round(ds_test_status[env][this_function][this_unique_test_type]['time'], 1)) + '<span class="tooltiptext">' + '<br/>----------<br/>'.join(map(str, ds_test_status[env][this_function][this_unique_test_type]['contextTimes'])) + '</span></span></td>')
            except:
                h.write("<td></td>")

        h.write("</tr>\n")
    h.write('<tbody>')
    h.write("</table>")







################################################################################
#
def main(args):
    remote_root_path = "http://github.com/datashield/"

    # Get all the command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("log_file_path", help="Path to the XML JUnit log file.")
    parser.add_argument("coverage_file_path", help="Path to the csv coverage file.")
    parser.add_argument("versions_file_path", help="Path to the versions file.")
    parser.add_argument("output_file_path", help="Path to the output file. (e.g. output.html)")
    parser.add_argument("local_repo_path", help="Path to the locally checked out repository.")
    parser.add_argument("remote_repo_name", help="Name of the remote repository.")
    parser.add_argument("branch", help="Branch name.")
    args = parser.parse_args()
    devtools_test_output_file = args.log_file_path
    coverage_file_path = args.coverage_file_path
    versions_file_path = args.versions_file_path
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
    # Get list of functions from R folder in the LOCAL repo as defined in lecal_repo_path
    #
    print("\n\n##########")
    ds_functions_path = glob.glob(local_repo_path + "/R/*.R")

    print("Number of local functions found: " + str(len(ds_functions_path)))

    ds_functions = []

    # Drop the .R at the end while doing this.
    for this_path in ds_functions_path:
        ds_functions.append((os.path.basename(this_path)).replace('.R', ''))

    ds_functions.sort()

    for this_function in ds_functions:
        print(this_function)

    # Make the test status dictionary. Ultimately it will look like the below.
    # The function names are based on the list of R functions in R directory.
    # env is a flag capturing the environment this test belongs to. Currently
    # this is one of r or vm and indicates if the test is based on the list of
    # functions in the R folder or doing testing something else.
    # ds_test_status[env][function_name][test_type]['number']
    # ds_test_status[env][function_name][test_type]['skipped']
    # ds_test_status[env][function_name][test_type]['failures']
    # ds_test_status[env][function_name][test_type]['errors']
    # ds_test_status[env][function_name][test_type]['time']
    # ds_test_status[env][function_name][test_type]['failureText'] = list()
    # ds_test_status[env][function_name][test_type]['contextTimes'] = list()
    # ds_test_status[env][function_name]['function_type'] = 'ds' or 'internal'

    # Make the dictionary and add the two environments.
    ds_test_status = {}
    ds_test_status['r'] = {}
    ds_test_status['vm'] = {}

    # Add all the functions in the R folder to ds_test_status. Do this now (as
    # opposed to driving this from the xml file), so any R functions that exist for
    # which there is no tests show up in the final table.
    for this_function in ds_functions:
        this_function = this_function.replace('.R', '')  # Drop the .R part from the end.
        ds_test_status['r'][this_function] = {}

        # Differentiate the internal and external functions. The external functions
        # are ones that users would call and ALWAYS begin with "ds.", whereas internal
        # functions are called by other functions. Used later to make table sorting nicer.
        if(this_function.startswith('ds')):
            ds_test_status['r'][this_function]['function_type'] = 'ds'
        else:
            ds_test_status['r'][this_function]['function_type'] = 'internal'

    ################################################################################
    # Get the list of tests from the local repo
    #
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
    # <function name>::<maths|expt|smk|args|disc>::<Optional other info>
    # e.g.
    # ds.asFactor::smoke
    for testsuite in root:
        print('\n', testsuite.attrib['name'], testsuite.attrib['tests'], testsuite.attrib['skipped'], testsuite.attrib['failures'], testsuite.attrib['errors'], testsuite.attrib['time'])

        context = testsuite.attrib['name']

        # Split by :: delimiter
        context_parts = context.split('::')

        function_name = ''
        test_type = ''
        test_type_extra = ''

        # Function name
        try:
            function_name = context_parts[0]
            function_name = function_name.replace('()', '')  # Drop the brackets from the function name if they exist
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

        # Extra info, like if single or multiple data source. Free form field
        try:
            test_type_extra = context_parts[2]
            print(test_type_extra)
        except:
            print("No extra test type.")

        # Set the environment as either r or vm depending if this function_name
        # is in the list of ds_functions - i.e. if it matches a function name
        # in the R directory.
        if function_name in ds_functions:
            env = 'r'
        else:
            env = 'vm'

        # Build the dictionary ds_test_status[function_name][test_type]{number, skipped, failures, errors, time}
        # This should automatically make an entry for each test type specified in the testthat files.
        try:

            # Add the function if it already isn't in ds_test_status. This will happen for tests that
            # are not named to match the R file names.
            if function_name not in ds_test_status[env]:
                ds_test_status[env][function_name] = {}
                ds_test_status[env][function_name]['function_type'] = 'NA'

            # If this test_type is not defined then initiate it for this function_name
            if test_type not in ds_test_status[env][function_name]:
                ds_test_status[env][function_name][test_type] = {}
                ds_test_status[env][function_name][test_type]['number'] = 0
                ds_test_status[env][function_name][test_type]['skipped'] = 0
                ds_test_status[env][function_name][test_type]['failures'] = 0
                ds_test_status[env][function_name][test_type]['errors'] = 0
                ds_test_status[env][function_name][test_type]['time'] = 0
                ds_test_status[env][function_name][test_type]['failureText'] = list()
                ds_test_status[env][function_name][test_type]['contextTimes'] = list()

            ds_test_status[env][function_name][test_type]['number'] += int(testsuite.attrib['tests'])
            ds_test_status[env][function_name][test_type]['skipped'] += int(testsuite.attrib['skipped'])
            ds_test_status[env][function_name][test_type]['failures'] += int(testsuite.attrib['failures'])
            ds_test_status[env][function_name][test_type]['errors'] += int(testsuite.attrib['errors'])
            ds_test_status[env][function_name][test_type]['time'] += float(testsuite.attrib['time'])

            # Not every test_type_extra field is set in the test files, so make sure there is a default.
            if test_type_extra != '':
                context_section = test_type_extra
            else:
                context_section = "Main"

            ds_test_status[env][function_name][test_type]['contextTimes'].append(context_section + ': ' + testsuite.attrib['time'])

            # Parse the text from the failure notice into the ds_test_status dictionary
            # if ds_test_status[env][function_name][test_type]['failures'] > 0:
            if ds_test_status[env][function_name][test_type]['failures'] > 0 or ds_test_status[env][function_name][test_type]['errors'] > 0:
                print("\n\nERRORS")
                print(testsuite.tag, testsuite.attrib)
                for testcase in testsuite:
                    print(testcase.tag, testcase.attrib)
                    for failure in testcase:
                        try:
                            print(failure.tag, failure.attrib)
                            print(failure.attrib['message'])
                            print(failure.text)
                            ds_test_status[env][function_name][test_type]['failureText'].append(failure.text)
                        except:
                            pass

                    for error in testcase:
                        try:
                            print(error.tag, error.attrib)
                            print(error.attrib['message'])
                            print(error.text)
                            ds_test_status[env][function_name][test_type]['failureText'].append(error.text)
                        except:
                            pass
        except:
            pass


    print("\n\n################\nParsed ds_test_status")
    pp.pprint(ds_test_status)

    # Get the coverage
    coverage = parse_coverage(coverage_file_path)




    ################################################################################
    # Make an HTML file of the results.

    h = open(output_file_name, "w")
    h.write('<!DOCTYPE html>\n')
    h.write('<html>\n')
    h.write('<head>\n')
    h.write('<link rel="stylesheet" href="../../../status.css">\n')
    h.write('<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>\n')
    h.write('<script type="text/javascript" src="../../../jquery.tablesorter.js"></script>\n')
    h.write("<script>$(function(){$('table').tablesorter({widgets        : ['zebra', 'columns'],usNumberFormat : false,sortReset      : true,sortRestart    : true});});</script>\n")
    h.write('</head>\n')
    h.write('<body>\n')

    h.write("<h2>" + remote_repo_name + " - " + branch_name + "</h2>")
    h.write("Made on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))




    # Get a list of unique test types (derived from the contexts), in aphabetical order for each env
    test_types = {}
    for this_env in ds_test_status.keys():
        if this_env not in test_types:
            test_types[this_env] = []
        for this_function in ds_test_status[this_env].keys():
            for this_test_type in ds_test_status[this_env][this_function].keys():
                if this_test_type != 'function_type':
                    test_types[this_env].append(this_test_type)


    # Dedupe and sort test types for each env type
    unique_test_types = {}
    for this_env in ds_test_status.keys():
        unique_test_types[this_env] = sorted(set(test_types[this_env]))


    h.write("<br/><br/>")

    h.write('<div style="overflow:auto">')
    build_html_summary_table(ds_test_status, unique_test_types, ['r','vm'], pp, h)
    parse_versions_file(versions_file_path, h)
    h.write("</div>")



    h.write("<h3>Tests based on DataSHIELD functions</h3>")
    build_html_table(ds_test_status, unique_test_types, 'r', pp, h, remote_repo_path, branch_name, gh_log_url, coverage, ds_tests, True)
    h.write("<br/><br/>")

    h.write("<h3>Tests based on the environment</h3>")
    build_html_table(ds_test_status, unique_test_types, 'vm', pp, h, remote_repo_path, branch_name, gh_log_url, coverage, ds_tests, False)
    
    
    h.write("</body>\n</html>")


if __name__ == '__main__':
    main(sys.argv[1:])
