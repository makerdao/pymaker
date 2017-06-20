help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

doc-clean:      ## Clean the documentation output directory
	rm -rf _doc

doc-build: doc-clean        ## Build the documentation
	sphinx-build . _doc

doc-open: doc-build         ## Open the documentation
	open _doc/index.html

doc-deploy: doc-build       ## Deploy the documentation at http://maker-py-docs.surge.sh
	surge --project _doc --domain maker-py-docs.surge.sh
