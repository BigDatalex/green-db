.PHONY: patch-core-version patch-database-version patch-extract-version patch-message-queue-version patch-scraping-version patch-workers-version patch-all patch-version

patch-core-version:
	$(MAKE) -C core

patch-database-version:
	$(MAKE) -C database

patch-extract-version:
	$(MAKE) -C extract

patch-message-queue-version:
	$(MAKE) -C message-queue

patch-scraping-version:
	$(MAKE) -C scraping

patch-workers-version:
	$(MAKE) -C workers

patch-all: patch-core-version patch-database-version patch-extract-version patch-message-queue-version patch-scraping-version patch-workers-version

patch-version: patch-all
	# get version from core package.
	$(eval VERSION=$(shell cd core; poetry version -s))
	
	git add core/pyproject.toml database/pyproject.toml extract/pyproject.toml message-queue/pyproject.toml scraping/pyproject.toml workers/pyproject.toml infrastructure/charts/scrapyd/Chart.yaml infrastructure/charts/workers/Chart.yaml
	git commit -m "bump version to '${VERSION}'"
	git tag ${VERSION}

	# push everything
	git push
	git push origin ${VERSION}