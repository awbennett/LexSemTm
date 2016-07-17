#!/bin/sh
#
#   these are all the calls in the manual
#   if the last line output is " Cannot run hca/hca ..." it hasn't worked.
#   note if it quits early due to errors it leaves files,
#   otherwise it deletes everything;
#   WARNING:   only run if you're happy to do a 'rm -rf c1.*' at end
#   also note some output goes to c1.log ...

TESTSTEM=c1

hca/hca -v -e -K20 -Adir -Bdir -C100 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -e -K20 -Adir -Bdir -C100 dddata/ch $TESTSTEM
	exit 1
fi
hca/hca -v -e -K20 -B0.001 -C100 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -e -K20 -B0.001 -C100 data/ch $TESTSTEM
	exit 1
fi
hca/hca -v -v -r0 -e -V -C0 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -v -r0 -e -V -C0 data/ch $TESTSTEM
	exit 1
fi
hca/hca -v -v -r0 -e -V -V -oidf,100 -C0 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -v -r0 -e -V -V -oidf,100 -C0 data/ch $TESTSTEM
	exit 1
fi
hca/hca -v -r0 -e -lsparse,2,1 -ltheta,2,1,0.001 -C20 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -r0 -e -lsparse,2,1 -ltheta,2,1,0.001 -C20 data/ch $TESTSTEM
	exit 1
fi
cp data/ch.smap-example data/ch.smap
hca/hca -v -r0 -e -lsparse,2,1 -ltheta,2,1,0.001 -C20 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
        rm data/ch.smap
	echo Cannot run hca/hca -v -r0 -e -lsparse,2,1 -ltheta,2,1,0.001 -C20 data/ch $TESTSTEM
	exit 1
fi
rm data/ch.smap
hca/hca -e -v -K20 -C100 -c20 -T100 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -e -v -K20 -C100 -c20 -T100 data/ch $TESTSTEM
	exit 1
fi
hca/hca -v -e -r0 -C0 -hdoc,4 -T100 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -e -r0 -C0 -hdoc,4 -T100 data/ch $TESTSTEM
	exit 1
fi
hca/hca -e -v -v -V -r0 -C0 -Llike,0,0 -X -p -T100 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -e -v -v -V -r0 -C0 -Llike,0,0 -X -p -T100 data/ch $TESTSTEM
	exit 1
fi
hca/hca -v -v -e -K20 -C100 -Sbdk=100 -Sad=0.5 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca -v -v -e -K20 -C100 -Sbdk=100 -Sad=0.5 data/ch $TESTSTEM
	exit 1
fi
hca/hca  -K20 -v -v -C300 -ltheta,2,250  -lphi,2,250 data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca  -K20 -v -v -C300 -ltheta,2,250  -lphi,2,250 data/ch $TESTSTEM
	exit 1
fi
cp $TESTSTEM.theta $TESTSTEM.testprob
hca/hca  -rphi -rtheta -hall -C0 -r0 -v -v -Tdata/ch data/ch $TESTSTEM
if [ "$?" != "0" ]; then
	echo Cannot run hca/hca  -rphi -rtheta -hall -C0 -r0 -v -v -Tdata/ch data/ch $TESTSTEM
	exit 1
fi
rm -rf $TESTSTEM.*
