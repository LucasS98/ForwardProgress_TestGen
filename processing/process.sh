#!/bin/bash
# Script to process tests and generate png/pdf

if [ $# -eq 0 ]
then
    echo "Supply folder name to process"
    exit 0
fi

shopt -s nullglob

str="_processed"
newname="$1$str"

rm -r $newname
cp -r $1 $newname


source="${BASH_SOURCE%/*}/"
count=0
for f in $newname/*/
do
    for f2 in $f/*.dot
    do
	if [[ $f =~ "_small" ]]
	then
	    :
	else
	    python $source/DotModify.py $f2
	    v2=${f2%.dot}
	    dot -Tpdf ${v2}_simple.dot -o $v2.pdf
	    dot -Tpng ${v2}_simple.dot -o $v2.png
	    cp $v2.xml ${v2}xml.txt

	    folderN=${f2%/*}
	    v3=${f2##*/}
	    index=${v3%.dot}
       	    python $source/CADPGen.py $folderN $index $source
	    
	    count=`expr $count + 1`
	fi
    done 		
done

python $source/HTMLGen.py $source/testExplorer.html $newname/testExplorer.html $count
