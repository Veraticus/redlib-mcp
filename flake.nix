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
            mcp
            httpx
          ];

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
            pythonPackages.mcp
            pythonPackages.httpx
            git
          ];

          shellHook = ''
            echo "Redlib MCP development environment"
            echo "  python src/redlib_mcp.py  - Run the MCP server"
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
