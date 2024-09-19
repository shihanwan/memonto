DATASET_URL=http://localhost:8080/test-dataset

sparql-query:
	curl -X POST $(DATASET_URL)/sparql \
	--data-urlencode 'query=SELECT ?s ?p ?o WHERE { GRAPH <${id}> { ?s ?p ?o } } LIMIT 100' \
	-H 'Accept: application/sparql-results+json'

sparql-delete:
	curl -X POST $(DATASET_URL)/update \
	--data-urlencode 'update=DELETE WHERE { GRAPH ?g { ?s ?p ?o } }; DELETE WHERE { ?s ?p ?o }' \
	-H 'Content-Type: application/x-www-form-urlencoded'

test:
	pytest

help:
	@echo "make sparql-query      - Execute SPARQL SELECT query"
	@echo "make sparql-delete     - Execute SPARQL DELETE query"
	@echo "make test              - Run all tests"
