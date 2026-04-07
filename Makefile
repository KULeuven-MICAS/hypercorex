# ==============================================================================
# Cleanup
# ==============================================================================

.PHONY: clean

clean:
	@echo "Cleaning build artifacts..."
	rm -rf __pycache__ tests/__pycache__ tests/sim_build
	@echo "Done."