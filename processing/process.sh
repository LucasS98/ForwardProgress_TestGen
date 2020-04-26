#!/bin/bash
# Script to process tests, generate png/pdfs and process labels

if [ $# -eq 0 ]
then
	echo "Supply folder name to process"
	exit 0
fi

shopt -s nullglob

str="_processed"
newname="$1$str"

rm -rf $newname
cp -r $1 $newname
rm -rf $newname/../checker_files
mkdir $newname/../checker_files


source="${BASH_SOURCE%/*}/"
count=0
for f in $newname/*/
do
	for f2 in $f/*.dot
	do
	if [[ $f2 =~ *_simple* ]]
	then
		:
	else
		# Make Dot, PNG, PDF files
		python $source/DotModify.py $f2
		v2=${f2%.dot}
		dot -Tpdf ${v2}_simple.dot -o $v2.pdf
		dot -Tpng ${v2}_simple.dot -o $v2.png
		cp $v2.xml ${v2}xml.txt

		# Getting some useful variables for parameters
		folderN=${f2%/*}
		v3=${f2##*/}
		index=${v3%.dot}
		# Make files for CADP
		python $source/CADPGen.py $folderN $index $source

		# Process CADP files into labels
		(cd $folderN/checker && lnt.open test_${index}_none.lnt generator test_${index}_none.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_obe.lnt generator test_${index}_obe.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_hsa.lnt generator test_${index}_hsa.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_lobe.lnt generator test_${index}_lobe.bcg > /dev/null)
		(cd $folderN/checker && lnt.open test_${index}_hsa_obe.lnt generator test_${index}_hsa_obe.bcg > /dev/null)
		(cd $folderN/checker && svl test_${index}.svl > labels_${index}.txt)
		python $source/ProcessLabels.py $folderN/checker/labels_${index}.txt

		# Make dot files from CADP graphs (convert to PDF manually as needed)
		(cd $folderN/checker && for i in *bcg ; do bcg_io $i -graphviz `basename $i .bcg`.dot ; done )

		# Move files to a different folder to clean test folder somewhat
		(cd $folderN/checker && cp labels_${index}.txt ../label_${index}.txt)
		(cd $folderN && mv checker ../../checker_files/$index)

		# Make Amber file (no saturation) for test (thanks Hari!)
		python $source/amber_test_generation.py $v2.txt $v2

		count=`expr $count + 1`
	fi
	done 		
done

# Convert scheduler results to CSV for comparison
python $source/CreateCSV.py $newname OBE
python $source/CreateCSV.py $newname HSA
python $source/CreateCSV.py $newname HSA_OBE
python $source/CreateCSV.py $newname LOBE
python $source/CreateCSV.py $newname WEAK_FAIR

# Copy HTML (with appropriate changes) to test folder
python $source/HTMLGen.py $source/testExplorer.html $newname/testExplorer.html $count
