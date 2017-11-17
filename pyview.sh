#!/usr/bin/bash

# TODO : detect `if __name__=="__main__"` lines

for arg in `find "$@" -iname "*.py"` ; do
	echo "File $arg:"
	grep -nhP "^\s*(?:(:?#\s*TODO)|def|class|import|\"\"\".+)" $arg |\
	perl -pe's/^(\d+)/    $1 /g; s/^\s*([ \d]{5}):/$1/g'
	echo
done
