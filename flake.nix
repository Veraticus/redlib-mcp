{
  description = "Redlib MCP Server - Model Context Protocol server for Redlib API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
        pythonPackages = python.pkgs;

        # Fetch additional dependencies not in nixpkgs
        py-key-value-shared = pythonPackages.buildPythonPackage rec {
          pname = "py_key_value_shared";
          version = "0.3.0";
          format = "wheel";
          src = pythonPackages.fetchPypi {
            inherit pname version format;
            dist = "py3";
            python = "py3";
            sha256 = "sha256-Ww77p+vKCLsVix6Tr8LwfTC49AwvwSziSkwNhPQvkpg=";
          };
          propagatedBuildInputs = with pythonPackages; [
            pydantic
          ];
          doCheck = false;
        };

        py-key-value-aio = pythonPackages.buildPythonPackage rec {
          pname = "py_key_value_aio";
          version = "0.3.0";
          format = "wheel";
          src = pythonPackages.fetchPypi {
            inherit pname version format;
            dist = "py3";
            python = "py3";
            sha256 = "sha256-HHgZFXZgeL/WCNqnaf77l+ZdHXN0aj37ZARg4yIHG2Q=";
          };
          propagatedBuildInputs = with pythonPackages; [
            py-key-value-shared
            anyio
            beartype
            cachetools
            diskcache
            pathvalidate
          ];
          doCheck = false;
        };

        pydocket = pythonPackages.buildPythonPackage rec {
          pname = "pydocket";
          version = "0.16.6";
          format = "wheel";
          src = pythonPackages.fetchPypi {
            inherit pname version format;
            dist = "py3";
            python = "py3";
            sha256 = "sha256-aD0h4uhGqlEGJ059WSEDMbJC1/sNzlsI07ggZWY+0YM=";
          };
          propagatedBuildInputs = with pythonPackages; [
            anyio
            pydantic
            redis
            cloudpickle
            opentelemetry-exporter-prometheus
            opentelemetry-instrumentation
            fakeredis
          ];
          doCheck = false;
        };

        fastmcp = pythonPackages.buildPythonPackage rec {
          pname = "fastmcp";
          version = "2.14.3";
          format = "wheel";
          src = pythonPackages.fetchPypi {
            inherit pname version format;
            dist = "py3";
            python = "py3";
            sha256 = "sha256-EDxrTG6XqazCUcgdMD8RD+TyvboxNT31FdZicr8blBQ=";
          };
          propagatedBuildInputs = with pythonPackages; [
            httpx
            uvicorn
            starlette
            pydantic
            pydantic-settings
            anyio
            sse-starlette
            httpx-sse
            opentelemetry-api
            opentelemetry-sdk
            exceptiongroup
            python-dotenv
            typer
            rich
            mcp
            platformdirs
            pydocket
            py-key-value-aio
            authlib
          ];
          pythonImportsCheck = [];
          doCheck = false;
        };

        redlib-mcp = pythonPackages.buildPythonApplication rec {
          pname = "redlib-mcp";
          version = "0.1.0";
          src = ./.;
          pyproject = true;

          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
          ];

          propagatedBuildInputs = with pythonPackages; [
            fastmcp
            httpx
            uvicorn
          ];

          dontCheckRuntimeDeps = true;
          pythonImportsCheck = [ "redlib_mcp" ];

          meta = with pkgs.lib; {
            description = "Model Context Protocol server for Redlib API";
            license = licenses.mit;
            platforms = platforms.unix;
          };
        };

      in
      {
        packages = {
          inherit redlib-mcp;
          default = redlib-mcp;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            python
            pythonPackages.pip
            pythonPackages.black
            pythonPackages.pytest
            pythonPackages.pytest-asyncio
            pythonPackages.httpx
            pythonPackages.uvicorn
            pythonPackages.starlette
            git
          ];

          shellHook = ''
            echo "Redlib MCP development environment"

            if [ ! -d .venv ]; then
              python -m venv .venv
            fi
            source .venv/bin/activate

            if ! python -c "import fastmcp" 2>/dev/null; then
              pip install -q "fastmcp>=2.13.0"
            fi

            pip install -q -e .

            echo "  python src/redlib_mcp.py  - Run the MCP server"
            echo "  redlib-mcp-server         - Run HTTP server with OAuth"
            echo "  pytest                    - Run tests"
            echo "  nix build                 - Build with Nix"
          '';
        };

        apps.default = {
          type = "app";
          program = "${redlib-mcp}/bin/redlib-mcp";
        };
      }
    );
}
