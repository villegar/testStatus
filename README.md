# testStatus

Simple script to parse the JUnit output of the testthat test from dsBaseClient. It builds a table sumarrizing:

- test coverage
- links to the test files
- test pass rate
- time for the tests to run


To run it use something like:

./status.py log_file coverage_file output_file_name path_to_local_dsBaseClient_repo dsBaseClient branch_name

so as a real example that looks like:

./status.py ../logs/dsBaseClient/v5.1-dev/20191119115752.xml ../logs/dsBaseClient/v5.1-dev/20191119115752.csv status.html ~/git/dsBaseClient dsBaseClient v5.1-dev
