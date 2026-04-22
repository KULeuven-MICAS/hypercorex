# ==============================================================================
# Directories
# ==============================================================================
# General
ROOT_DIR  := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
LOGS_DIR := $(ROOT_DIR)logs

# Questasim
VSIM_BUILD_DIR:= $(ROOT_DIR)questa/work_vsim
VSIM_TCL_DIR := $(ROOT_DIR)questa/vsim_tcl
VSIM_FILELIST_DIR := $(ROOT_DIR)questa/vsim_flist

# ==============================================================================
# Questasim build and simulation
# ==============================================================================
VSIM_MODULE :=
VSIM_MODULE_FILELIST := $(VSIM_FILELIST_DIR)/$(VSIM_MODULE)_flist.tcl

VSIM_FLAGS = -t 1ps
VSIM_FLAGS += -voptargs=+acc
VSIM_FLAGS += -do "log -r /*; run -a"

VOPT_FLAGS = +acc

$(VSIM_BUILD_DIR):
	mkdir -p $@
$(VSIM_TCL_DIR):
	mkdir -p $@
$(LOGS_DIR):
	mkdir -p $@

$(VSIM_TCL_DIR)/$(VSIM_MODULE).vsim: $(VSIM_MODULE_FILELIST) | $(VSIM_TCL_DIR) $(VSIM_BUILD_DIR) $(LOGS_DIR)
	touch $@
	vsim -c -do "source $<; quit" | tee $(VSIM_BUILD_DIR)/vlog.log
	@! grep -P "Errors: [1-9]*," $(VSIM_BUILD_DIR)/vlog.log
	vopt $(VOPT_FLAGS) -work $(VSIM_BUILD_DIR) tb_$(VSIM_MODULE) -o $(VSIM_MODULE)_opt | tee $(VSIM_BUILD_DIR)/vopt.log
	@! grep -P "Errors: [1-9]*," $(VSIM_BUILD_DIR)/vopt.log
	@echo "#!/bin/bash" > $@
	@echo 'vsim +permissive $(VSIM_FLAGS) -work $(VSIM_BUILD_DIR) -c \
				$(VSIM_MODULE)_opt +permissive-off' >> $@
	@chmod +x $@
	@echo "#!/bin/bash" > $@.gui
	@echo 'vsim +permissive $(VSIM_FLAGS) -work $(VSIM_BUILD_DIR) \
				$(VSIM_MODULE)_opt +permissive-off' >> $@.gui
	@chmod +x $@.gui

build-vsim: $(VSIM_TCL_DIR)/$(VSIM_MODULE).vsim

# ==============================================================================
# Cleanup
# ==============================================================================

.PHONY: clean

clean-all: clean clean-vsim

clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__ tests/__pycache__ tests/sim_build
	@echo "Done."

clean-vsim:
	@echo "Cleaning QuestaSim build artifacts..."
	rm -rf $(VSIM_BUILD_DIR) $(VSIM_TCL_DIR) $(LOGS_DIR)
	@echo "Done."

# ==============================================================================
# Debug
# ==============================================================================
show-dir:
	@echo "ROOT_DIR: $(ROOT_DIR)"
	@echo "VSIM_BUILD_DIR: $(VSIM_BUILD_DIR)"
	@echo "VSIM_TCL_DIR: $(VSIM_TCL_DIR)"
	@echo "LOGS_DIR: $(LOGS_DIR)"