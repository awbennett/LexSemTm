##  Linux versions
# -lrt needed for clock_gettime(), Linux only
#      but only used in check.c
#  assumes GSL stored in regular paths
CFLAGS = -Wall -DNDEBUG -O5
# CFLAGS = -g

SRC = stable.c digamma.c yaps.c lgamma.c arms.c
HFILES = stable.h arms.h digamma.h srng.h yaps.h lgamma.h 
OBJ = $(SRC:.c=.o)
LIBRARY = libstb.a

library:  $(OBJ)
	ar rcs $(LIBRARY) $(OBJ)

clean: 
	rm -f *.o $(LIBRARY)

distclean: clean
	rm -f TAGS *.d

etags:  $(SRC) $(HFILES)
	etags  $(SRC) $(HFILES)

depend:
	makedepend $(FILES) 

# DO NOT DELETE THIS LINE -- make depend depends on it. 
