# detect if the CI mode is enabled
IS_CI_ENABLED := $(shell [ -z "$$CI" ] && v=false || v=true; echo $$v)

# toggle bash verbosity
ifeq ($(IS_CI_ENABLED),false)
	SHELL := /usr/bin/env bash
else
	SHELL := /usr/bin/env bash -x
endif

# supress make unnecessary warnings/infos
MAKEFLAGS += -s

# get all arguments after the target name
RUN_ARGS := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))

# ...and turn them into do-nothing targets
$(eval $(RUN_ARGS):;@:)

# get target's first argument
RUN_ARG := $(word 1, $(RUN_ARGS))

# exit if there's no arguments
ifeq ($(RUN_ARG),)
$(error Error: empty action! Example: make <ACTION:[run,gen,test or build]> <TARGET:[app,config or <SERVICE_NAME>]>)
endif

# The cat abuse is needed for e.g. Ubuntu, where the recommended install of yq is a strictly confined snap and can only be used via stdin by default.
define yaml_query
$(if $(strip $1),$(shell cat '$(strip $1)' | yq r - '$(strip $2)'),)
endef

# detect the current operating system
DETECTED_OS := $(shell uname)

# detect if the CI mode is enabled
IS_CI_ENABLED := $(shell [ -z "$$CI" ] && v=false || v=true; echo $$v)

# check prerequisites if not in the CI
ifeq ($(IS_CI_ENABLED),false)
EXECUTABLES := git go git-crypt gcloud docker envsubst
PREREQUISITES := $(foreach exec,$(EXECUTABLES),\
	$(if $(shell which $(exec)), ,$(error "Error: $(exec) is not available in your PATH")))
endif

# detect general attributes
TARGET_NAME := $(word 2, $(RUN_ARGS))
ifdef TARGET_NAME
	BUILDFILE := $(shell [ -f **/${TARGET_NAME}/Buildfile ] && find **/${TARGET_NAME} -name Buildfile)
    ifneq ($(TARGET_NAME),$(filter $(TARGET_NAME),all list))
        BUILDER := $(call yaml_query,$(BUILDFILE), metadata.builder)
        RELEASE_VERSION := $(call yaml_query,$(BUILDFILE), metadata.version)
        COMMIT_ID := $(shell v=$$(git rev-parse --short HEAD); echo $$v)
        KIND := $(call yaml_query,$(BUILDFILE), kind)
        ifeq ($(KIND),App)
	        PARENT := apps
        else ifeq ($(KIND),CronJob)
	        PARENT := jobs
        else ifeq ($(KIND),Test)
	        PARENT := tests
        else ifeq ($(KIND),Service)
	        PARENT := services
        endif
    endif
endif

# decide what to do based on the second argument
ifeq ($(RUN_ARG),project) # make <ACTION> project
	INIT_TARGET := init-prj-deps init-prj-k8s-config
else ifeq ($(RUN_ARG),config) # make <ACTION> config <ENVIRONMENT>/<NAMESPACE>
	TEST_TARGET := test-config
	GEN_TARGET := gen-config
	APPLY_TARGET := apply-config
	CLOUD_ENV_NAME := $(shell echo $(word 2, $(RUN_ARGS)) | cut -d"/" -f1)
	K8S_NAMESPACE := $(shell echo $(word 2, $(RUN_ARGS)) | cut -d"/" -f2)
	# use context names as created by target "init-prj-k8s-config", which start with "$${PROJECT_NAME}-".
	# but if CI mode is on, use context names without the "$${PROJECT_NAME}-" prefix.
	K8S_CONTEXT := $(if $(findstring true,$(IS_CI_ENABLED)), $(CLOUD_ENV_NAME), $${PROJECT_NAME}-aio)
else ifeq ($(RUN_ARG),image) # make <ACTION> image <TARGET_NAME>
	BUILD_TARGET := build-image
else ifeq ($(RUN_ARG),docker) # make <ACTION> docker all
    ifeq ($(TARGET_NAME),all)
		GEN_TARGET := gen-docker-all
		BUILD_TARGET := build-docker-all
    else
		BUILD_TARGET := build-docker
		GEN_TARGET := gen-docker
    endif
else ifeq ($(RUN_ARG),builder) # make <ACTION> builder <TARGET_NAME>
	GET_TARGET := get-builder
else ifeq ($(RUN_ARG),app) # make <ACTION> app <TARGET_NAME> [<ENVIRONMENT>/<NAMESPACE>]
	SERVICE_NAME := $(shell v=$$( find **/${TARGET_NAME} -name Buildfile -exec yq r {} metadata.name \;); echo $$v)
	INIT_TARGET := init-app
	TEST_TARGET := test-app
	BUILD_TARGET := build-app
	GEN_TARGET := gen-app
	RUN_TARGET := run-app
	DEPLOY_TARGET := deploy-manifest
	CLOUD_ENV_NAME := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f1)
	K8S_NAMESPACE := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f2)
	# use context names as created by target "init-prj-k8s-config", which start with "$${PROJECT_NAME}-".
	# but if CI mode is on, use context names without the "$${PROJECT_NAME}-" prefix.
	K8S_CONTEXT := $(if $(findstring true,$(IS_CI_ENABLED)), $(CLOUD_ENV_NAME), $${PROJECT_NAME}-aio)
	MANUAL_DEPLOY_TARGET := init-app build-app build-image gen-manifest deploy-manifest
else ifeq ($(RUN_ARG),test) # make <ACTION> test <TARGET_NAME>
	INIT_TARGET := init-test
	RUN_TARGET := run-test
else ifeq ($(RUN_ARG),apps) # make <ACTION> apps
	GET_TARGET := get-apps
else ifeq ($(RUN_ARG),services) # make <ACTION> services
	GET_TARGET := get-services
else ifeq ($(RUN_ARG),changes) # make <ACTION> changes <KIND> <FROM_REVISION> <TO_REVISION>
	GET_TARGET := get-changes
	CHANGES_KIND := $(word 2, $(RUN_ARGS))
	FROM_REVISION := $(word 3, $(RUN_ARGS))
	TO_REVISION := $(word 4, $(RUN_ARGS))
else ifeq ($(RUN_ARG),tests) # make <ACTION> tests
	GET_TARGET = get-tests
else ifeq ($(RUN_ARG),job) # make <ACTION> job <TARGET_NAME> [<ENVIRONMENT>/<NAMESPACE>]
	SERVICE_NAME := $(shell v=$$( find **/${TARGET_NAME} -name Buildfile -exec yq r {} metadata.name \;); echo $$v)
	CLOUD_ENV_NAME := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f1)
	K8S_NAMESPACE := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f2)
	# use context names as created by target "init-prj-k8s-config", which start with "$${PROJECT_NAME}-".
	# but if CI mode is on, use context names without the "$${PROJECT_NAME}-" prefix.
	K8S_CONTEXT := $(if $(findstring true,$(IS_CI_ENABLED)), $(CLOUD_ENV_NAME), $${PROJECT_NAME}-aio)
	BUILD_TARGET := build-job build-image
	GEN_TARGET := gen-job
	RUN_TARGET := run-job
	MANUAL_DEPLOY_TARGET := build-job build-image gen-manifest deploy-manifest
else ifeq ($(RUN_ARG),openapi) # make <ACTION> openapi <TARGET_NAME>
	GEN_TARGET := Skip-target
else ifeq ($(RUN_ARG),service) # make <ACTION> service <TARGET_NAME> [<ENVIRONMENT>/<NAMESPACE>]
	SERVICE_NAME := $(shell v=$$( find **/${TARGET_NAME} -name Buildfile -exec yq r {} metadata.name \;); echo $$v)
	INIT_TARGET := init-service
	TEST_TARGET := test-service
	BUILD_TARGET := build-service
	GEN_TARGET := gen-manifest
	RUN_TARGET := run-service
	CLEAN_TARGET := clean-service
	DEPLOY_TARGET := deploy-manifest
	CLOUD_ENV_NAME := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f1)
	K8S_NAMESPACE := $(shell echo $(word 3, $(RUN_ARGS)) | cut -d"/" -f2)
	# use context names as created by target "init-prj-k8s-config", which start with "$${PROJECT_NAME}-".
	# but if CI mode is on, use context names without the "$${PROJECT_NAME}-" prefix.
	K8S_CONTEXT := $(if $(findstring true,$(IS_CI_ENABLED)), $(CLOUD_ENV_NAME), $${PROJECT_NAME}-aio)
    ifeq ($(BUILDER),none)
		MANUAL_DEPLOY_TARGET := gen-manifest deploy-manifest
	else
		MANUAL_DEPLOY_TARGET := init-service build-service build-image clean-service gen-manifest deploy-manifest
	endif
else
	$(error Invalid TARGET_NAME)
endif

# start builder conditions
ifeq ($(BUILDER),golang)
	INIT_SERVICE := init-service-golang
	TEST_SERVICE := test-service-golang
	BUILD_SERVICE := build-service-golang
	BUILD_JOB := skip-target
	RUN_SERVICE := run-service-golang
	INIT_TEST := init-test-golang
	RUN_TEST := run-test-golang
else ifeq ($(BUILDER),python)
	INIT_SERVICE := init-service-python
	TEST_SERVICE := test-service-python
	BUILD_SERVICE := build-service-python
	BUILD_JOB := build-job-python
	RUN_SERVICE := run-service-python
	RUN_JOB := run-job-python
	CLEAN_SERVICE := clean-service-python
	INIT_TEST := init-test-python
	RUN_TEST := run-test-python
else ifeq ($(BUILDER),nodejs)
	INIT_APP := init-app-nodejs
	TEST_APP := test-app-nodejs
	BUILD_APP := build-app-nodejs
	RUN_APP := run-app-nodejs
	GEN_APP := gen-manifest
else ifeq ($(BUILDER),swissknife)
	INIT_JOB := skip-target
	TEST_JOB := skip-target
	BUILD_JOB := build-job-swissknife
	GEN_JOB := gen-job-swissknife
endif
# end builder conditions

# export the following as system environment variables
.EXPORT_ALL_VARIABLES:
-include Makefile.variables
-include Makefile.dev.variables

# build shell script for kubernetes manifest file substitution
define ENVSUBST_SCRIPT
export SERVICE_NAME=${SERVICE_NAME}
export DEPLOYMENT_NAME=${SERVICE_NAME}-${RELEASE_VERSION}
export SUBSET=${RELEASE_VERSION}
export IMAGE_TAG=${RELEASE_VERSION}-${COMMIT_ID}
export IMAGE_URI=${DOCKER_REGISTRY_URI}/${PARENT}/${TARGET_NAME}

kubectl kustomize ${PARENT}/${TARGET_NAME}/k8s/overlays/${CLOUD_ENV_NAME} | envsubst > ${PARENT}/${TARGET_NAME}/k8s/${CLOUD_ENV_NAME}_manifest.yaml
endef

# export the substitute script as system variable
export ENVSUBST_SCRIPT

# only required for debugging the Makefile
debug:
	# @:

-include debug

skip-target:
	@echo "Skipped!"

# start project specifc targets
init-prj-deps: skip-target

init-prj-k8s-config:
	gcloud container clusters get-credentials muzna-bo-aio-01 --zone europe-west2-c --project strange-metrics-258802
	kubectl config rename-context gke_strange-metrics-258802_europe-west2-c_muzna-bo-aio-01 muzna-aio

# start Infra/CI specific targets
get-builder:
	@echo $(shell v=$$(yq r $$(find **/${TARGET_NAME} -name Buildfile) metadata.builder); echo $$v)

get-apps:
	for BUILDFILE in $$(ls apps/*/Buildfile); do \
		echo $$(yq r $$BUILDFILE metadata.name); \
	done

get-services:
	for BUILDFILE in $$(ls services/*/Buildfile); do \
		echo $$(yq r $$BUILDFILE metadata.name); \
	done

get-changes:
	@git diff-tree --no-commit-id --name-only -r ${FROM_REVISION} ${TO_REVISION} | grep ${CHANGES_KIND} | cut -d/ -f2 | uniq

get-tests:
	for BUILDFILE in $$(ls tests/*/Buildfile); do \
		echo $$(yq r $$BUILDFILE metadata.name); \
	done

# start docker targets
gen-docker-all:
	for BUILDFILE in $$(ls infrastructure/docker/*/Buildfile); do \
		REGISTRY_URI=$$(yq r $$BUILDFILE metadata.registry); \
		IMAGE_NAME=$$(yq r $$BUILDFILE -j | jq -r ".metadata.name"); \
		IMAGE_BASE=$$(yq r $$BUILDFILE -j | jq -r ".spec | .base"); \
		IMAGE_CUSTOM_TAG=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .customTag != null then .customTag else false end)"); \
		IMAGE_INTERAL_BASE=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .interalBase != null then true else false end)"); \
		if test "$${IMAGE_CUSTOM_TAG}" != 'false'; then \
			IMAGE_BASE_TAG=$${IMAGE_CUSTOM_TAG}-$${IMAGE_BASE//:/-}; \
		else \
			IMAGE_BASE_TAG=$${IMAGE_BASE//:/-}; \
		fi; \
		IMAGE_CUSTOM_VERSION=$$(yq r $$BUILDFILE -j | jq -r ".spec | .version"); \
		IMAGE_BASE_ONLY=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .baseOnly != null then true else false end)"); \
		IMAGE_ENV_VARIABLES=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .env != null then true else false end)"); \
		IMAGE_SECRETS=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .secrets != null then true else false end)"); \
		IMAGE_SCRIPT_NAME=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .script != null then .script else false end)"); \
		if ! ($$IMAGE_INTERAL_BASE); then \
			mkdir -p ./infrastructure/docker/$$IMAGE_NAME/.base; \
			echo "FROM $$IMAGE_BASE" > ./infrastructure/docker/$$IMAGE_NAME/.base/Dockerfile; \
		else \
			mkdir -p ./infrastructure/docker/$$IMAGE_NAME/.base; \
			echo "FROM $$REGISTRY_URI/base/$$IMAGE_BASE" > ./infrastructure/docker/$$IMAGE_NAME/.base/Dockerfile; \
		fi; \
		if ($${IMAGE_ENV_VARIABLES}); then \
			awk '!/^ENV/' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
			ENV_VALUES=(); \
			for ENV_VAR in $$(yq r $$BUILDFILE -j | jq -r ".spec | .env | keys[]"); do \
				ENV_VALUE=$$(yq r $$BUILDFILE -j | jq -r ".spec | .env | .$${ENV_VAR}"); \
				ENV_VALUES+="ENV $${ENV_VAR} $${ENV_VALUE}\\n"; \
			done; \
			awk -v ENV_VALUES="$${ENV_VALUES}" 'NR==3{print ENV_VALUES}1' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
		fi; \
		if ($${IMAGE_SECRETS}); then \
			mkdir -p ./infrastructure/docker/$$IMAGE_NAME/.secrets; \
			awk '!/^COPY/' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
			awk -v COPY_SECRETS="COPY .secrets/ /tmp/secrets" 'NR==2{print COPY_SECRETS}1' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
			for ENV_SECRET in $$(yq r $$BUILDFILE -j | jq -r ".spec | .secrets | values[]"); do \
				set +x; echo "$${!ENV_SECRET}" | base64 -d > ./infrastructure/docker/$$IMAGE_NAME/.secrets/$${ENV_SECRET}; \
			done; \
		fi; \
		if ! ($$IMAGE_BASE_ONLY); then \
			awk 'NR==1 {$$0=replace} 1' replace="FROM $$REGISTRY_URI/base/$${IMAGE_BASE#*/}" ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
		else \
			awk 'NR==1 {$$0=replace} 1' replace="FROM $$REGISTRY_URI/base/$$IMAGE_BASE" ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
			mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
		fi; \
		awk 'NF > 0' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
		mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
	done

gen-docker:
	REGISTRY_URI=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile metadata.registry); \
	IMAGE_NAME=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".metadata.name"); \
	IMAGE_BASE=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .base"); \
	IMAGE_CUSTOM_TAG=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .customTag != null then .customTag else false end)"); \
	IMAGE_INTERAL_BASE=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .interalBase != null then true else false end)"); \
	if test "$${IMAGE_CUSTOM_TAG}" != 'false'; then \
		IMAGE_BASE_TAG=$${IMAGE_CUSTOM_TAG}-$${IMAGE_BASE//:/-}; \
	else \
		IMAGE_BASE_TAG=$${IMAGE_BASE//:/-}; \
	fi; \
	IMAGE_CUSTOM_VERSION=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .version"); \
	IMAGE_BASE_ONLY=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .baseOnly != null then true else false end)"); \
	IMAGE_ENV_VARIABLES=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .env != null then true else false end)"); \
	IMAGE_SECRETS=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .secrets != null then true else false end)"); \
	IMAGE_SCRIPT_NAME=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .script != null then .script else false end)"); \
	if ! ($$IMAGE_INTERAL_BASE); then \
		mkdir -p ./infrastructure/docker/$$IMAGE_NAME/.base; \
		echo "FROM $$IMAGE_BASE" > ./infrastructure/docker/$$IMAGE_NAME/.base/Dockerfile; \
	else \
		mkdir -p ./infrastructure/docker/$$IMAGE_NAME/.base; \
		echo "FROM $$REGISTRY_URI/base/$$IMAGE_BASE" > ./infrastructure/docker/$$IMAGE_NAME/.base/Dockerfile; \
	fi; \
	if ($${IMAGE_ENV_VARIABLES}); then \
		awk '!/^ENV/' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
		mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
		ENV_VALUES=(); \
		for ENV_VAR in $$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .env | keys[]"); do \
			ENV_VALUE=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .env | .$${ENV_VAR}"); \
			ENV_VALUES+="ENV $${ENV_VAR} $${ENV_VALUE}\\n"; \
		done; \
		awk -v ENV_VALUES="$${ENV_VALUES}" 'NR==3{print ENV_VALUES}1' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
		mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
	fi; \
	if ($${IMAGE_SECRETS}); then \
		mkdir -p ./infrastructure/docker/${TARGET_NAME}/.secrets; \
		awk '!/^COPY/' ./infrastructure/docker/${TARGET_NAME}/Dockerfile > ./infrastructure/docker/${TARGET_NAME}/Dockerfile.tmp; \
		mv ./infrastructure/docker/${TARGET_NAME}/Dockerfile.tmp ./infrastructure/docker/${TARGET_NAME}/Dockerfile; \
		awk -v COPY_SECRETS="COPY .secrets/ /tmp/secrets" 'NR==2{print COPY_SECRETS}1' ./infrastructure/docker/${TARGET_NAME}/Dockerfile > ./infrastructure/docker/${TARGET_NAME}/Dockerfile.tmp; \
		mv ./infrastructure/docker/${TARGET_NAME}/Dockerfile.tmp ./infrastructure/docker/${TARGET_NAME}/Dockerfile; \
		for ENV_SECRET in $$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .secrets | values[]"); do \
			set +x; echo "$${!ENV_SECRET}" | base64 -d > ./infrastructure/docker/${TARGET_NAME}/.secrets/$${ENV_SECRET}; \
		done; \
	fi; \
	if ! ($$IMAGE_BASE_ONLY); then \
		awk 'NR==1 {$$0=replace} 1' replace="FROM $$REGISTRY_URI/base/$${IMAGE_BASE#*/}" ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
		mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
	else \
		awk 'NR==1 {$$0=replace} 1' replace="FROM $$REGISTRY_URI/base/$$IMAGE_BASE" ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
		mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \
	fi; \
	awk 'NF > 0' ./infrastructure/docker/$$IMAGE_NAME/Dockerfile > ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp; \
	mv ./infrastructure/docker/$$IMAGE_NAME/Dockerfile.tmp ./infrastructure/docker/$$IMAGE_NAME/Dockerfile; \

build-docker-all: gen-docker-all
	for BUILDFILE in $$(ls infrastructure/docker/*/Buildfile); do \
		REGISTRY_URI=$$(yq r $$BUILDFILE metadata.registry); \
		IMAGE_NAME=$$(yq r $$BUILDFILE -j | jq -r ".metadata.name"); \
		IMAGE_BASE=$$(yq r $$BUILDFILE -j | jq -r ".spec | .base"); \
		IMAGE_CUSTOM_TAG=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .customTag != null then .customTag else false end)"); \
		if test "$${IMAGE_CUSTOM_TAG}" != 'false'; then \
			IMAGE_BASE_TAG=$${IMAGE_CUSTOM_TAG}-$${IMAGE_BASE//:/-}; \
		else \
			IMAGE_BASE_TAG=$${IMAGE_BASE//:/-}; \
		fi; \
		IMAGE_BASE_ONLY=$$(yq r $$BUILDFILE -j | jq -r ".spec | (if .baseOnly != null then true else false end)"); \
		IMAGE_CUSTOM_VERSION=$$(yq r $$BUILDFILE -j | jq -r ".spec | .version"); \
		docker build -t $$REGISTRY_URI/base/$${IMAGE_BASE#*/} ./infrastructure/docker/$$IMAGE_NAME/.base; \
		docker push $$REGISTRY_URI/base/$${IMAGE_BASE#*/}; \
		if ($$IMAGE_BASE_ONLY); then \
			docker build -t $$REGISTRY_URI/base/$$IMAGE_NAME:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION ./infrastructure/docker/$$IMAGE_NAME; \
			docker push $$REGISTRY_URI/base/$$IMAGE_NAME:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION; \
		else \
			docker build -t $$REGISTRY_URI/images/$$IMAGE_NAME:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION ./infrastructure/docker/$$IMAGE_NAME; \
			docker push $$REGISTRY_URI/images/$$IMAGE_NAME:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION; \
		fi; \
	done

build-docker: gen-docker
	REGISTRY_URI=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile metadata.registry); \
	IMAGE_NAME=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".metadata.name"); \
	IMAGE_BASE=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .base"); \
	IMAGE_CUSTOM_TAG=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .customTag != null then .customTag else false end)"); \
	if test "$${IMAGE_CUSTOM_TAG}" != 'false'; then \
		IMAGE_BASE_TAG=$${IMAGE_CUSTOM_TAG}-$${IMAGE_BASE//:/-}; \
	else \
		IMAGE_BASE_TAG=$${IMAGE_BASE//:/-}; \
	fi; \
	IMAGE_BASE_ONLY=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | (if .baseOnly != null then true else false end)"); \
	IMAGE_CUSTOM_VERSION=$$(yq r ./infrastructure/docker/${TARGET_NAME}/Buildfile -j | jq -r ".spec | .version"); \
	if ! ($$IMAGE_BASE_ONLY); then \
		docker build -t $$REGISTRY_URI/base/${TARGET_NAME}:$${IMAGE_BASE_TAG#*/} ./infrastructure/docker/${TARGET_NAME}/.base; \
		docker build -t $$REGISTRY_URI/images/${TARGET_NAME}:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION ./infrastructure/docker/${TARGET_NAME}; \
	else \
		docker build -t $$REGISTRY_URI/base/$${IMAGE_BASE} ./infrastructure/docker/${TARGET_NAME}/.base; \
		docker push $$REGISTRY_URI/base/$${IMAGE_BASE}; \
		docker build -t $$REGISTRY_URI/base/${TARGET_NAME}:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION ./infrastructure/docker/${TARGET_NAME}; \
		docker push $$REGISTRY_URI/base/${TARGET_NAME}:$${IMAGE_BASE_TAG#*/}-FDC-$$IMAGE_CUSTOM_VERSION; \
	fi;
# end docker targets
# end Infra/CI specific targets

# start config specific targets
test-config:
	@cd infrastructure/kubernetes/ksonnet/configuration && ks validate ${CLOUD_ENV_NAME}

gen-config:
	@cd infrastructure/kubernetes/ksonnet/configuration && ks show ${CLOUD_ENV_NAME} > ks-${CLOUD_ENV_NAME}-${K8S_NAMESPACE}.yaml

apply-config:
	@kubectl --context ${K8S_CONTEXT} -n ${K8S_NAMESPACE} apply -f infrastructure/kubernetes/ksonnet/configuration/ks-${CLOUD_ENV_NAME}-${K8S_NAMESPACE}.yaml
# end config specific targets

# start job specific targets
## start swissknife job specific targets
build-job-swissknife: build-image

gen-job-swissknife: gen-manifest
## end swissknife job specific targets
# end job specific targets

# start service specific targets
## start golang service specific targets
dep-golang:
	@[ -d vendor ] || go mod download

init-service-golang: dep-golang

test-service-golang: run-lint-golang
	@go test -v -cover ./pkg/...
	@go test -v -cover ./services/${TARGET_NAME}/...

build-service-golang:
ifeq ($(DETECTED_OS),Darwin)
	@docker run --rm -it -e GO111MODULE=on -e CGO_ENABLED=0 -v $$(pwd):/opt/microservice -w /opt/microservice $$IMAGE_GOLANG \
	sh -c "go build -v -x -o /opt/microservice/services/${TARGET_NAME}/bin/main /opt/microservice/services/${TARGET_NAME}/cmd/server/*.go"
else
	@go build -v -x -o ./services/${TARGET_NAME}/bin/main ./services/${TARGET_NAME}/cmd/server/*.go
endif

run-service-golang:
	@rm -f go.sum && go run ./services/${TARGET_NAME}/cmd/server/*.go
## end golang service specific targets

## start python specific targets
init-service-python: skip-target
test-service-python: skip-target
build-service-python:
	@cd ./services/${TARGET_NAME} && poetry export --with-credentials --without-hashes -f requirements.txt -o requirements.txt
build-job-python:
	@cd ./jobs/${TARGET_NAME} && poetry export --with-credentials --without-hashes -f requirements.txt -o requirements.txt
clean-service-python: skip-target

run-service-python:
	@cd ./services/${TARGET_NAME} && rm -f poetry.lock && poetry install --no-interaction --no-dev && poetry run python main.py
## end python service specific targets

## start python specific targets
run-job-python:
	@cd ./jobs/${TARGET_NAME} && rm -f poetry.lock && poetry install --no-interaction --no-dev && poetry run python main.py
## end python service specific targets

## start nodejs  specific targets
init-app-nodejs:
	@cd ./apps/${TARGET_NAME} && npm install

test-app-nodejs:
	@cd ./apps/${TARGET_NAME} && npm run prettier-check
	@cd ./apps/${TARGET_NAME} && export CI=true && npm run test

build-app-nodejs:
	@cd ./apps/${TARGET_NAME} && npm run build

run-app-nodejs:
	@cd ./apps/${TARGET_NAME} && npm run serve

## end nodejs service specific targets

## end general service specific targets
build-image:
	@docker build -t ${DOCKER_REGISTRY_URI}/${PARENT}/${TARGET_NAME}:${RELEASE_VERSION}-${COMMIT_ID} $(shell find ${PARENT} -name ${TARGET_NAME})
	@docker push ${DOCKER_REGISTRY_URI}/${PARENT}/${TARGET_NAME}:${RELEASE_VERSION}-${COMMIT_ID}

gen-manifest:
	@echo "$$ENVSUBST_SCRIPT" > .subst && sh .subst

deploy-manifest:
	kubectl --context ${K8S_CONTEXT} -n ${K8S_NAMESPACE} apply -f ${PARENT}/${TARGET_NAME}/k8s/${CLOUD_ENV_NAME}_manifest.yaml;
	if [ ! ${KIND} = "CronJob" ]; then kubectl --context ${K8S_CONTEXT} -n ${K8S_NAMESPACE} rollout status deployment/${TARGET_NAME} && kubectl --context ${K8S_CONTEXT} -n ${K8S_NAMESPACE} rollout restart deployment/${TARGET_NAME}; fi; \
## end general service specific targets
# start service specific targets


# start system-test specific targets
## start golang system-test specific targets
init-test-golang: dep-golang

run-test-golang:
	@find ./tests -type d -name ${TARGET_NAME} -exec go test -v {} +

run-lint-golang:
	@cd ./${PARENT}/${TARGET_NAME} && golangci-lint run --enable=golint --exclude-use-default=false --skip-dirs openapi/go
## start golang system-test specific targets
# end system-test specific targets

# start system-test targets
init-test: ${INIT_TEST}

run-test: ${RUN_TEST}
# end system-test main targets

# start job main targets
init-job: ${INIT_JOB}

test-job: ${TEST_JOB}

run-job: ${RUN_JOB}

gen-job: ${GEN_JOB}

build-job: ${BUILD_JOB}

# end job main targets

# start app main targets
init-app: ${INIT_APP}

test-app: ${TEST_APP}

gen-app: ${GEN_APP}

build-app: ${BUILD_APP}

run-app: ${RUN_APP}
# end app main targets

# start service main targets
init-service: ${INIT_SERVICE}

test-service: ${TEST_SERVICE}

build-service: ${BUILD_SERVICE}

run-service: ${RUN_SERVICE}

clean-service: ${CLEAN_SERVICE}
# end service main targets

# start general targets
get: ${GET_TARGET}

init: ${INIT_TARGET}

gen: ${GEN_TARGET}

test: ${TEST_TARGET}

build: ${BUILD_TARGET}

run: ${RUN_TARGET}

deploy: ${DEPLOY_TARGET}

manual-deploy: ${MANUAL_DEPLOY_TARGET}

apply: ${APPLY_TARGET}

update: ${UPDATE_TARGET}
# end general targets
