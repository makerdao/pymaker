help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

doc-clean:      ## Clean the documentation output directory
	cd docs; rm -rf _doc

doc-build: doc-clean        ## Build the documentation
	cd docs; sphinx-build . _doc

doc-open: doc-build         ## Open the documentation
	cd docs; open _doc/index.html

doc-deploy: doc-build       ## Deploy the documentation at http://maker-keeper-docs.surge.sh
	cd docs; surge --project _doc --domain maker-keeper-docs.surge.sh
