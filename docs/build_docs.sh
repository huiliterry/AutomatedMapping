# script - automated update documents
cd /home/hli47/InseasonMapping/docs
sphinx-apidoc -o source ../Code
make html