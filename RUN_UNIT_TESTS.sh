
#
#  Perform unit testing
#
echo "Performing Unit Testing:"
pytest
if (( $? != 0 ))
then
   echo "Resolve all of the above errors before checking for code coverage."
   exit 1
fi

#
#  Check code coverage percentage
#
echo ""
echo "Checking code coverage:"
pytest --cov=.

