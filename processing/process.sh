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

		(cd $folderN/checker && lnt.open test_${index}_none.lnt generator test_${index}_none.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_obe.lnt generator test_${index}_obe.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_hsa.lnt generator test_${index}_hsa.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_lobe.lnt generator test_${index}_lobe.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_hsa_obe.lnt generator test_${index}_hsa_obe.bcg > /dev/null)
		(cd $folderN/checker && svl test_${index}.svl > labels_${index}.txt)
		python $source/ProcessLabels.py $folderN/checker/labels_${index}.txt
		(cd $folderN/checker && cp labels_${index}.txt ../label_${index}.txt)
		(cd $folderN && rm -rf checker)

		python $source/amber_test_generation.py $v2.txt $v2

		count=`expr $count + 1`
	fi
	done 		
done

python $source/HTMLGen.py $source/testExplorer.html $newname/testExplorer.html $count
