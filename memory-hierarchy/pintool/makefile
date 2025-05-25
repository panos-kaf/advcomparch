# If the tool is built out of the kit, PIN_ROOT must be specified in the make invocation and point to the kit root.
PIN_ROOT ?= /home/panos/tools/pin
#PIN_ROOT ?= /mnt/c/NTUA/tools/pin # windows
ifdef PIN_ROOT
CONFIG_ROOT := $(PIN_ROOT)/source/tools/Config
else
CONFIG_ROOT := ../Config
endif
include $(CONFIG_ROOT)/makefile.config
include makefile.rules
include $(TOOLS_ROOT)/Config/makefile.default.rules

TOOL_CXXFLAGS += -Wno-array-bounds
