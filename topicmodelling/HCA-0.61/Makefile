##
#
#  to get multi-threaded version working, add -DH_THREADS
#  to CPPFLAGS to Linux/Mac-OSX versions below
#     e.g.,  remove the comment '#' symbol
#

#######################################
##  Linux versions
#
#  add "-g" or "-O5 -DNDEBUG" or ....
#  WARNING:  threads and debugging code ('-g') don't mix because some of the
#            asserts are shuffled around by the compiler
MYDEBUG=-O5 -DNDEBUG -ffast-math -DHAVE_INLINE 
# MYDEBUG=-g

CPPFLAGS =  -I../util/ -I../lib/ $(MYDEBUG) # -DH_THREADS
CFLAGS = -Wall 
LDFLAGS = -L../util -L../lib -lhca -lstb  -lm -pthread

####################################################
##  Mac OSX versions
#CFLAGS = -D__WORDSIZE=64 -I/opt/local/include -Wall
#LDFLAGS = -L/opt/local/lib -L../util -L../lib -lhca -lstb -lm -pthread
#CPPFLAGS=-I/opt/local/include -I../util/ -I../lib/ 


export CFLAGS
export LDFLAGS
export CPPFLAGS

all:    util lib hca

yes:

util:    yes
	cd util; make 

lib:    yes
	cd lib; make 

hca:    yes
	cd hca; make 

clean:  yes
	cd util; make clean
	cd lib; make clean
	cd hca; make clean	

distclean: 
	rm -f TAGS */TAGS
	cd lib; make distclean
	cd util; make distclean
	cd hca; make distclean	

etags:  
	etags  lib/*.c lib/*.h util/*.c util/*.h hca/*.h hca/*.c
