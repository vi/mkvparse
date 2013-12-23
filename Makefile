all: mkvsplit

mkvsplit: mkvsplit.o
		${CC} ${LDFLAGS} mkvsplit.o -o mkvsplit
