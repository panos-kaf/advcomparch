SNIPER_BASE_DIR ?= /root/sniper
SNIPER_INCLUDE_DIR = $(SNIPER_BASE_DIR)/include

CC = gcc

TARGET = locks 

#LFLAG ?= -DMUTEX 
#LFLAG ?= -DTAS_CAS
#LFLAG ?= -DTAS_TS
#LFLAG ?= -DTTAS_CAS
LFLAG ?= -DTTAS_TS

#IMPLFLAG ?= -DSNIPER
IMPLFLAG ?= -DREAL

CFLAGS ?= -Wall -O0 -lpthread $(IMPLFLAG) $(LFLAG) #-DDEBUG
CFLAGS += -I$(SNIPER_INCLUDE_DIR)
CFLAGS += -Wno-unused-variable

$(TARGET): locks_scalability.c
	$(CC) $^ $(HOOKS_LDFLAGS) $(CFLAGS) -o $@

clean :
	rm -f $(TARGET)
