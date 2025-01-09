# Makefile for building and distributing the provider

HOSTNAME=registry.terraform.io
NAMESPACE=your-namespace
NAME=cloudoptimizer
BINARY=terraform-provider-${NAME}
VERSION=0.1.0
OS_ARCH=linux_amd64

default: install

.PHONY: build
build:
	go build -o ${BINARY}

.PHONY: install
install: build
	mkdir -p ~/.terraform.d/plugins/${HOSTNAME}/${NAMESPACE}/${NAME}/${VERSION}/${OS_ARCH}
	mv ${BINARY} ~/.terraform.d/plugins/${HOSTNAME}/${NAMESPACE}/${NAME}/${VERSION}/${OS_ARCH}/${BINARY}_v${VERSION}

.PHONY: test
test:
	go test ./... -v

.PHONY: testacc
testacc:
	TF_ACC=1 go test ./... -v $(TESTARGS) -timeout 120m

.PHONY: release
release:
	goreleaser release --rm-dist

.PHONY: release-snapshot
release-snapshot:
	goreleaser release --snapshot --skip-publish --rm-dist

.PHONY: clean
clean:
	rm -rf dist/
	rm -f ${BINARY}

.PHONY: docs
docs:
	tfplugindocs generate

.PHONY: fmt
fmt:
	go fmt ./...

.PHONY: vet
vet:
	go vet ./...

.PHONY: lint
lint:
	golangci-lint run

.PHONY: mod-tidy
mod-tidy:
	go mod tidy

.PHONY: mod-vendor
mod-vendor:
	go mod vendor

.PHONY: check
check: fmt vet lint test

.PHONY: prepare-release
prepare-release:
	@echo "Preparing release v${VERSION}"
	@if [ -z "$$GITHUB_TOKEN" ]; then \
		echo "Please set GITHUB_TOKEN environment variable"; \
		exit 1; \
	fi
	@if [ -z "$$GPG_FINGERPRINT" ]; then \
		echo "Please set GPG_FINGERPRINT environment variable"; \
		exit 1; \
	fi
	@echo "Creating git tag v${VERSION}"
	git tag v${VERSION}
	git push origin v${VERSION}

.PHONY: publish
publish: prepare-release release
	@echo "Publishing provider to Terraform Registry"
	@echo "Please ensure you have:"
	@echo "1. Updated the version in version.go"
	@echo "2. Updated CHANGELOG.md"
	@echo "3. Created and pushed git tag"
	@echo "4. Set GITHUB_TOKEN environment variable"
	@echo "5. Set GPG_FINGERPRINT environment variable"

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build              Build provider binary"
	@echo "  install            Install provider locally"
	@echo "  test               Run unit tests"
	@echo "  testacc            Run acceptance tests"
	@echo "  release            Create and publish a release"
	@echo "  release-snapshot   Create a snapshot release"
	@echo "  clean              Clean build artifacts"
	@echo "  docs               Generate provider documentation"
	@echo "  fmt                Format Go code"
	@echo "  vet                Run Go vet"
	@echo "  lint               Run linter"
	@echo "  mod-tidy           Tidy Go modules"
	@echo "  mod-vendor         Vendor Go dependencies"
	@echo "  check              Run all checks (fmt, vet, lint, test)"
	@echo "  prepare-release    Prepare for a release"
	@echo "  publish            Publish provider to Terraform Registry"
