{
  description = "Expressive Python analytics at any scale.";

  inputs = {
    flake-compat = {
      url = "github:edolstra/flake-compat";
      flake = false;
    };

    flake-utils.url = "github:numtide/flake-utils";

    gitignore = {
      url = "github:hercules-ci/gitignore.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";

    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs = { self, flake-utils, gitignore, nixpkgs, poetry2nix, ... }: {
    overlays.default = nixpkgs.lib.composeManyExtensions [
      gitignore.overlay
      poetry2nix.overlay
      (import ./nix/overlay.nix)
    ];
  } // flake-utils.lib.eachDefaultSystem (
    localSystem:
    let
      pkgs = import nixpkgs {
        inherit localSystem;
        overlays = [ self.overlays.default ];
      };
      inherit (pkgs) lib;

      backendDevDeps = with pkgs; [
        # impala UDFs
        clang_12
        cmake
        ninja
        # snowflake
        openssl
        # backend test suite
        docker-compose
        # visualization
        graphviz-nox
        # duckdb
        duckdb
        # mysql
        mariadb-client
        # pyspark
        openjdk17_headless
        # postgres
        postgresql
        # sqlite
        sqlite-interactive
      ];
      shellHook = ''
        export IBIS_TEST_DATA_DIRECTORY="$PWD/ci/ibis-testing-data"

        ${pkgs.rsync}/bin/rsync \
          --chmod=Du+rwx,Fu+rw --archive --delete \
          "${pkgs.ibisTestingData}/" \
          "$IBIS_TEST_DATA_DIRECTORY"

        export TEMPDIR
        TEMPDIR="$(python -c 'import tempfile; print(tempfile.gettempdir())')"

        # necessary for mkdocs
        export PYTHONPATH=''${PWD}''${PYTHONPATH:+:}''${PYTHONPATH}
      '';

      preCommitDeps = with pkgs; [
        actionlint
        git
        just
        nixpkgs-fmt
        pre-commit
        prettier
        shellcheck
        shfmt
        statix
      ];

      mkDevShell = name: env: pkgs.mkShell {
        inherit name;
        nativeBuildInputs = (with pkgs; [
          # python dev environment
          env
          # rendering release notes
          changelog
          glow
          # used in the justfile
          jq
          yj
          # commit linting
          commitlint
          # link checking
          lychee
          # release automation
          nodejs
          # poetry executable
          env.pkgs.poetry
          # used in notebooks to download data
          curl
        ])
        ++ preCommitDeps
        ++ backendDevDeps;

        inherit shellHook;

        PGPASSWORD = "postgres";
        MYSQL_PWD = "ibis";
        MSSQL_SA_PASSWORD = "1bis_Testing!";
      };
    in
    rec {
      packages = {
        inherit (pkgs) ibis38 ibis39 ibis310;

        default = pkgs.ibis310;

        inherit (pkgs) update-lock-files;
      };

      devShells = rec {
        ibis38 = mkDevShell "ibis38" pkgs.ibisDevEnv38;
        ibis39 = mkDevShell "ibis39" pkgs.ibisDevEnv39;
        ibis310 = mkDevShell "ibis310" pkgs.ibisDevEnv310;

        default = ibis310;

        preCommit = pkgs.mkShell {
          name = "preCommit";
          nativeBuildInputs = [ pkgs.ibisSmallDevEnv ] ++ preCommitDeps;
        };

        links = pkgs.mkShell {
          name = "links";
          nativeBuildInputs = with pkgs; [ just lychee ];
        };

        release = pkgs.mkShell {
          name = "release";
          nativeBuildInputs = with pkgs; [
            git
            ibisSmallDevEnv.pkgs.poetry
            nodejs
            unzip
            gnugrep
          ];
        };
      };
    }
  );
}
